"""
Mowgli Swarm — parallel agent fan-out with merge step.

Inspired by Ruflo's swarm coordination patterns, adapted for single-developer
CLI use: no distributed consensus, no vector DB — just threads + a merge model.

Pattern:
  1. Decompose the prompt into N worker sub-prompts
  2. Run N worker agents in parallel (threads)
  3. Collect outputs
  4. Run a merge agent that synthesises the results

Usage (slash command):
  /swarm <prompt>           — auto-decompose into router.swarm_workers tasks
  /swarm 5 <prompt>         — override worker count

Automatic routing:
  When classify() returns route=="swarm", _execute_turn calls swarm_execute().
"""
from __future__ import annotations
import subprocess
import threading
import uuid
from dataclasses import dataclass, field

from rich.console import Console
from rich.markup import escape

from .config import MowgliConfig
from .providers import get_provider
from .providers.base import StreamState, StreamEvent
from .router import RouterConfig

# ─── Decomposition prompt ─────────────────────────────────────────────────────

_DECOMPOSE_PROMPT = """\
You are a task decomposer. Split the following task into exactly {n} independent sub-tasks.
Each sub-task must be self-contained and executable by a separate agent without shared state.
Return ONLY a JSON array of {n} strings, one per sub-task. No prose, no numbering outside JSON.

Task: {task}"""

_MERGE_PROMPT = """\
You are a synthesis agent. Below are {n} independent agent outputs for the same overarching task.
Merge them into a single coherent, deduplicated response. Resolve any contradictions by favouring
the most complete / accurate answer. Output only the final merged result.

Original task: {task}

--- Agent outputs ---
{outputs}"""


# ─── Worker result ────────────────────────────────────────────────────────────

@dataclass
class WorkerResult:
    index: int
    sub_prompt: str
    text: str = ""
    cost_usd: float = 0.0
    error: str = ""


# ─── Core execution ───────────────────────────────────────────────────────────

def _run_worker(
    index: int,
    sub_prompt: str,
    worker_alias: str,
    config: MowgliConfig,
    results: list[WorkerResult],
    tone_prompt: str,
) -> None:
    spec = config.resolve_model(worker_alias)
    provider = get_provider(spec.provider)

    args = provider.build_headless_args(
        prompt=sub_prompt,
        model_id=spec.model_id,
        session_id=str(uuid.uuid4()),
        resume=False,
        include_partial=False,
        system_prompt=tone_prompt,
    )

    result = WorkerResult(index=index, sub_prompt=sub_prompt)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
        state = StreamState()
        for line in proc.stdout.splitlines():
            event: StreamEvent | None = provider.parse_stream_line(line, state)
            if event is None:
                continue
            if event.type == "text_delta":
                result.text += event.content
            elif event.type == "cost":
                result.cost_usd = event.cost_usd
    except subprocess.TimeoutExpired:
        result.error = "timeout"
    except Exception as e:
        result.error = str(e)

    results[index] = result


def _decompose(
    task: str,
    n: int,
    classifier_alias: str,
    config: MowgliConfig,
) -> list[str]:
    """Ask the classifier model to split task into n sub-prompts."""
    import json
    spec = config.resolve_model(classifier_alias)
    provider = get_provider(spec.provider)

    args = provider.build_headless_args(
        prompt=_DECOMPOSE_PROMPT.format(n=n, task=task[:800]),
        model_id=spec.model_id,
        session_id=str(uuid.uuid4()),
        resume=False,
        include_partial=False,
    )

    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=30)
        state = StreamState()
        raw = ""
        for line in proc.stdout.splitlines():
            event = provider.parse_stream_line(line, state)
            if event and event.type == "text_delta":
                raw += event.content

        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            parts = json.loads(raw[start:end])
            if isinstance(parts, list) and len(parts) == n:
                return [str(p) for p in parts]
    except Exception:
        pass

    # Fallback: send the same prompt to all workers
    return [task] * n


def swarm_execute(
    task: str,
    config: MowgliConfig,
    router: RouterConfig,
    console: Console,
    tone_prompt: str,
    n_workers: int | None = None,
) -> float:
    """
    Fan-out *task* to N parallel workers, then merge.

    Returns total cost (USD).
    """
    n = n_workers or router.swarm_workers

    console.print(
        f"  [bold magenta]⬡ swarm[/bold magenta]  "
        f"[dim]{n} × {router.swarm_worker_alias} → merge:{router.swarm_merge_alias}[/dim]"
    )

    # 1. Decompose
    console.print("  [dim]decomposing task…[/dim]")
    sub_prompts = _decompose(task, n, router.classifier_alias, config)

    # 2. Fan-out in parallel
    results: list[WorkerResult] = [WorkerResult(index=i, sub_prompt=sub_prompts[i]) for i in range(n)]
    threads = [
        threading.Thread(
            target=_run_worker,
            args=(i, sub_prompts[i], router.swarm_worker_alias, config, results, tone_prompt),
            daemon=True,
        )
        for i in range(n)
    ]

    console.print(f"  [dim]launching {n} workers…[/dim]")
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=130)

    total_cost = sum(r.cost_usd for r in results)

    # Show worker summaries
    for r in results:
        if r.error:
            console.print(f"  [dim red]worker {r.index + 1} error: {r.error}[/dim red]")
        else:
            preview = r.text[:80].replace("\n", " ")
            console.print(f"  [dim]worker {r.index + 1}: {escape(preview)}…[/dim]")

    # 3. Merge
    console.rule(f"[bold]Merging[/bold]  [dim]{router.swarm_merge_alias}[/dim]")

    outputs_block = "\n\n".join(
        f"[Worker {r.index + 1}]\n{r.text}" for r in results if r.text
    )
    merge_prompt = _MERGE_PROMPT.format(n=n, task=task, outputs=outputs_block)

    merge_spec = config.resolve_model(router.swarm_merge_alias)
    merge_provider = get_provider(merge_spec.provider)

    merge_args = merge_provider.build_headless_args(
        prompt=merge_prompt,
        model_id=merge_spec.model_id,
        session_id=str(uuid.uuid4()),
        resume=False,
        include_partial=True,
        system_prompt=tone_prompt,
    )

    merge_proc = subprocess.Popen(
        merge_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    state = StreamState()
    merge_cost = 0.0
    assert merge_proc.stdout is not None
    for raw_line in merge_proc.stdout:
        line = raw_line.rstrip("\n")
        if not line:
            continue
        event = merge_provider.parse_stream_line(line, state)
        if event is None:
            continue
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "cost":
            merge_cost = event.cost_usd

    merge_proc.wait()
    if not state.last_char_newline:
        print()

    total_cost += merge_cost
    return total_cost

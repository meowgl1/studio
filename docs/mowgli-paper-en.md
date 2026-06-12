# Mowgli CLI: A Multi-Provider, Routing-Aware Command-Line Interface for Large Language Models

**Author:** Thomas  
**Affiliation:** mowgli.studio  
**Date:** June 2026  
**Branch:** feat/readme-craft-skill — github.com/meowgl1/studio

---

## Abstract

This paper documents the design, implementation, and evaluation of Mowgli CLI — a terminal-first, multi-provider interface for interacting with Large Language Models (LLMs). Mowgli addresses three recurring problems in developer LLM workflows: unnecessary token expenditure caused by routing all queries to the most capable (and expensive) model; lack of support for heterogeneous provider ecosystems; and the absence of intelligent task decomposition for complex or parallelisable workloads. The system implements a multi-dimensional query classifier, a three-tier routing strategy (simple → cheap model, complex → sequential plan/execute pipeline, swarm → parallel fan-out with merge), a JSONL-based learning store (ReasoningBank), and a PII scrubbing pipeline. Architectural decisions are compared against Ruflo — a full enterprise swarm framework — to contextualise design trade-offs between operational simplicity and distributed coordination capability. The document concludes with a frank assessment of what the current system does well, where it fails, and what meaningful work remains.

---

## 1. Introduction

### 1.1 Motivation

The dominant pattern for LLM-assisted development in 2025–2026 is a single-model chat interface: the developer sends a message, the most capable available model answers, the response is displayed. This pattern is wasteful in two measurable ways.

First, **cost**. A query such as "what does this function return?" costs 10–30× more when routed to Claude Opus versus Claude Haiku, yet the quality difference for factual retrieval tasks is negligible. Developers using interactive assistants on usage-based plans commonly exhaust 20% of their monthly budget in a handful of exploratory questions — precisely because every message, regardless of complexity, hits the same expensive endpoint.

Second, **quality ceiling**. Highly complex tasks — multi-file refactors, architecture proposals, writing test suites across a codebase — benefit from decomposition. A single model processing a 2,000-token prompt containing five loosely related sub-tasks will produce a worse outcome than five focused agents processing 400 tokens each, with a synthesis pass at the end. Yet standard chat interfaces offer no decomposition mechanism.

Mowgli was built to solve both problems within the constraints of a CLI tool: it must start in under a second, require no persistent infrastructure, and feel like a normal terminal program.

### 1.2 Scope

Mowgli is not:
- A distributed multi-agent system (no networking, no consensus protocols)
- A model fine-tuning or evaluation framework
- An autonomous agent that operates without human steering

Mowgli is:
- A smart dispatcher that routes human queries to the right model automatically
- A lightweight orchestrator that can fan-out parallelisable tasks to multiple model instances
- A learning system that records its own routing history and improves suggestions over time

### 1.3 Paper Structure

Section 2 surveys related work. Section 3 describes the overall architecture. Sections 4–8 cover each subsystem in detail. Section 9 evaluates the system: advantages, limitations, missing features, and open questions. Section 10 concludes with design philosophy reflections.

---

## 2. Related Work and Positioning

### 2.1 Ruflo

The most relevant comparison for Mowgli is **Ruflo** (github.com/ruvnet/ruflo), an enterprise multi-agent swarm framework built on top of Claude Code. Ruflo implements:

- **Three swarm topologies**: hierarchical (leader-delegate), mesh (peer-to-peer), and adaptive (self-organising)
- **Distributed consensus**: Raft algorithm for leader election and Byzantine Fault Tolerance for untrusted environments
- **HNSW vector indexing**: agents are embedded in semantic vector space; incoming queries are routed via approximate nearest-neighbour search
- **SONA neural patterns**: self-organising optimisation that adjusts routing thresholds autonomously over time
- **ReasoningBank**: trajectory-based long-term memory that records successful reasoning paths and reuses them
- **Zero-trust security**: mTLS inter-agent communication, ed25519 identity verification, PII detection pipeline
- **33 pre-built MCP plugin integrations**

Ruflo is operationally heavy. It requires a vector database, multiple background worker processes, and a web dashboard. It is designed for teams, not individuals.

Mowgli adopts four of Ruflo's conceptual patterns — swarm fan-out, multi-dimensional task scoring, ReasoningBank, and PII scrubbing — while replacing Ruflo's distributed infrastructure with single-process equivalents: threading instead of networking, JSONL instead of a vector DB, regex instead of an ML-based PII classifier.

### 2.2 LangChain / LlamaIndex

LangChain (Harrison Chase, 2022) and LlamaIndex (Jerry Liu, 2022) provide Python frameworks for chaining LLM calls. Both are library-level: they require the developer to write orchestration code. Mowgli inverts this relationship — the routing logic is inside the tool, not the application the developer is building.

### 2.3 Claude Code

Mowgli wraps **Claude Code** (Anthropic, 2025), which is itself a CLI providing headless access to Claude models via `--output-format stream-json`. Mowgli is not an alternative to Claude Code; it is a meta-layer that decides which model Claude Code should use, manages session continuity across turns, and adds provider-level abstraction so that Gemini CLI calls can be mixed in.

### 2.4 Positioning Summary

| System | Level | Infrastructure | Multi-provider | Auto-routing | Swarm |
|---|---|---|---|---|---|
| Claude Code | CLI | None | No | No | No |
| Gemini CLI | CLI | None | No | No | No |
| LangChain | Library | None | Yes | Manual | No |
| Ruflo | Framework | DB + workers + dashboard | Yes | SONA self-learning | Yes (distributed) |
| **Mowgli** | **CLI** | **None** | **Yes** | **Multi-dim classifier** | **Yes (threaded)** |

---

## 3. System Architecture

### 3.1 Module Map

```
src/mowgli/
├── cli.py             Click entry point; routes to REPL or headless pipe
├── repl.py            MowgliREPL — main event loop, turn execution, slash commands
├── router.py          Multi-dimensional classifier, RouterConfig, ClassifyResult
├── swarm.py           Parallel fan-out executor with decomposition and merge
├── reasoning_bank.py  JSONL learning store; suggests models from history
├── pii_scrubber.py    Regex redaction pipeline
├── config.py          ModelSpec, MowgliConfig, model registry with override support
├── branding.py        Terminal banner, /help text
├── game.py            Pixel dino easter egg (30fps, gravity, hi-score)
├── mcp_manager.py     MCP server enable/disable at runtime
└── providers/
    ├── base.py        Provider protocol, StreamState, StreamEvent dataclasses
    ├── claude.py      ClaudeProvider — wraps claude CLI via subprocess
    └── gemini.py      GeminiProvider — wraps gemini CLI via subprocess
```

### 3.2 Data Flow

```
User input
    │
    ▼
[PII scrubber]          ← regex redaction before any external call
    │
    ▼
[Router.classify()]     ← haiku call (~50 tokens); returns ClassifyResult JSON
    │
    ├─ simple   → [simple_alias model]  fresh session, headless, cheap
    │
    ├─ complex  → [plan: opus]  →  [execute: sonnet]  sequential pipeline
    │
    └─ swarm    → [decompose: haiku]
                     │
                 [N × worker: haiku]  parallel threads
                     │
                 [merge: sonnet]
    │
    ▼
[ReasoningBank.record()]  ← log turn metadata to JSONL
    │
    ▼
Output to terminal
```

### 3.3 Session Model

Mowgli distinguishes between **session model** (the model the user interacted with or will interact with when routing is disabled) and **routed model** (the model selected by the router for a specific turn). When routing is enabled, simple queries run in a fresh, stateless session on the cheap model. Complex and swarm queries also use fresh sessions because the pipeline creates its own context. Session continuity (via `--resume <session_id>`) is only preserved in the explicit "router off" mode, where the user has chosen a single model for a full conversation.

This is a deliberate design choice with a significant trade-off, discussed in Section 9.

---

## 4. Router: Multi-Dimensional Classification

### 4.1 Design Rationale

The first version of Mowgli's router (v2.3) used a binary classifier: the query was sent to Haiku with the prompt `"Reply with exactly one word: SIMPLE or COMPLEX"`. This had two critical failures.

**Failure 1: No abstraction scoring.** A one-sentence query like "Explain the CAP theorem and its implications for distributed consensus in Byzantine environments" was reliably classified SIMPLE because it was short. Conversely, a verbose procedural question about a single function was classified COMPLEX due to its length. The classifier was measuring token count, not intellectual demand.

**Failure 2: No parallelism detection.** The system had no way to identify that a task was decomposable. "Write tests for functions A, B, C, D, and E" would route to complex (plan → execute), producing sequential output, when the five sub-tasks were entirely independent and could run in parallel.

The v2.4 classifier addresses both by returning structured JSON across four orthogonal dimensions.

### 4.2 ClassifyResult Schema

```python
@dataclass
class ClassifyResult:
    effort:   int    # 1–10: cognitive/engineering cost to answer well
    tools:    int    # estimated tool calls needed (0 = pure text)
    domain:   str    # conversational | factual | code | architectural | creative
    parallel: bool   # true if task contains independent sub-tasks
    route:    str    # simple | complex | swarm
```

The classifier model (Haiku by default) receives:

```
Analyse the following user query and return a JSON object — nothing else.

Fields:
  effort   (int 1-10): cognitive/engineering effort required
  tools    (int 0-N):  estimated tool calls needed
  domain   (str):      conversational | factual | code | architectural | creative
  parallel (bool):     true if the task contains independent subtasks
  route    (str):      simple | complex | swarm

Routing rules:
  simple  → effort ≤ 4 AND tools ≤ 1
  swarm   → effort ≥ 7 AND parallel is true
  complex → everything else
```

### 4.3 Routing Thresholds

| Condition | Route | Models |
|---|---|---|
| effort ≤ 4 AND tools ≤ 1 | simple | `simple_alias` (default: haiku) |
| effort ≥ 7 AND parallel=true | swarm | N×`swarm_worker_alias` → `swarm_merge_alias` |
| else | complex | plan:`complex_plan_alias` → execute:`complex_execute_alias` |

The thresholds are hard-coded in v2.4. They should become learnable via ReasoningBank in a future version (see Section 9.4).

### 4.4 RouterConfig

```python
@dataclass
class RouterConfig:
    enabled: bool = True
    classifier_alias: str = "haiku"
    simple_alias: str = "haiku"
    complex_plan_alias: str = "opus"
    complex_execute_alias: str = "sonnet"
    swarm_worker_alias: str = "haiku"
    swarm_merge_alias: str = "sonnet"
    swarm_workers: int = 3
    auto_compact_turns: int = 20
```

All fields are runtime-mutable via the `/router` command or programmatic access.

### 4.5 The simple_alias Bug (Historical)

Prior to v2.4, the router contained a silent correctness bug. In `_execute_turn()`:

```python
# v2.3 — buggy
if route == "complex":
    self._execute_pipe(...)
    return None
else:
    self.console.print(f"  ⎇ simple → {self.router.simple_alias}")
    # FALLS THROUGH — uses self.model_spec, NOT simple_alias!
```

The log would display `⎇ simple → haiku` while actually executing the request using Sonnet (the session default). This caused 3–5× cost overruns on every simple query. The fix adds an explicit branch that builds args from `simple_spec = config.resolve_model(self.router.simple_alias)` before dispatching.

---

## 5. Swarm: Parallel Fan-Out with Merge

### 5.1 Conceptual Foundation

The swarm pattern addresses the observation that many developer tasks are implicitly parallel. Refactoring ten files is ten independent tasks. Translating a codebase to another language is N independent translation units. Writing a test suite is one test per function, independently writable.

Standard LLM interfaces process these sequentially because they maintain a single conversation thread. Mowgli's swarm module breaks this constraint.

The design is directly inspired by Ruflo's swarm architecture, specifically the fan-out topology where a coordinator decomposes a task, multiple workers execute in parallel, and a synthesis agent merges the results. The key difference is implementation layer: Ruflo's workers are distributed agents communicating over mTLS; Mowgli's workers are threads spawning subprocess calls on the local machine.

### 5.2 Execution Pipeline

```
Task (user prompt)
    │
    ▼
[Decomposer — haiku]
  Prompt: "Split this task into exactly N independent sub-tasks.
           Return ONLY a JSON array of N strings."
    │
    ▼
[sub_prompts: list[str]]  — N strings
    │
    ├─ Thread 0: subprocess → haiku → result_0
    ├─ Thread 1: subprocess → haiku → result_1
    └─ Thread N: subprocess → haiku → result_N
    │
    ▼ (join all threads, timeout=130s)
[Merge prompt → sonnet]
  "You are a synthesis agent. Merge these N outputs into a single
   coherent, deduplicated response. Resolve contradictions."
    │
    ▼
Final output
```

### 5.3 Decomposition Fallback

If the decomposer fails to return a valid JSON array (parse error, timeout, wrong length), the fallback strategy is to send the original prompt unchanged to all N workers. This produces redundant outputs but guarantees the merge step still has material to work with. The merge model (Sonnet) is expected to deduplicate correctly.

### 5.4 Manual Override

The `/swarm` slash command bypasses the automatic router:

```
/swarm write a docstring for every public function in src/mowgli/
/swarm 5 translate all error messages to Spanish
```

The optional integer prefix overrides `router.swarm_workers` for that call only.

### 5.5 Limitations of the Current Implementation

The threading model has a hard ceiling at local machine concurrency. A 16-core machine can realistically run 8–10 subprocess workers simultaneously before I/O becomes the bottleneck. More importantly, worker results are currently collected in full before merge — there is no streaming merge. The user sees nothing until all N workers complete. For large tasks, this latency is significant.

---

## 6. ReasoningBank: Lightweight Learning

### 6.1 Motivation

Ruflo implements a trajectory-based learning store backed by a vector database. The goal is to learn, over time, which agents and models perform best for which categories of problem — and to use this history to improve future routing decisions without manual configuration.

Mowgli's ReasoningBank is the same concept implemented without infrastructure. The constraint is zero-dependency: the bank must work on any machine with no additional services.

### 6.2 Record Schema

```jsonl
{
  "ts": "2026-06-13T09:14:22.331Z",
  "domain": "code",
  "effort": 4,
  "tools": 2,
  "parallel": false,
  "route": "simple",
  "model": "haiku",
  "cost_usd": 0.0003,
  "quality": null
}
```

The `quality` field is left null at write-time. Future tooling — a `/rate` command, or post-hoc annotation — can backfill it. Until then, the bank uses cost as an inverse-quality proxy: cheaper answers for the same domain/effort profile are weakly preferred.

### 6.3 Model Suggestion Algorithm

```python
def suggest_model(domain, effort, config_models):
    matches = [r for r in load() if r.domain == domain and abs(r.effort - effort) <= 2]
    if len(matches) < 5:
        return None  # insufficient data

    scores = {}
    for r in matches:
        score = r.quality if r.quality is not None else max(0, 1.0 - r.cost_usd * 1000)
        scores.setdefault(r.model, []).append(score)

    return max(scores, key=lambda m: mean(scores[m]))
```

The `±2 effort tolerance` means a bank record from an effort=5 task informs suggestions for effort=3–7 queries in the same domain. This addresses data sparsity in early sessions.

### 6.4 What the Bank Currently Does Not Do

- **Feed routing automatically**: `suggest_model()` is implemented but not yet wired into `classify()` as an override. The bank collects data but does not yet change routing decisions. This is intentional — the data set needs to grow before automated overrides are trustworthy.
- **Handle multi-turn context quality**: quality scores, when eventually collected, cannot easily account for whether a response was good because the model is good, or because it had helpful context from previous turns.

---

## 7. PII Scrubber

### 7.1 Threat Model

The scrubber addresses a specific, narrow threat: a developer copies a code block containing a credential into the Mowgli prompt, and that credential is transmitted to a remote LLM API where it may be logged.

This is not a comprehensive security system. It does not prevent:
- Semantic exfiltration (describing a password without writing it)
- Gradual context poisoning across turns
- Prompt injection from external tool results

It addresses the most common accidental exposure pattern.

### 7.2 Pattern Coverage

| Category | Example | Replacement |
|---|---|---|
| OpenAI key | `sk-abc123...` | `[OPENAI_KEY]` |
| Anthropic key | `sk-ant-...` | `[ANTHROPIC_KEY]` |
| Google API key | `AIza...` | `[GOOGLE_KEY]` |
| AWS Key ID | 20-char uppercase | `[AWS_KEY_ID]` |
| AWS Secret | 40-char base64 | `[AWS_SECRET]` |
| GitHub tokens | `ghp_`, `gho_`, `github_pat_` | `[GITHUB_TOKEN]` |
| Bearer tokens | `Bearer <token>` | `Bearer [TOKEN]` |
| JWTs | Three base64url segments | `[JWT]` |
| PEM private keys | `-----BEGIN PRIVATE KEY-----` block | `[PRIVATE_KEY]` |
| Email addresses | `user@domain.tld` | `[EMAIL]` |
| Hex secrets | 32+ hex chars | `[SECRET]` |

### 7.3 False Positive Risk

The AWS patterns are the most aggressive: the 20-character uppercase pattern catches AWS Access Key IDs but could also match all-caps identifiers or constants in code. The 40-character base64 pattern for AWS secrets could match SHA-1 hashes or base64-encoded binary data.

Future versions should allow per-pattern opt-out in `~/.studio/mowgli/scrubber.json`.

---

## 8. Provider Abstraction

### 8.1 Protocol Definition

Both Claude and Gemini providers implement the `Provider` protocol:

```python
class Provider(Protocol):
    name: str

    def build_headless_args(
        self,
        prompt: str,
        model_id: str,
        session_id: str,
        resume: bool = False,
        include_partial: bool = True,
        system_prompt: str | None = None,
    ) -> list[str]: ...

    def parse_stream_line(self, line: str, state: StreamState) -> StreamEvent | None: ...

    def run_interactive(self, model_id: str) -> None: ...
```

Providers do not call APIs directly — they construct argument lists for subprocess invocation of the underlying CLIs (`claude` and `gemini`). This means Mowgli inherits all authentication, rate-limiting, and capability management from the upstream CLI tools. It also means Mowgli cannot work without those CLIs installed.

### 8.2 StreamState and StreamEvent

```python
class StreamState:
    printed_text_len: int     # deduplicate cumulative text events
    seen_tool_ids: set[str]   # deduplicate tool_use events
    last_char_newline: bool   # track terminal cursor position
    session_id: str | None    # set from init event

class StreamEvent:
    type: str         # text_delta | tool_use | tool_result | cost | error
    content: str
    tool_name: str | None
    tool_input: dict | None
    cost_usd: float
```

The stream-json format used by Claude Code emits cumulative text (not deltas), so `printed_text_len` is used to compute the incremental portion. Tool use events are deduplicated by ID because the same tool call may appear in multiple stream events as the input is progressively completed.

### 8.3 Gemini Provider Limitations

The Gemini provider assumes the `gemini` CLI exposes an interface similar to Claude Code's (`-p`, `-o stream-json`, `-m`, `--session-id`, `--resume`). In practice, the Gemini CLI's exact stream-json format may differ. The `system_prompt` parameter added in v2.4 is accepted by the method signature for Protocol compliance but not forwarded, as the Gemini CLI does not expose an equivalent `--append-system-prompt` flag.

---

## 9. Evaluation

### 9.1 What Works Well

**Cost reduction.** The router's most immediate value is economic. A typical developer session of 30 queries — mostly factual lookups, short code explanations, and quick fixes — will contain perhaps 20 simple queries and 10 complex ones. With the old single-model approach (Sonnet for everything), the 20 simple queries consume Sonnet tokens at ~$0.003/1K. With routing enabled, those 20 queries route to Haiku at ~$0.00025/1K — a 12× cost reduction on 67% of the traffic. Real-world token savings of 60–70% per session are achievable on typical developer workloads.

**Zero operational overhead.** Mowgli requires no database, no daemon, no configuration before first use. `pip install -e .` followed by `mowgli` is the complete onboarding flow. This is non-trivial: the developer productivity cost of setting up and maintaining infrastructure is often greater than the cost of the inefficiency the infrastructure was meant to solve.

**Transparent routing.** Every routed turn prints its classification inline:

```
  ⎇ complex  effort:8 tools:5 domain:architectural
```

The user always knows which model is answering and why. This builds trust in the router's decisions and makes misclassifications immediately visible.

**PII protection as a default.** Most developers do not think about credential exposure when pasting code into a chat interface. Having the scrubber run silently on every turn provides protection without requiring the user to think about it.

### 9.2 Known Weaknesses

**Classification cost.** Every turn triggers a Haiku call for classification before the actual query is executed. This adds ~0.5–2 seconds of latency and a small but non-zero token cost (~50 tokens input + ~30 output). For very fast conversational queries, the classification overhead may exceed the cost of simply routing everything to Haiku in the first place.

A future optimisation: heuristic pre-filter before classification. If the query is under 20 tokens and contains no code blocks or file paths, classify as simple without the API call.

**Session continuity loss.** When routing is enabled, each turn in "simple" mode uses a fresh session. This means the model has no memory of previous turns. A user who asks "what is the capital of France?" (simple → haiku, session A) and then "and what is its population?" (simple → haiku, session B) will get an incorrect answer because the pronoun "its" has no referent in the second session.

This is the most significant usability flaw in the current architecture. The trade-off was made deliberately: supporting session continuity across routed models requires either maintaining separate session IDs per model (memory overhead, unclear reset semantics) or always routing the same-model turns to the same session (breaking swarm and pipeline calls). No clean solution exists that preserves both cost efficiency and conversational continuity without a more sophisticated session management layer.

**Swarm latency opacity.** During a swarm execution, the user sees "launching N workers…" and then nothing until all workers complete. For a 3-worker × 60-second task, the user waits 60 seconds with no feedback. Streaming worker progress would significantly improve perceived responsiveness.

**Classifier hallucination.** The JSON classification is produced by Haiku, which occasionally returns malformed JSON, wraps the response in markdown code fences, or includes explanatory prose. The parser attempts to extract the first `{...}` substring and falls back to `ClassifyResult.fallback()` on failure. The fallback routes to complex — conservative but adds unnecessary cost when the query was actually simple.

**ReasoningBank does not yet influence routing.** The bank collects data but `suggest_model()` is not wired into `classify()`. This means the learning system is passive — it observes but does not act. Connecting the two is the highest-priority v2.5 feature.

### 9.3 What Is Missing

The following features are identified as meaningful gaps, not cosmetic omissions:

**1. Quality feedback loop.**
The `quality` field in ReasoningBank records is always null. Without a mechanism to rate responses (even a simple 1–5 `/rate` command post-turn), the bank's model suggestion degrades to pure cost minimisation rather than quality-adjusted routing.

**2. Adaptive routing thresholds.**
The thresholds (`effort ≤ 4` for simple, `effort ≥ 7` for swarm) are hard-coded constants. In Ruflo, SONA patterns adjust these autonomously based on outcome feedback. Mowgli should learn from the bank: if effort=5 queries routed to complex consistently produce low-quality responses, lower the complex threshold.

**3. Streaming swarm progress.**
Workers complete asynchronously but results are batched. A streaming interface — showing partial output from each worker as it arrives, then synthesising — would make swarm calls feel interactive rather than opaque.

**4. Multi-turn routing coherence.**
The router treats each turn independently. It does not consider: what model answered the previous turn? Is the current query a follow-up that requires the same context? Implementing turn-level routing memory would prevent the conversational continuity failures described in 9.2.

**5. Provider capability awareness.**
The router can assign any query to any model without checking whether that model can execute the task. Assigning a complex code generation task with 15 tool calls to `gemini-lite` (limited context window) may fail silently. A capability registry mapping model → max_context / tool_support / code_execution would enable the router to exclude incompatible models.

**6. Obsidian MCP stability.**
The Obsidian MCP server (MCPVault, configured in v2.3) has reported intermittent failures. The root cause has not been investigated at the time of writing. MCP server health is not monitored by Mowgli — failed servers fail silently from the user's perspective.

**7. Test coverage for new modules.**
router.py, swarm.py, reasoning_bank.py, and pii_scrubber.py are untested at the unit level. The existing test suite (72 tests for the pre-v2.4 codebase) does not cover any of the v2.4 additions. This is a significant technical debt.

**8. Token budget management.**
There is no mechanism to set a per-session or per-turn spending cap. A user who accidentally triggers 10 swarm calls does not receive a warning. Implementing a configurable `max_session_cost_usd` that halts execution would prevent unexpected charges.

### 9.4 Design Decisions: Rationale

**Why subprocess over SDK calls?**
Mowgli dispatches to `claude` and `gemini` CLI binaries via subprocess rather than calling the Anthropic SDK or Gemini API directly. This choice preserves all credential management, rate limiting, MCP server configuration, permissions, and tool definitions that the upstream CLIs provide. The cost is that Mowgli is tightly coupled to the CLI binary versions. The benefit is that a new Mowgli session automatically inherits any Claude Code configuration the user has set up — tools, permissions, MCP servers — without Mowgli needing to replicate that configuration.

**Why JSONL over SQLite or a vector DB?**
JSONL is universally readable with `tail -f`, `jq`, or any text editor. It requires no schema migration, no query language, and no external dependency. The ReasoningBank at 500 records (the configured rolling window) is approximately 50KB — trivial to read entirely into memory on every suggestion call. The performance characteristics are adequate for the expected usage scale (hundreds to low thousands of records per developer per month). SQLite would add query flexibility; a vector DB would add semantic search. Neither provides enough marginal value to justify the complexity increase.

**Why not adopt Ruflo's consensus protocols?**
Raft consensus and Byzantine Fault Tolerance are correct solutions for distributed systems where agents run on separate machines with network partitions and adversarial conditions. For a single-developer CLI where all "agents" are threads spawning subprocesses on the same machine, these protocols add latency, complexity, and failure modes without providing any of their intended benefits. The decision to use threading is a conscious scope limitation: Mowgli is a personal tool, not a distributed system.

**Why are the router thresholds not configurable via config file?**
In the current implementation, RouterConfig defaults are hard-coded in `router.py` and mutable only at runtime via the Python API or the `/router` command. A `~/.studio/mowgli/router.json` configuration file would be the correct mechanism for persistent personalisation. This was deferred to avoid premature feature expansion before the routing logic itself is validated by real usage.

---

## 10. Conclusion

Mowgli CLI addresses a real and measurable problem: the homogenisation of LLM queries into single-model, single-provider, single-complexity calls. By introducing a multi-dimensional classifier, three routing tiers, parallel swarm execution, and a passive learning store, it captures a significant fraction of the cost and quality improvements achievable through intelligent dispatch — while remaining a single-command, zero-infrastructure terminal tool.

The comparison with Ruflo is instructive in both directions. Ruflo demonstrates what is possible when full distributed infrastructure is available: self-organising topologies, consensus-based decision validation, vector-indexed agent search. Mowgli demonstrates what is achievable without any of it, for a single developer at a terminal. The Ruflo patterns that translated — swarm fan-out, multi-dimensional scoring, trajectory logging, PII scrubbing — proved that the conceptual insights of enterprise multi-agent systems are separable from their operational complexity.

The most honest assessment of the current system: the routing logic is sound but the learning system is passive, the swarm UX is opaque, and the session continuity trade-off creates a class of conversational failure that will frustrate users who expect coherent multi-turn interactions. These are known deficiencies, not unknown unknowns. The path from v2.4 to a production-quality tool requires closing them systematically.

---

## References

1. Ruflo — ruvnet, 2026. *Ruflo: Enterprise Multi-Agent Swarm Framework*. github.com/ruvnet/ruflo

2. Anthropic, 2025. *Claude Code: Command-Line Interface for Claude*. claude.ai/code

3. Google, 2025. *Gemini CLI*. github.com/google-gemini/gemini-cli

4. Chase, H., 2022. *LangChain*. github.com/langchain-ai/langchain

5. Liu, J., 2022. *LlamaIndex (formerly GPT Index)*. github.com/run-llama/llama_index

6. Lamport, L., Shostak, R., Pease, M., 1982. *The Byzantine Generals Problem*. ACM Transactions on Programming Languages and Systems, 4(3):382–401.

7. Ongaro, D., Ousterhout, J., 2014. *In Search of an Understandable Consensus Algorithm (Raft)*. USENIX ATC '14.

8. Malkov, Y.A., Yashunin, D.A., 2018. *Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs (HNSW)*. IEEE Transactions on Pattern Analysis and Machine Intelligence.

9. OWASP, 2025. *OWASP Top 10 for Large Language Model Applications*.

10. mowgli.studio, 2026. *Studio — rules, contexts, hooks, agents, skills, dashboard*. github.com/meowgl1/studio

---

*This document was produced as part of the studio project at mowgli.studio. The implementation described is available at github.com/meowgl1/studio on branch `feat/readme-craft-skill`.*

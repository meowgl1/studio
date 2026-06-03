---
name: eval-harness
description: Build evaluation harnesses for AI/LLM features — define capability tests, baselines, pass rates, regressions
triggers:
  - "eval"
  - "evaluation"
  - "llm test"
  - "ai eval"
  - "build eval"
  - "evals-driven"
---

# Skill — Eval Harness

Evals are the test suite for AI/LLM features. Define before implementing.

## When to build an eval

- Any LLM call that produces structured output
- Any AI feature that needs reliability guarantees
- Before refactoring a prompt or model
- When a user reports unexpected AI behavior

## Eval structure

```
evals/
  {feature}/
    cases.jsonl         # test cases — input + expected output
    runner.py           # runs all cases, reports results
    baseline.json       # last recorded pass rates (committed)
```

## Case format (cases.jsonl)

One JSON object per line:

```jsonl
{"id": "classify-001", "input": "This product broke after one day", "expected_label": "complaint", "expected_sentiment": "negative"}
{"id": "classify-002", "input": "Amazing quality, will buy again!", "expected_label": "praise", "expected_sentiment": "positive"}
{"id": "classify-003", "input": "The delivery was late but product is fine", "expected_label": "mixed", "expected_sentiment": "neutral"}
```

## Runner template

```python
# evals/classify/runner.py
import asyncio
import json
from pathlib import Path
from dataclasses import dataclass
from app.ai.classify import classify_feedback  # the function being tested

CASES_FILE = Path(__file__).parent / "cases.jsonl"
BASELINE_FILE = Path(__file__).parent / "baseline.json"


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    expected: dict
    actual: dict
    error: str | None = None


async def run_case(case: dict) -> EvalResult:
    try:
        result = await classify_feedback(case["input"])
        passed = (
            result.label == case["expected_label"]
            and result.sentiment == case["expected_sentiment"]
        )
        return EvalResult(
            case_id=case["id"],
            passed=passed,
            expected={"label": case["expected_label"], "sentiment": case["expected_sentiment"]},
            actual={"label": result.label, "sentiment": result.sentiment},
        )
    except Exception as e:
        return EvalResult(case_id=case["id"], passed=False, expected={}, actual={}, error=str(e))


async def main():
    cases = [json.loads(l) for l in CASES_FILE.read_text().strip().splitlines()]
    results = await asyncio.gather(*[run_case(c) for c in cases])

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    pass_rate = passed / total

    print(f"\nResults: {passed}/{total} passed ({pass_rate:.1%})")

    # Show failures
    for r in results:
        if not r.passed:
            print(f"  FAIL [{r.case_id}]")
            print(f"    expected: {r.expected}")
            print(f"    actual:   {r.actual}")
            if r.error:
                print(f"    error:    {r.error}")

    # Compare to baseline
    if BASELINE_FILE.exists():
        baseline = json.loads(BASELINE_FILE.read_text())
        baseline_rate = baseline.get("pass_rate", 0)
        delta = pass_rate - baseline_rate
        symbol = "▲" if delta >= 0 else "▼"
        print(f"\nBaseline: {baseline_rate:.1%}  →  Now: {pass_rate:.1%}  {symbol} {abs(delta):.1%}")
        if pass_rate < baseline_rate - 0.05:
            print("⚠ REGRESSION — pass rate dropped > 5%")

    # Save new baseline
    BASELINE_FILE.write_text(json.dumps({"pass_rate": pass_rate, "total": total, "passed": passed}))

    return 0 if pass_rate >= 0.8 else 1  # exit 1 if below threshold


if __name__ == "__main__":
    exit(asyncio.run(main()))
```

## pass@1 and pass@3 metrics

For non-deterministic tasks (generation, summarization):

```python
async def pass_at_k(case: dict, k: int = 3) -> float:
    """Run case k times, return fraction that passed."""
    results = await asyncio.gather(*[run_case(case) for _ in range(k)])
    return sum(1 for r in results if r.passed) / k
```

Report both `pass@1` (single run) and `pass@3` (average of 3) for release-critical paths.

## Eval-driven workflow

```
1. Write cases.jsonl  ← define success before writing the prompt
2. Run eval → RED (all fail, feature doesn't exist yet)
3. Implement feature / write prompt
4. Run eval → target GREEN (≥ 80% pass rate)
5. Commit baseline.json
6. On any prompt or model change → re-run eval before merging
```

## Regression guard

Add to CI:

```yaml
# .github/workflows/evals.yml
- name: Run evals
  run: python evals/classify/runner.py
  # Fails CI if pass_rate drops > 5% below baseline
```

## Prompt versioning

Track prompts like code:

```python
CLASSIFY_PROMPT_V2 = """
Classify the following customer feedback.
Return JSON: {"label": "complaint|praise|mixed|question", "sentiment": "positive|negative|neutral"}

Feedback: {input}
"""
```

Version in filename or constant — never edit in place without running evals first.

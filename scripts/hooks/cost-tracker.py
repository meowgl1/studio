#!/usr/bin/env python3
"""
Stop hook — tracks token usage and context window utilization.
On Claude Pro (subscription), there is no per-token cost — this hook
tracks context consumption instead: useful for understanding compaction
risk and session efficiency.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import (
    load_session,
    save_session,
    context_utilization,
    get_project_name,
)


def main():
    input_tokens = int(os.environ.get("CLAUDE_INPUT_TOKENS", 0))
    output_tokens = int(os.environ.get("CLAUDE_OUTPUT_TOKENS", 0))

    if input_tokens == 0 and output_tokens == 0:
        return  # no token data available, skip silently

    state = load_session()
    state["input_tokens"] = state.get("input_tokens", 0) + input_tokens
    state["output_tokens"] = state.get("output_tokens", 0) + output_tokens

    total_in = state["input_tokens"]
    total_out = state["output_tokens"]
    utilization = context_utilization(total_in)

    if utilization >= 80:
        warn = " ⚠️  compaction likely soon"
    elif utilization >= 50:
        warn = " — context half full"
    else:
        warn = ""

    state["context_utilization_pct"] = utilization
    save_session(state)

    project = get_project_name()
    print(
        f"[studio] tokens: {total_in:,} in / {total_out:,} out · context: {utilization}%{warn} · {project}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

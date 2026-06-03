#!/usr/bin/env python3
"""
Stop hook — tracks token usage and estimated cost.
Reads Claude Code environment variables for token counts.
Writes a running total to the project changelog.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import (
    load_session,
    save_session,
    estimate_cost,
    append_to_changelog,
    get_project_name,
)


def main():
    # Claude Code exposes token counts via environment variables
    input_tokens = int(os.environ.get("CLAUDE_INPUT_TOKENS", 0))
    output_tokens = int(os.environ.get("CLAUDE_OUTPUT_TOKENS", 0))

    if input_tokens == 0 and output_tokens == 0:
        return  # no token data available, skip silently

    state = load_session()
    state["input_tokens"] = state.get("input_tokens", 0) + input_tokens
    state["output_tokens"] = state.get("output_tokens", 0) + output_tokens

    total_in = state["input_tokens"]
    total_out = state["output_tokens"]
    cost = estimate_cost(total_in, total_out)

    state["estimated_cost_usd"] = round(cost, 4)
    save_session(state)

    # Print cost summary to stderr
    project = get_project_name()
    print(
        f"[studio] cost: {total_in:,} in / {total_out:,} out · ~${cost:.3f} USD · project: {project}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

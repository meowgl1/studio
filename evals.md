# Agent Evals Framework

## Every agent file MUST define
- success_criteria: observable outcomes that mean the task is done
- failure_signals: warning signs that something went wrong
- escalation_trigger: when agent stops and asks human before continuing
- eval_examples: minimum 3 golden examples (input → expected output)

## Session logging (write to memory/facts.md after each agent session)
- what was asked
- what was done
- success/fail
- unexpected behavior

## Standard metrics (apply to all agents)
- Task completion: did it finish what was asked?
- Constraint compliance: did it respect IGNORE.md?
- Schema compliance: output matches expected format?
- Side effects: anything modified outside declared tool scope?

## Failure = stop and report
If agent detects it violated a constraint or produced unexpected output:
1. Stop immediately
2. Report: what happened, what was expected, what was produced
3. Wait for explicit instruction before continuing
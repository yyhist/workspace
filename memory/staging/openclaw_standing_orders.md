# OpenClaw Standing Orders Documentation

Source: https://docs.openclaw.ai/automation/standing-orders

## Core Concept

Standing orders grant your agent **permanent operating authority** for defined programs. Instead of giving individual task instructions each time, you define programs with clear scope, triggers, and escalation rules — and the agent executes autonomously within those boundaries.

**Without standing orders:**
- You must prompt the agent for every task
- The agent sits idle between requests
- Routine work gets forgotten or delayed
- You become the bottleneck

**With standing orders:**
- The agent executes autonomously within defined boundaries
- Routine work happens on schedule without prompting
- You only get involved for exceptions and approvals
- The agent fills idle time productively

## Anatomy of a Standing Order

```
## Program: [Name]

**Authority:** What the agent is authorized to do
**Trigger:** When to execute (schedule, event, or condition)
**Approval gate:** What requires human sign-off before acting
**Escalation:** When to stop and ask for help

### Execution steps
1. Step one
2. Step two
3. ...

### What NOT to do
- Boundary one
- Boundary two
```

## Execute-Verify-Report Pattern

Every task in a standing order should follow this loop:

1. **Execute** — Do the actual work (don't just acknowledge)
2. **Verify** — Confirm the result is correct
3. **Report** — Tell the owner what was done and verified

### Execution Rules
- Every task follows Execute-Verify-Report. No exceptions.
- "I'll do that" is not execution. Do it, then report.
- "Done" without verification is not acceptable. Prove it.
- If execution fails: retry once with adjusted approach.
- If still fails: report failure with diagnosis. Never silently fail.
- Never retry indefinitely — 3 attempts max, then escalate.

## Best Practices

**Do:**
- Start with narrow authority and expand as trust builds
- Define explicit approval gates for high-risk actions
- Include "What NOT to do" sections
- Combine with cron jobs for reliable execution
- Review agent logs weekly
- Update standing orders as needs evolve

**Avoid:**
- Grant broad authority on day one
- Skip escalation rules
- Assume the agent will remember verbal instructions
- Mix concerns in a single program
- Forget to enforce with cron jobs

## Application to Current Work

The current `self-exploration/SKILL.md` v4.1 is essentially a standing order for autonomous action. It defines:
- **Scope:** Run/Build/Reconfigure/Plan tasks
- **Triggers:** Every 20 minutes via cron
- **Approval gates:** Human help only for structural blockers
- **Escalation:** Report blockers, don't silently fail

This aligns well with the standing orders pattern.

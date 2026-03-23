# Agent Collaboration Contract

This file defines how the primary agent and any delegated sub-agents should operate in this
repository.

It is repo-local execution policy, not product behavior.

## Purpose

- Keep agent behavior consistent across sessions
- Make delegation explicit, bounded, and reviewable
- Preserve one clear owner for user communication and final correctness
- Reduce vague or improvisational agent behavior

## Operating Model

- One lead agent owns the user request end to end
- Sub-agents are optional accelerators, not replacements for ownership
- The lead agent is responsible for synthesis, correctness, and the final response
- Sub-agents report findings or complete scoped work, then hand control back to the lead agent

## Request Triage

Before acting, the lead agent should classify the request:

- Question or explanation: inspect only the needed context and answer directly; do not edit files
  unless the user asks
- Planning or research: gather context, produce a scoped answer or plan, and avoid persistent edits
- Implementation or bug fix: inspect the relevant code, make the change, verify it, and close with
  a concise outcome
- Review: prioritize findings, risks, regressions, and missing tests before any summary
- Prompt or agent-instruction work: read `.codex/skills/agent-prompt-design/SKILL.md` and sample
  the prompt corpus before writing instructions

## Lead Agent Responsibilities

- Read the mandatory repo context in `AGENTS.md` before meaningful changes
- Use the relevant repo-local skill files when the task matches them
- Gather enough context before acting; prefer existing repo patterns over invention
- Keep user updates brief, factual, and progress-oriented
- Make reasonable assumptions when the risk is low; ask the user only when ambiguity is material
- Verify important sub-agent claims locally before relying on them in final decisions
- Own all final recommendations, edits, and communication to the user
- Update `.agent/memory.md` after meaningful milestones that change repo understanding or working
  rules

## When To Use Sub-Agents

Use sub-agents only when delegation materially improves throughput and the work can be bounded.

Good uses:

- Parallel exploration of distinct repo areas
- Targeted read-only investigations
- Disjoint implementation tasks with separate write scopes
- Sidecar verification while the lead agent continues non-overlapping work

Avoid delegation when:

- The immediate next step is blocked on the answer and the lead agent can do it directly
- The task is ambiguous and needs tight user interaction
- Multiple agents would touch the same file or a shared contract
- The delegation would duplicate work or add more coordination than value

## Supported Sub-Agent Roles

If the runtime supports role selection, use the narrowest fit:

- `explorer`: read-only discovery, architecture tracing, file location, reference gathering, and
  risk identification
- `worker`: bounded implementation or fix work with explicit file ownership
- `default`: use only when no narrower role fits or the runtime does not expose specialized roles

Do not invent role behavior that conflicts with the actual runtime.

## Sub-Agent Contract

Every sub-agent must:

- Receive a concrete task, expected output, and explicit boundaries
- Stay within its assigned scope
- Treat the rest of the repo as live and avoid reverting others' work
- Report verified facts separately from inference
- Cite the files inspected and the checks or commands run
- Return control once its scoped task is complete or blocked

For write-capable sub-agents:

- Assign owned files or modules up front
- Avoid shared contracts unless explicitly assigned
- Validate the touched scope with the smallest relevant checks
- Surface blockers instead of improvising broad refactors

## Communication Contract

The lead agent should communicate in a way that is:

- Concise
- Direct
- Technically explicit
- Free of filler or unnecessary reassurance

Communication rules:

- State what is being checked, changed, or verified
- Distinguish verified facts from inference when it matters
- For review tasks, present findings first
- For long tasks, send short progress updates instead of long explanations
- Sub-agents do not speak to the user as the final authority; they report back to the lead agent

## Evidence And Quality Bar

- Prefer existing repo patterns, naming, and boundaries
- Keep LLM behavior behind narrow interfaces
- Do not trust model output without parsing, recovery, and validation
- Run the smallest relevant checks for the touched scope
- Do not claim work is verified if no verification was run
- Avoid new dependencies or broad architecture changes unless clearly justified

## Repo-Specific Ground Rules

- Use `apps/aegra` to confirm framework behavior before guessing
- Use `apps/system-prompts-and-models-of-ai-tools` as a comparative corpus, not a copy source
- Keep frontend request details in hooks and API layers rather than UI components
- Keep routing, parsing, validation, correction, and storage concerns separated
- Preserve event-driven and undo-friendly backend design decisions already recorded in repo docs

## Stop Conditions

- The lead agent should stop only when the request is fully handled or a concrete blocker remains
- If blocked, report the exact blocker, what was tried, and the smallest decision needed from the
  user
- Finished sub-agents should be closed once their results are integrated

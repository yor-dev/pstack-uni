---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

{{#claude}}
Fan out N parallel subagent workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.
{{/claude}}
{{#codex}}
Fan out N parallel local workers. They may cover separate slices, race the same
brief, or mix both. The parent waits, aggregates, and returns one report.
{{/codex}}

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
{{#claude}}
3. Set N from the user or derive it from the shape. N is total workers, regardless of the available concurrency.
4. Pick the worker model and effort from the `swarm workers` line in the pstack model configuration section of the project-root `AGENTS.md`. If the rule or that line is missing, use `grok-4.7-xhigh-fast`. `auto` and `inherit-parent` mean the parent model and effort. If a configured model is unavailable, use the default and say so. If that default is also unavailable, use the closest available model in the same family. If none exists, ask the user to choose an available model. For a model race, name each arm's model up front.
{{/claude}}
{{#codex}}
3. Set N from the user or derive it from the shape. N is total workers, not the local concurrency limit.
4. Pick the worker model from the `swarm workers` line in the pstack model configuration section of the project-root `AGENTS.md`. If the section or that line is missing, use `grok-4.7-xhigh-fast`. For `auto` or `inherit-parent`, use the parent model and effort. If the configured model is unavailable, use the default and say so. If the default is unavailable, use the closest valid model ID of the same family from the available models; if none exists, ask for a model choice. For a model race, name each arm's model up front.
{{/codex}}
5. Give each worker its own writable output when it writes. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method (sample count, what one sample is, order). The worker records both in its result.

## Phase B: Fan out

{{#claude}}
Spawn all N workers concurrently using the step 4 model and effort.

Give each code-writing worker its own local worktree. When a worker must start from a specified branch, use a checkout of that branch and include its local path in the brief.
{{/claude}}
{{#codex}}
Start all N workers as parallel subagents without the poteto-agent body, using each role's configured model and effort. Give each code-writing worker its own local worktree.
When a worker must start from a specified branch, use a checkout of that branch
and include its local path in the brief.
{{/codex}}

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

{{#claude}}
Read the result and terminal report for every worker. Drop a result that does not record the SHAs and method its brief names, and rerun that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.
{{/claude}}
{{#codex}}
Read every worker result. Drop a result that does not record the SHAs and method its brief names, and rerun that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a
race, apply the selection rule declared up front. Use first pass, rank all, or
best-of. Do not paste raw worker dumps.
{{/codex}}

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.

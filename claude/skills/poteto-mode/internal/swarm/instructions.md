---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

Fan out N parallel local native `Agent` workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers, not the local Agent concurrency limit.
4. Pick the worker model from the `swarm workers` line in `~/.claude/rules/pstack-models.md`. If the rule or that line is missing, use `grok-4.7-xhigh-fast`. For `auto` or `inherit-parent`, omit `model` so the workers run on the parent model. If the Agent tool rejects a slug, use the default and say so. If it rejects the default, use the closest valid slug of the same family from its error message. For a model race, name each arm's model up front.
5. Give each worker its own writable output when it writes.

## Phase B: Fan out

Spawn all N workers in one message using local native `Agent` calls with `subagent_type: pstack:general-purpose-<effort>`, `run_in_background: true`, and the step 4 model. Use the unsuffixed `general-purpose` type and omit `model` for `auto` or `inherit-parent`, as defined in the Subagents section.

Give each code-writing worker its own local worktree. When a worker must start from a specified branch, use a checkout of that branch and include its local path in the brief.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the local Agent result and terminal report for every worker. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.

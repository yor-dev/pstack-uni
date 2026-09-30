---
name: setup-pstack
description: Configure pstack's model and effort choices per role in the project AGENTS.md. Use for setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write the pstack model configuration in the active project's root `AGENTS.md`. Keep `CLAUDE.md` in that directory as a relative symlink to `AGENTS.md`, so both tools read the same project instructions.

## Steps

### 1. Detect available models

Identify the models and effort levels available in this session. If they cannot be determined, ask the user. Do not save a concrete model choice that has not been confirmed available. The aliases `inherit-parent` and `auto` are always valid.

### 2. Load current state

The upstream role choices are listed below. Their Cursor names encode model family and effort together. Resolve each to an available model and a separate effort level. A choice with no available counterpart needs a user choice in step 3.

```
feature, refactoring: grok-4.7-xhigh-fast
bug-fix: grok-4.7-xhigh-fast
perf-issue: grok-4.7-xhigh-fast
hillclimb: grok-4.7-xhigh-fast
judgment and prose: claude-opus-5-5-max
hardest tasks: claude-opus-5-5-max
how explorer: grok-4.7-xhigh-fast
how explainer: claude-opus-5-5-max
why investigators: grok-4.7-xhigh-fast
why synthesizer: claude-opus-5-5-max
reflect tooling: gpt-5.6-sol-max
reflect judgment, divergent, synthesizer: claude-opus-5-5-max
arena runners: claude-opus-5-5-max, gpt-5.6-sol-max, grok-4.7-xhigh-fast
arena cross-judge pool: claude-opus-5-5-max, gpt-5.6-sol-max, grok-4.7-xhigh-fast
swarm workers: grok-4.7-xhigh-fast
architect runners: claude-opus-5-5-max, gpt-5.6-sol-max, grok-4.7-xhigh-fast
interrogate reviewers: claude-opus-5-5-max, gpt-5.6-sol-max, grok-4.7-xhigh-fast
```

If the pstack model configuration section of the project-root `AGENTS.md` exists, read its `# budget` line and role values as the current choices. Otherwise start from the upstream choices above. A line whose role is not listed above, such as `how critics`, is from a retired role. Drop it.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Offer these four options with these exact labels, and name the current budget when the rule records one.

- `unlimited — keep max`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Build the working table from the upstream choices, and on a re-run keep any role changed by family, list, or alias (`inherit-parent`, `auto`). `unlimited` leaves every effort as in that table. `large`, `medium`, and `small` set the effort of every real model entry, panel entries included, to `xhigh`, `high`, or `medium`. Store model and effort separately. If a model does not support the target, choose its highest supported effort at or below the target on the ladder `max` > `xhigh` > `high` > `medium` > `low`; if none exists, mark the role as needing a choice. `inherit-parent` and `auto` do not change.

**(c) Show the roles and confirm.** Show every role with its model and effort, marking unavailable choices as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the available models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model and effort) as the options. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one entry whose model family differs from the parent's when possible. `swarm workers` is the default model and effort for every worker unless a race or comparison assigns another choice per arm.

### 4. Validate

Every concrete model and effort written must be available in this session. `inherit-parent` and `auto` always pass. If a choice is unavailable, stop and ask again.

### 5. Write the rule

Find the active project root (the Git root, or the current working directory if there is no Git root). Read its `AGENTS.md`, or create it if absent. Replace only the section between `<!-- pstack-models:start -->` and `<!-- pstack-models:end -->`, or append it if absent. Preserve all other instructions. The section has a `# budget` line with the chosen label and its target effort, and one line per role using the labels above. Replace the whole section so re-runs stay idempotent. A real model value is an object with `model` and `effort`; an alias is `inherit-parent` or `auto`. Panel values are lists of those entries. Fill every value with the confirmed choices. Example value shapes:

```
<!-- pstack-models:start -->
## pstack model configuration. One line per role. Delete a line to fall back to the upstream choice.
# budget: large (xhigh)
how explainer: {"model": "<confirmed model>", "effort": "xhigh"}
swarm workers: inherit-parent
arena runners: [{"model": "<confirmed model>", "effort": "xhigh"}, "auto"]
<!-- pstack-models:end -->
```

Ensure `CLAUDE.md` in the same directory is a relative symlink whose target is `AGENTS.md`. If it is already that link, leave it alone. If it is another file or link, preserve any instructions not already in `AGENTS.md` before replacing it; omit an `@AGENTS.md` import to avoid a self-import. Resolve conflicting instructions with the user before replacing either file. Never write through the symlink.

### 6. Confirm

Tell the user the project instructions and symlink were written and that they apply to new sessions in this project. Re-running this skill updates the pstack section.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one." On yes, read and follow [create-verification-skill](../poteto-mode/internal/create-verification-skill/instructions.md). On no, move on without pushing.

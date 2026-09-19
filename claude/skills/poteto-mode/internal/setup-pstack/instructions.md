---
name: setup-pstack
description: Configure which models pstack uses per role and at what reasoning budget. Detects your available models and writes an always-applied rule that overrides the skill defaults. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write `~/.claude/rules/pstack-models.md`, an always-applied rule that sets pstack's model and effort per role.

## Steps

### 1. Detect available models

Enumerate the model selectors accepted by the `Agent` tool in this session and their supported effort levels. A selector may be an alias such as `opus` rather than a full model ID. A models API or CLI can identify the available models behind those selectors, but the Agent schema determines which values can be passed. If you cannot detect any, ask the user to paste the selectors they have access to. Never write a model selector you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not model selectors.

### 2. Load current state

The upstream role choices are listed below. Their Cursor names encode model family and effort together; they are not literal Agent model arguments. Resolve each to a detected selector for the same model and its separate effort setting. A choice with no available counterpart needs a user choice in step 3.

```
feature, refactoring: grok-4.6-fast-xhigh
bug-fix: grok-4.6-fast-xhigh
perf-issue: grok-4.6-fast-xhigh
hillclimb: grok-4.6-fast-xhigh
judgment and prose: claude-fable-5-1-thinking-max
hardest tasks: claude-fable-5-1-thinking-max
how explorer: grok-4.6-fast-xhigh
how explainer: claude-fable-5-1-thinking-max
why investigators: grok-4.6-fast-xhigh
why synthesizer: claude-fable-5-1-thinking-max
reflect tooling: gpt-5.6-sol-max
reflect judgment, divergent, synthesizer: claude-fable-5-1-thinking-max
arena runners: claude-fable-5-1-thinking-max, gpt-5.6-sol-max, grok-4.6-fast-xhigh, claude-opus-5-thinking-xhigh
arena cross-judge pool: claude-fable-5-1-thinking-max, gpt-5.6-sol-max, grok-4.6-fast-xhigh, claude-opus-5-thinking-xhigh
swarm workers: grok-4.6-fast-xhigh
architect runners: claude-fable-5-1-thinking-max, gpt-5.6-sol-max, grok-4.6-fast-xhigh, claude-opus-5-thinking-xhigh
interrogate reviewers: claude-fable-5-1-thinking-max, gpt-5.6-sol-max, grok-4.6-fast-xhigh, claude-opus-5-thinking-xhigh
```

If `~/.claude/rules/pstack-models.md` exists, read its `# budget` line and role values as the current choices. Otherwise start from the upstream choices above.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Prefer AskUserQuestion over free text. Offer these four options with these exact labels, and name the current budget when the rule records one.

- `unlimited — keep max`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Build the working table from the upstream choices, and on a re-run keep any role changed by family, list, or alias (`inherit-parent`, `auto`). `unlimited` leaves every effort as in that table. `large`, `medium`, and `small` set the effort of every real model entry, panel entries included, to `xhigh`, `high`, or `medium`. Model ID and effort are separate fields; do not append effort to a Claude Code model ID. If a model does not support the target, choose its highest supported effort at or below the target on the ladder `max` > `xhigh` > `high` > `medium` > `low`; if none exists, mark the role as needing a choice. `inherit-parent` and `auto` do not change.

**(c) Show the roles and confirm.** Show every role with its model and effort, marking unavailable choices as needing a choice. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model and effort) as the options. Prefer AskUserQuestion over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one entry whose model family differs from the parent's when possible. `swarm workers` is the default model and effort for every worker unless a race or comparison assigns another choice per arm.

### 4. Validate

Every model selector written must be accepted by the current Agent schema and resolve to an available model, with an effort supported by that model. A canonical ID from a model catalog alone does not pass this check. `inherit-parent` and `auto` always pass. If a chosen model or effort is not available, stop and ask again.

### 5. Write the rule

Write `~/.claude/rules/pstack-models.md` without `paths` frontmatter, with a `# budget` line with the chosen label and its target effort, and one line per role using the labels above. Overwrite the whole file so re-runs stay idempotent. A real model value is an object with `model` (the Agent selector) and `effort`; an alias is `inherit-parent` or `auto`. Panel values are lists of those entries. Fill every value with the confirmed choices. Example value shapes:

```
# pstack model configuration. One line per role. Delete a line to fall back to the upstream choice.
# budget: large (xhigh)
how explainer: {"model": "<confirmed Agent selector>", "effort": "xhigh"}
swarm workers: inherit-parent
arena runners: [{"model": "<confirmed Agent selector>", "effort": "xhigh"}, "auto"]
```

In `Agent` calls, the object's `model` is the model argument. Its effort selects the native agent definition: `pstack:poteto-agent-<effort>` for poteto delegates or `pstack:general-purpose-<effort>` for workflow delegates, or `pstack:comment-sicko-<effort>` for Comment Sicko. These definitions cover `low`, `medium`, `high`, `xhigh`, and `max`. For `inherit-parent` or `auto`, use the corresponding unsuffixed `pstack:poteto-agent`, `general-purpose`, or `pstack:comment-sicko` and omit the model argument. Panel entries still count individually.

### 6. Confirm

Tell the user the rule was written and that it applies to new sessions. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke [`/create-verification-skill`](../create-verification-skill/instructions.md) (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.

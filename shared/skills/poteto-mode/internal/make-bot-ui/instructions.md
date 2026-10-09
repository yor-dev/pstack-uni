---
{{#claude}}
name: make-bot-ui
description: Build a custom UI that wakes a Cursor cloud routine through an API trigger.
{{/claude}}
{{#codex}}
name: Make Bot UI
description: >-
  Use when building a custom UI (page, dashboard, buttons) that should wake a
  Grok Bot over a webhook, when the user must provide a webhook sender key, or
  when exposing that UI on Tailscale.
{{/codex}}
---
{{#codex}}
# Make a bot UI
{{/codex}}

{{#claude}}
# Make Bot UI
{{/claude}}
{{#codex}}
This source skill requires a cloud routine. Cloud use is excluded from the
Codex distribution, and the current native surface has no verified webhook
routine, secret-value card, or wake-event contract. Do not execute the cloud
routine workflow from Codex.
{{/codex}}

{{#claude}}
This skill is excluded from the local Claude distribution because it depends on Cursor cloud routines and API-triggered wakeups. It has no local subagent translation. Do not use this file as an active procedure.

The upstream contract remains available at the pinned [make-bot-ui skill](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/make-bot-ui/SKILL.md) for reference only.
{{/claude}}
{{#codex}}
The upstream contract remains available as a fixed reference at
[upstream SKILL.md](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/make-bot-ui/SKILL.md).
{{/codex}}

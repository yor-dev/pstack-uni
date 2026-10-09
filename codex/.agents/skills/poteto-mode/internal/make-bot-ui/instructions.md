---
name: Make Bot UI
description: >-
  Use when building a custom UI (page, dashboard, buttons) that should wake a
  Grok Bot over a webhook, when the user must provide a webhook sender key, or
  when exposing that UI on Tailscale.
---
# Make a bot UI

This source skill requires a cloud routine. Cloud use is excluded from the
Codex distribution, and the current native surface has no verified webhook
routine, secret-value card, or wake-event contract. Do not execute the cloud
routine workflow from Codex.

The upstream contract remains available as a fixed reference at
[upstream SKILL.md](https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/make-bot-ui/SKILL.md).

---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

The parent finds its own Codex rollout file before fanning out. Codex stores local sessions as date-partitioned JSONL files under `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Use the current `CODEX_THREAD_ID` exposed to shell commands, then confirm the first `session_meta` record's `payload.id` and `payload.cwd`. Do not scan another workspace's rollouts.

```bash
find "${CODEX_HOME:-$HOME/.codex}/sessions" -type f -name "rollout-*-${CODEX_THREAD_ID}.jsonl"
```

Each rollout line has a top-level `timestamp`, `type`, and `payload`. The session overview is `type: "session_meta"`; conversation text is in `response_item` records whose payload is a `message` with `content` items of type `input_text` or `output_text`. Tool calls appear as `custom_tool_call` or `function_call` response items and identify their paired outputs with `call_id`.

For each candidate, inspect the first `session_meta` record and then the visible `message` content to confirm the opening user prompt. Ignore `reasoning` records and `encrypted_content`; they are not transcript text for this workflow. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

One message, three ordinary `spawn_agent` calls without the poteto-agent body, explicit `model:` on each. Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript). Put each reviewer template in the native spawn message; do not rely on a Cursor agent type or custom-agent metadata.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | your configured reflect-judgment model (default `claude-fable-5-1-thinking-max`) | `references/judgment-reviewer.md` |
| Tooling | your configured reflect-tooling model (default `gpt-5.6-sol-max`) | `references/tooling-reviewer.md` |
| Divergent | your configured reflect-judgment model (default `claude-fable-5-1-thinking-max`) | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the completed subagent response.

### 3. Synthesize

One ordinary `spawn_agent` call without the poteto-agent body, using your configured reflect-judgment model (default `claude-fable-5-1-thinking-max`). The synthesizer's quality check includes spot-verifying citations, which can require MCP access. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. See the [encode-lessons-in-structure](../principle-encode-lessons-in-structure/instructions.md) principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly. Body edits may target a native `SKILL.md`, internal `instructions.md`, or the caller's existing selection instruction in an entry skill, internal instructions file, or playbook:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Codex's `skill-creator` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (a native catalog skill didn't trigger when it should have): hand to Codex's `skill-creator` and run a description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: hand creation to `skill-creator`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched native registered skill before declaring done. Internal instruction files are not registered skills. Skip this step if no validator is available.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.

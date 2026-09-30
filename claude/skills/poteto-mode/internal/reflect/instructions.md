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

The parent finds its own transcript file before fanning out. Use the active workspace's Claude project directory under `~/.claude/projects/<project>/`. Do not glob across sibling project directories. That crosses workspace boundaries and reads private chats from unrelated projects.

```bash
ls -t <claude-project>/*.jsonl <claude-project>/*/subagents/*.jsonl 2>/dev/null | head -10
```

The native layout has session files at `<claude-project>/<session>.jsonl` and subagent files at `<claude-project>/<session>/subagents/<agent>.jsonl`. A session file contains metadata and message records. Find the first record with `type: "user"` and `message.role: "user"`; its `message.content` may be a string or an array of content blocks.

For each candidate, inspect the first opening user record and normalize its `message.content` before checking that it contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

Spawn three reviewers concurrently. Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript).

Each reviewer and the synthesizer name a role line in the pstack model configuration section of the project-root `AGENTS.md` and a default. Use that line's `{model, effort}`, or the default if the line is missing. `auto` and `inherit-parent` mean the parent model and effort. If a configured model is unavailable, use the role's default and say so. If that default is also unavailable, use the closest available model in the same family. If none exists, ask the user to choose an available model.

| Lens | Role line | Default `model` | Prompt template |
|---|---|---|---|
| Judgment | `reflect judgment, divergent, synthesizer` | `claude-opus-5-5-max` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `gpt-5.6-sol-max` | `references/tooling-reviewer.md` |
| Divergent | `reflect judgment, divergent, synthesizer` | `claude-opus-5-5-max` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their reports.

### 3. Synthesize

Spawn one synthesizer subagent using the `reflect judgment, divergent, synthesizer` line (default `claude-opus-5-5-max`). Its quality check includes spot-verifying citations, which can require MCP access. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. See the [encode-lessons-in-structure](../principle-encode-lessons-in-structure/instructions.md) principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly. Body edits may target a native `SKILL.md`, internal `instructions.md`, or the caller's existing selection instruction in an entry skill, internal instructions file, or playbook:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Claude Code's official `skill-creator:skill-creator` plugin skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (a native catalog skill didn't trigger when it should have): hand to Claude Code's official `skill-creator:skill-creator` plugin skill and run its description-optimization loop.
- `new skill via native creator: <kebab-name>`: hand creation to `skill-creator:skill-creator`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched native registered skill before declaring done. Internal instruction files are not registered skills. Skip this step if no validator is available.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.

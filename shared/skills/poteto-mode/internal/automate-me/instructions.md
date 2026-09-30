---
name: automate-me
description: "Use for \"automate me\", \"create/update/refresh my -mode skill\", \"turn/capture my preferences or working style into a skill\", or wanting agents to follow how the user works. Drafts or revises a personal -mode skill via a native skill creator + unslop, optionally pulling fresh evidence from recent transcripts."
---

# Automate me

A guided flow for turning the user's working conventions into a skill agents will follow. The output is one `-mode` skill tailored to them (e.g. `jay-mode`, `priya-mode`).

{{#claude}}
This skill orchestrates three others: an inline mining pass (see step 1), Claude Code's official `skill-creator:skill-creator` plugin skill (authoring), and the [unslop](../unslop/instructions.md) skill (prose discipline). It sequences them. It doesn't replace them.
{{/claude}}
{{#codex}}
This skill orchestrates three others: an inline mining pass (see step 1), Codex's `skill-creator` (authoring), and the [unslop](../unslop/instructions.md) skill (prose discipline). It sequences them. It doesn't replace them.
{{/codex}}

## Flow

### 0. Check for an existing skill

{{#claude}}
Look for `.claude/skills/*-mode/SKILL.md` and `~/.claude/skills/*-mode/SKILL.md` matching the user's handle. Claude Code discovers skills from the direct `skills/<name>/SKILL.md` layout, so do not place a mode under a nested personal category directory. If one exists, confirm intent with `AskUserQuestion` (unless they already said "update my skill" or similar):
{{/claude}}
{{#codex}}
Look recursively for `.agents/skills/**/*-mode/SKILL.md` and `~/.codex/skills/*-mode/SKILL.md` matching the user's handle. Mode skills can live in a personal category directory (`.agents/skills/<handle>/`), not only at the top level. If one exists, confirm intent with the user (unless they already said "update my skill" or similar):
{{/codex}}

- Update the existing skill (default for repeat runs)
- Start fresh (rare, ask why before doing it)

Update mode changes the rest of the flow:
- Step 1 mines only history since the skill was last edited (`git log -1 --format=%cI <path>`).
- Step 2 asks what's changed or missing, not what to capture from zero.
- Step 4 edits the existing file in place. Preserve sections the user hasn't contradicted. Revise ones with new evidence. Add new sections only for genuinely new rules.

### 1. Mine their history

{{#claude}}
Locate the active workspace's transcripts before fanning out. Use only the active Claude project directory under `~/.claude/projects/<project>/`. Don't glob across sibling project directories. That crosses workspace boundaries and reads private chats from unrelated projects.
{{/claude}}
{{#codex}}
Locate the active workspace's Codex rollouts before fanning out. Use only `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` files whose `session_meta.payload.cwd` matches the active workspace. Do not scan another workspace's rollouts. Read visible `response_item` messages and tool calls; ignore `reasoning` and `encrypted_content` records.
{{/codex}}

Survey recent agent conversations within that scope for recurring patterns. Run multiple parallel subagents across slices of history (e.g. last 2-4 weeks, split into 3 slices so each has enough material). Each slice mining subagent reads transcripts from the workspace-scoped path the parent provides, looks for the signals below, and returns a short structured list of patterns it saw with evidence pointers. Default signals worth hunting:

- Response preferences (length, tone, format, "dumb it down" corrections)
- Delegation habits (subagents, models, specialized workflows, parallelism)
- Verification posture (what "done" means, unit tests vs live repro, reviewers)
- Code and prose discipline (style, principles cited, lint/format tools)
- Process conventions (worktrees, commits, PRs, review/merge tooling)
- Meta preferences (fixing skills mid-task, proposing new ones)

Cross-check across slices before elevating a signal. Patterns seen in 2+ slices are high-confidence. Lone signals are weak and usually get dropped.

### 2. Ask the user directly

{{#claude}}
Mining misses intent that hasn't come up yet. Use Claude's native `AskUserQuestion` tool rather than asking the user to type from scratch.
{{/claude}}
{{#codex}}
Mining misses intent that hasn't come up yet. Present numbered category choices in chat rather than asking the user to type from scratch.
{{/codex}}

{{#claude}}
Shape: one or two questions with 4-6 options each. For four options, use `AskUserQuestion`, with `multiSelect: true` for category questions. For five or six, present the question and every numbered option in chat, accepting multiple numbers for category questions, because the native choice schema accepts at most four options. Start broad ("Which areas matter most?"), then follow up on selected areas with specific options. After the structured rounds, one free-form chat question catches anything the options missed.
{{/claude}}
{{#codex}}
Shape: one or two questions with 4-6 options each. For category questions, accept all applicable numbers or category names in the answer. Start broad, then follow up on the categories they pick. Leave a free-form question for anything the choices miss.
{{/codex}}

Don't dump 20 questions.

### 3. Cluster findings

Group the combined signals into sections. Common ones (use only what applies):

- **Response style**: length, tone, format.
- **Autonomy**: how much to do without asking, MCP tool use.
- **Understand first**: which skills to reach for when scoping or investigating a change.
- **Subagents**: default, parallelism, model-to-task, specialized workflows.
- **Prose / code discipline**: principles, lint tools, style guides.
- **Review and verify**: repro posture, verification skills, live-testing tools.
- **Process**: git worktrees, commits, PRs, review/merge tooling.
- **Skills**: skill-authoring habits, fix-the-skill-first, proposing new skills.

The [poteto-mode](../../SKILL.md) skill shows the shape. Read it for granularity. Don't copy its content. The user's rules are not the same as poteto-mode's.

### 4. Draft the skill

{{#claude}}
Use Claude Code's official `skill-creator:skill-creator` plugin skill to author the skill. Placement:
{{/claude}}
{{#codex}}
Use Codex's `skill-creator` skill to author the skill. Placement:
{{/codex}}

{{#claude}}
- Path: preserve an existing mode skill's direct skill directory. For a new mode, use `.claude/skills/<handle>-mode/SKILL.md` in the project (or `~/.claude/skills/<handle>-mode/SKILL.md` if the user prefers a personal skill).
{{/claude}}
{{#codex}}
- Path: preserve an existing mode skill's category. For a new mode, use `.agents/skills/<handle>/<handle>-mode/SKILL.md` when the repo has an established personal category for that handle. Otherwise default to `.agents/skills/<handle>-mode/SKILL.md` in the project (or `~/.codex/skills/<handle>-mode/` if the user prefers a personal skill).
{{/codex}}
- Handle: the user's first name or chosen identifier.
{{#claude}}
- Frontmatter `description`: trigger on their name + `/<handle>-mode` + "work in their style", not on generic keywords like "write code" or "review PR".
{{/claude}}
{{#codex}}
- Frontmatter `description`: trigger on their name + `$<handle>-mode` + "work in their style", not on generic keywords like "write code" or "review PR".
{{/codex}}
{{#claude}}
- Frontmatter formatting: follow `skill-creator:skill-creator`'s YAML rules. Keep `description` as one YAML scalar. Quote it or use `description: >-` with indented continuation lines when punctuation or wrapping requires it.
{{/claude}}
{{#codex}}
- Frontmatter formatting: follow `skill-creator`'s YAML rules. Keep `description` as one YAML scalar. Quote it or use `description: >-` with indented continuation lines when punctuation or wrapping requires it.
{{/codex}}
{{#claude}}
- Frontmatter `disable-model-invocation: true` by default. Opt out only if the user explicitly wants their mode to apply on every turn.
{{/claude}}
{{#codex}}
- In the authored skill's `agents/openai.yaml`, set `policy.allow_implicit_invocation: false` by default. Enable implicit invocation only if the user explicitly wants their mode to apply on every turn.
{{/codex}}

### 5. Iterate on prose

{{#claude}}
Apply the [unslop](../unslop/instructions.md) skill and `skill-creator:skill-creator`'s writing guidelines to every line.
{{/claude}}
{{#codex}}
Apply the [unslop](../unslop/instructions.md) skill and `skill-creator`'s writing guidelines to every line.
{{/codex}}

Show the draft to the user and take feedback. Expect multiple iterations. Cut ruthlessly. A mode skill is not a manual.

### 6. Land it

Work in a worktree off main. Commit and open a PR. Don't push to main directly.

## Guardrails

- **Don't overfit to one conversation.** A preference stated once and contradicted another time is noise. Require multiple instances before codifying it.
- **Don't be clever.** Restating other skills' contents, inventing metaphors, or writing "poetic" prose for an agent reader is cost without benefit. Keep it operational.
- **Reference, don't inline.** Other skills the user relies on should appear as path references, not pasted excerpts. Same for any principle docs they maintain elsewhere.
- **Keep sections minimal.** Only add a section if the user has a specific, non-default rule there. "Communicate clearly" is not a section. "Short paragraphs. Tables when comparing options. Bullets only when items are genuinely parallel." is.
- **Name conventions generic.** Use "the user" or "the human" in imperatives, not the author's first name.
- **Don't force symmetry.** If a user has no process rules worth writing down, skip the Process section entirely.

## Evaluation

A `-mode` skill is subjective output. A skill-creator-style test/iterate benchmark loop isn't useful here. Vibe-check with the user: does it read like them? Did it miss anything? Then ship.

{{#claude}}
Run Claude Code's official `skill-creator:skill-creator` plugin skill description-optimization loop only if the skill's trigger accuracy turns out to be a problem in practice.
{{/claude}}
{{#codex}}
Run a description-optimization loop with `skill-creator` only if the skill's trigger accuracy turns out to be a problem in practice.
{{/codex}}

## When not to use

{{#claude}}
- User wants a task-specific skill (not working conventions): `skill-creator:skill-creator` alone, no mining required.
{{/claude}}
{{#codex}}
- User wants a task-specific skill (not working conventions): `skill-creator` alone, no mining required.
{{/codex}}
- User wants to capture one narrow workflow (e.g. "how I write commit messages"). That's a regular skill, not a mode skill.

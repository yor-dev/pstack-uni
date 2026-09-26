---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Each spawn below names a role line in the pstack model configuration section of `~/.codex/AGENTS.md` and a default. Use the line's model and effort, or the default if the section or line is missing. For `auto` or `inherit-parent`, use the parent model and effort. If `spawn_agent` rejects a configured model, use the default and say so. If it rejects the default, use the closest valid model ID of the same family from its error message; if none exists, ask for a model choice.

## Step 1. Assess Complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. One explainer explores and explains in a single pass. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): spawn parallel explorers first, then hand off to the explainer. Go to Step 2a.

When in doubt, take the simple path.

## Step 2a. Explore (complex questions only)

Decompose the question into 2 to 4 exploration angles, each a distinct slice of the subsystem. Spawn all explorers in a single message:

- Tool: `spawn_agent` without the poteto-agent body
- `model` and `reasoning_effort`: the `how explorer` line, default `grok-4.7-xhigh-fast`

Each explorer gets the prompt in `references/explorer-prompt.md` with its angle filled in. Then go to Step 3.

## Step 2b. Direct Explain (simple questions)

Spawn one subagent with `spawn_agent` that explores and explains in one pass:

- Tool: `spawn_agent` without the poteto-agent body
- `model` and `reasoning_effort`: the `how explainer` line, default `claude-opus-5-5-max`

Build its prompt from `references/explainer-prompt.md` without the explorer-findings section. Go to Step 4.

## Step 3. Synthesize (complex questions only)

Once all explorers have returned, spawn one subagent with `spawn_agent` to synthesize their findings into one explanation:

- Tool: `spawn_agent` without the poteto-agent body
- `model` and `reasoning_effort`: the `how explainer` line, default `claude-opus-5-5-max`

Build its prompt from `references/explainer-prompt.md` with every explorer's findings filled in.

## Step 4. Present

Present the explainer's output to the user. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## Output Format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.

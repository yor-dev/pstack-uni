# pstack-uni

[日本語](README.ja.md)

A port of [pstack](https://github.com/cursor/plugins/tree/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack) for Claude Code and Codex. It runs investigation, design, implementation, and review workflows with local subagents. The upstream version is 0.15.9.

## Installation

### Claude Code

Add the marketplace and install the plugin from within Claude Code.

```text
/plugin marketplace add yor-dev/pstack-uni
/plugin install pstack@pstack-uni
```

To create or improve skills, also install the official `skill-creator` plugin.

```text
/plugin install skill-creator@claude-plugins-official
```

### Codex

Using Node.js and the [skills CLI](https://github.com/vercel-labs/skills), run these commands in your project.

```sh
npx skills add https://github.com/yor-dev/pstack-uni/tree/main/codex/.agents/skills/poteto-mode --agent codex --yes
npx skills add https://github.com/yor-dev/pstack-uni/tree/main/codex/.agents/skills/setup-pstack --agent codex --yes
```

To allow subagents to delegate to their own subagents in CLI V1, merge this setting into your project's `.codex/config.toml`. CLI V2 ignores this setting.

```toml
[agents]
max_depth = 3
```

## Usage

After installation, start your chosen environment and invoke `poteto-mode` followed by your investigation or implementation request. Use `setup-pstack` to choose the model and reasoning effort for each role.

| Action | Claude Code | Codex |
| --- | --- | --- |
| Request investigation or implementation | `/pstack:poteto-mode <request>` | `$poteto-mode <request>` |
| Configure models | `/pstack:setup-pstack` | `$setup-pstack` |

## Limitations

- Execution is local only. Cloud execution, Bot UI routines and webhooks, and timer-based resumption after a turn ends are outside the scope of this port.
- Codex watcher notifications cannot resume a turn that has ended. Steps that depend on this operation are unsupported.
- `setup-pstack` saves model settings in your project's `AGENTS.md` and makes `CLAUDE.md` a relative symlink to it.
- Plan validation requires Node.js. The PR watcher and Orchestrate require Bun. GitHub operations require the GitHub CLI and authentication for the target repository.

## License

This repository is under the [MIT License](LICENSE). Ported pstack files and bundled cursor-team-kit instructions retain their original copyright notices and MIT licenses.

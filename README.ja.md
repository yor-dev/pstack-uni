# pstack-uni

[pstack](https://github.com/cursor/plugins/tree/ecc249f1e306fc64ddf83c7bed16cacf7c2239db/pstack) の Claude Code・Codex 向け移植版です。調査・設計・実装・レビューのワークフローを、ローカルの子エージェントを使って実行します。移植元のバージョンは 0.15.5 です。

## 導入

### Claude Code

Claude Code 内で marketplace を追加し、プラグインをインストールします。

```text
/plugin marketplace add yor-dev/pstack-uni
/plugin install pstack@pstack-uni
```

スキルの作成・改善を行う場合は、公式 `skill-creator` プラグインも導入してください。

```text
/plugin install skill-creator@claude-plugins-official
```

### Codex

Node.js と [skills CLI](https://github.com/vercel-labs/skills) を使い、対象プロジェクトで次を実行します。

```sh
npx skills add https://github.com/yor-dev/pstack-uni/tree/main/codex/.agents/skills/poteto-mode --agent codex --yes
npx skills add https://github.com/yor-dev/pstack-uni/tree/main/codex/.agents/skills/setup-pstack --agent codex --yes
```

CLI V1 で孫エージェントまで委任するには、プロジェクトの `.codex/config.toml` に次を統合してください。CLI V2 ではこの設定は無視されます。

```toml
[agents]
max_depth = 3
```

## 使い方

導入後に利用する環境を起動し、`poteto-mode` に調査・実装したい内容を続けて依頼します。役割ごとのモデルと推論の強さを選ぶ場合は `setup-pstack` を使います。

| 操作 | Claude Code | Codex |
| --- | --- | --- |
| 調査・実装の依頼 | `/pstack:poteto-mode <依頼内容>` | `$poteto-mode <依頼内容>` |
| モデル設定 | `/pstack:setup-pstack` | `$setup-pstack` |

## 利用上の制約

- 実行環境はローカルに限定します。クラウド実行、Bot UI の routine・webhook、定期タイマーによるターン終了後の再開は対象外です。
- Claude Code のエージェントによる goal の設定・取得と、Codex の watcher 通知による終了済みターンの再開は非対応です。これらに依存する手順は実行できません。
- `setup-pstack` は対象プロジェクトの `AGENTS.md` にモデル設定を保存し、`CLAUDE.md` をそこへの相対シンボリックリンクにします。
- 計画の検証には Node.js、PR watcher と Orchestrate には Bun、GitHub 操作には GitHub CLI と対象リポジトリへの認証が必要です。

## ライセンス

このリポジトリは [MIT ライセンス](LICENSE) です。移植した pstack と同梱する cursor-team-kit の指示書には、元の著作権表示と MIT ライセンスを保持しています。

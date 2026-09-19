# pstack-uni

[poteto の pstack](https://github.com/cursor/plugins/tree/e31650eea443aaea1e84cc15d88c13f40080b275/pstack) の Claude Code・Codex 向け移植版です。移植の実装作業は完了しています。実行環境の制約、ユーザー指定の除外範囲、実際に検証した範囲は以下に記載しています。

ユーザー指定により、エージェントの実行環境はローカルに限定します。本家のクラウド worker は各環境のローカル子エージェントへ対応づけます。クラウド専用の routine と、ローカルを含む定期タイマーによるターン終了後の再開は移植対象外です。

## Claude Code

`claude/` がプラグイン本体です。`poteto-mode` を明示起動し、プレイブックと下位スキルの内部ファイルを必要に応じて読みます。下位スキルを個別のコマンドとして登録しません。

リポジトリのルートで、プラグインを検証用のモデル・effort で読み込めます。

```sh
CLAUDE_CODE_ENABLE_TODO_TOOLS=1 claude --plugin-dir ./claude --model claude-opus-5 --effort low --settings '{"env":{"CLAUDE_CODE_EFFORT_LEVEL":"low"}}'
```

入口は `/pstack:poteto-mode` です。検証では、子エージェントにも Claude Opus 5 / low を使う指定を依頼文に渡しています。`--settings` は、既存のユーザー設定に effort の環境変数がある場合も、この起動では low を優先させる指定です。設定ファイルには保存しません。

入口・内部ファイル・子エージェント定義の読み込みと、背景委任を確認しています。通常の対話 CLI では、親→子→孫の起動と、孫の結果を子が集約して親へ返す流れも確認しました。非対話 `--print` では、子が先に終了すると孫の結果が親へ直接届きます。設定保存と Comment Sicko によるコメント編集も実行しました。スキル作成では、入口から公式 `skill-creator`、実装の委任、生成スキルの利用試験まで実行しました。調査では、本文が届いた後にモデルが手順を省略する実行がありました。この観測だけで移植コードの欠陥とは断定していません。コンパクション後の入口の再添付は確認できましたが、末尾が切り詰められました。

役割別の model と effort は、Claude のモデル指定と effort ごとのネイティブエージェント定義へ翻訳しました。履歴の保存先・形式を Claude 用に変更し、依存する `deslop`・`control-cli`・`control-ui` は本家のファイルを内部に同梱しています。動的 `/loop` の監視には native `Monitor` を使い、イベント受信後に応答が再開することを実行確認しました。

スキルの作成・改善には公式 `skill-creator` プラグインを使います。未導入の環境では Claude Code で `/plugin install skill-creator@claude-plugins-official` を実行します。[公式の導入手順](https://code.claude.com/docs/en/discover-plugins#install-plugins)。この作業では常用環境へインストールしていません。

## Codex

`codex/.agents/` を対象プロジェクトの `.agents/` として配置する構成です。入口は `$poteto-mode` 一つで、下位スキルとエージェント本文は内部ファイルです。自動起動は無効にしています。

CLI V1 では、本家の深さ3の委任に合わせて `.codex/config.toml` の `[agents]` に `max_depth = 3` を設定します。同梱の `codex/.codex/config.toml` はこの設定だけを持ちます。既存設定がある場合は、このキーを統合してください。V2 ではこのキーは無視されます。

GPT-5.6 Luna / xhigh で、入口から Investigation・how・説明担当への委任、設定保存、Comment Sicko によるコメント編集、native goal の作成・取得・達成終了を確認しています。スキル作成では、入口から native `skill-creator`、設計・実装・検証の委任を経て、実行可能な成果物を作成しました。履歴処理は Codex の rollout 形式へ変更し、Claude 版と同じ3つの依存指示書を同梱しています。

## 対応範囲

同梱スクリプトを使う経路には Node.js（計画の検証）、Bun（PR watcher と Orchestrate）、GitHub CLI と対象リポジトリへの認証が必要です。これは各ワークフローを使う際の依存です。

| 操作 | Claude Code | Codex |
| --- | --- | --- |
| 明示起動、内部ファイル読込、ローカル委任 | 実行確認済み | 実行確認済み |
| native creator を使うスキル作成 | 成果物の作成・利用を実行確認 | 成果物の作成・動作を実行確認 |
| 履歴、設定保存、コメント編集 | 形式を翻訳。保存・編集を実行確認 | 形式を翻訳。保存・編集を実行確認 |
| goal の作成・取得 | ユーザーの `/goal` は存在。agent の `Skill(goal)` は UI コマンドとして拒否されることを実測。取得ツールも未発見 | native goal ツールで実行確認済み |
| watcher 出力での再開 | `Monitor` で実行確認済み | ターン終了後の再開は未対応 |
| 定期タイマーによるターン終了後の再開 | ユーザー指定で対象外 | ユーザー指定で対象外 |
| クラウド実行・クラウド専用の定期起動 | ユーザー指定で対象外 | ユーザー指定で対象外 |
| Bot UI の routine・webhook | クラウドを必要とするため対象外 | クラウドを必要とするため対象外 |

Claude の agent 自身による goal 操作と、Codex の watcher 通知による終了済みターンの再開は、確認した実行環境では利用できません。これらを追加実装待ちの項目として扱わず、依存する本家の操作は非対応と明記します。コンパクション後の全文保持は移植の完成条件に含めず、各環境の標準のコンテキスト管理に従います。具体的な翻訳・実行条件・制約は [Claude Code への翻訳](docs/claude-code-translation.md) と [Codex への翻訳](docs/codex-translation.md) に記載しています。対象外のクラウド機能と定期タイマーによる再開は、今後の実装・検証項目に含めません。

Opus 5 / low と GPT-5.6 Luna / xhigh は検証時だけの指定です。両版の配布ファイルは本家の役割別モデル選択を維持します。常用環境へのインストールやユーザー設定の保存は行っていません。

本家は pstack v0.15.2、コミット `e31650eea443aaea1e84cc15d88c13f40080b275` を基準としています。移植したファイルのライセンスは [MIT](claude/LICENSE) です。

## 本家の更新への対応

[固定元と全ファイルの対応表](maintenance/upstream.json)、[Claude の完全パッチ](maintenance/patches/claude.patch)、[Codex の完全パッチ](maintenance/patches/codex.patch) を保存しています。[差分の意味](docs/upstream-differences.md) と [更新手順・検証方法](docs/updating-upstream.md) を合わせて参照してください。

`tools/upstream.py` は、保存パッチからの復元検証と、新旧本家・現行移植版の三者比較を行います。新規・削除・競合を報告し、更新候補を別ディレクトリへ出力します。配布版への反映は翻訳内容をレビューして行います。

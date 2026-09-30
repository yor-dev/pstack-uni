# pstack-uni

[poteto の pstack 0.15.5](https://github.com/cursor/plugins/tree/ecc249f1e306fc64ddf83c7bed16cacf7c2239db/pstack) の Claude Code・Codex 向け移植版です。保守上の基点は `ecc249f1e306fc64ddf83c7bed16cacf7c2239db` です。実行環境の制約、ユーザー指定の除外範囲、実際に検証した範囲は以下に記載しています。

ユーザー指定により、エージェントの実行環境はローカルに限定します。本家のクラウド worker は各環境のローカル子エージェントへ対応づけます。クラウド専用の routine と、ローカルを含む定期タイマーによるターン終了後の再開は移植対象外です。

## Claude Code

`claude/` がプラグイン本体です。`poteto-mode` とモデル設定用の `setup-pstack` を登録します。その他の45スキルは `poteto-mode` の内部ファイルとして必要に応じて読みます。

Claude Code 内で marketplace を追加し、プラグインをインストールします。このリポジトリは非公開なので、アクセス権のある Git 認証が必要です。

```text
/plugin marketplace add yor-dev/pstack-uni
/plugin install pstack@pstack-uni
```

導入後は `/pstack:poteto-mode 調査したいことや実装したいこと` と依頼します。役割別モデルの設定には `/pstack:setup-pstack` を使います。Claude Code 版はスキルとネイティブエージェント定義を一緒に導入するため、marketplace を使います。`npx skills add` でスキルだけを入れても、プラグイン全体の導入にはなりません。[marketplace の公式説明](https://code.claude.com/docs/en/plugin-marketplaces)。

開発時はリポジトリのルートで、プラグインを検証用のモデル・effort で直接読み込めます。

```sh
CLAUDE_CODE_ENABLE_TODO_TOOLS=1 claude --plugin-dir ./claude --model claude-opus-5 --effort low --settings '{"env":{"CLAUDE_CODE_EFFORT_LEVEL":"low"}}'
```

ワークフローの入口は `/pstack:poteto-mode` です。検証では、子エージェントにも Claude Opus 5 / low を使う指定を依頼文に渡しています。`--settings` は、既存のユーザー設定に effort の環境変数がある場合も、この起動では low を優先させる指定です。設定ファイルには保存しません。

入口・内部ファイル・子エージェント定義の読み込みと、背景委任を確認しています。通常の対話 CLI では、親→子→孫の起動と、孫の結果を子が集約して親へ返す流れも確認しました。非対話 `--print` では、子が先に終了すると孫の結果が親へ直接届きます。設定保存と Comment Sicko によるコメント編集も実行しました。スキル作成では、入口から公式 `skill-creator`、実装の委任、生成スキルの利用試験まで実行しました。調査では、本文が届いた後にモデルが手順を省略する実行がありました。この観測だけで移植コードの欠陥とは断定していません。コンパクション後の入口の再添付は確認できましたが、末尾が切り詰められました。

役割別の model と effort は、Claude のモデル指定と effort ごとのネイティブエージェント定義へ翻訳しました。履歴の保存先・形式を Claude 用に変更し、依存する `deslop`・`control-cli`・`control-ui` は本家のファイルを内部に同梱しています。動的 `/loop` の監視には native `Monitor` を使い、イベント受信後に応答が再開することを実行確認しました。

スキルの作成・改善には公式 `skill-creator` プラグインを使います。未導入の環境では Claude Code で `/plugin install skill-creator@claude-plugins-official` を実行します。[公式の導入手順](https://code.claude.com/docs/en/discover-plugins#install-plugins)。この作業では常用環境へインストールしていません。

## Codex

対象プロジェクトで次を実行します。Codex 版のパスを明示し、Claude Code 版と取り違えないようにします。非公開リポジトリへの Git 認証と、[skills CLI](https://github.com/vercel-labs/skills) が対応する Node.js が必要です。検証した skills 1.7.0 は Node.js 22.20.0 以降を要求します。

```sh
npx skills add https://github.com/yor-dev/pstack-uni/tree/main/codex/.agents/skills/poteto-mode --agent codex --yes
npx skills add https://github.com/yor-dev/pstack-uni/tree/main/codex/.agents/skills/setup-pstack --agent codex --yes
```

プロジェクトの `.agents/skills/poteto-mode/` と `.agents/skills/setup-pstack/` へ導入されます。clone 済みなら URL の代わりに、それぞれのローカルディレクトリを指定できます。その他の45スキル・エージェント本文・参照資料・スクリプトは `poteto-mode` に同梱します。`poteto-mode` の自動起動は無効です。導入後に Codex を起動し、作業には `$poteto-mode 調査したいことや実装したいこと`、モデル設定には `$setup-pstack` を使います。

両版の `setup-pstack` は対象プロジェクト直下の `AGENTS.md` に共通の役割別モデル設定区画を書きます。同じ場所の `CLAUDE.md` は `AGENTS.md` を指す相対シンボリックリンクにします。設定値は `{model, effort}` です。保存したモデル指定をもう一方の環境が受け付けない場合は、その環境でモデルを選び直す必要があります。

旧版が保存した役割行は、0.15.2当時の既定モデルを固定している場合があります。0.15.5の既定値を使うには、旧 `~/.claude/rules/pstack-models.md` の pstack 役割行を削除し（pstack 専用ならファイルごと削除可）、旧 `~/.codex/AGENTS.md` では pstack 区画だけを削除して、対象プロジェクトで `setup-pstack` を再実行します。両方ある場合は両方を整理し、他の指示は残してください。旧設定で個別に選んだモデルを使い続ける場合は、再実行時に選び直します。

CLI V1 では、本家の深さ3の委任に合わせて `.codex/config.toml` の `[agents]` に `max_depth = 3` を設定します。同梱の `codex/.codex/config.toml` はこの設定だけを持ちます。既存設定がある場合は、このキーを統合してください。V2 ではこのキーは無視されます。

`npx skills add` は `.codex/config.toml` を設定しないため、CLI V1 では次の値を別途統合します。

```toml
[agents]
max_depth = 3
```

GPT-5.6 Luna / xhigh で、入口から Investigation・how・説明担当への委任、設定保存、Comment Sicko によるコメント編集、native goal の作成・取得・達成終了を確認しています。スキル作成では、入口から native `skill-creator`、設計・実装・検証の委任を経て、実行可能な成果物を作成しました。履歴処理は Codex の rollout 形式へ変更し、Claude 版と同じ3つの依存指示書を同梱しています。

## 対応範囲

同梱スクリプトを使う経路には Node.js（計画の検証）、Bun（PR watcher と Orchestrate）、GitHub CLI と対象リポジトリへの認証が必要です。これは各ワークフローを使う際の依存です。

| 操作 | Claude Code | Codex |
| --- | --- | --- |
| 明示起動、内部ファイル読込、ローカル委任 | 実行確認済み | 実行確認済み |
| `setup-pstack` の独立登録・起動 | プラグイン検証済み。新しいプロジェクト保存先とリンク作成は未検証 | 一時導入と予算表示を確認。新しいプロジェクト保存先とリンク作成は未検証 |
| native creator を使うスキル作成 | 成果物の作成・利用を実行確認 | 成果物の作成・動作を実行確認 |
| 履歴、設定保存、コメント編集 | 形式を翻訳。一時ファイルへの保存とコメント編集を実行確認 | 形式を翻訳。一時ファイルへの保存とコメント編集を実行確認 |
| goal の作成・取得 | ユーザーの `/goal` は存在。agent の `Skill(goal)` は UI コマンドとして拒否されることを実測。取得ツールも未発見 | native goal ツールで実行確認済み |
| watcher 出力での再開 | `Monitor` で実行確認済み | ターン終了後の再開は未対応 |
| 定期タイマーによるターン終了後の再開 | ユーザー指定で対象外 | ユーザー指定で対象外 |
| クラウド実行・クラウド専用の定期起動 | ユーザー指定で対象外 | ユーザー指定で対象外 |
| Bot UI の routine・webhook | クラウドを必要とするため対象外 | クラウドを必要とするため対象外 |

Claude の agent 自身による goal 操作と、Codex の watcher 通知による終了済みターンの再開は、確認した実行環境では利用できません。これらを追加実装待ちの項目として扱わず、依存する本家の操作は非対応と明記します。コンパクション後の全文保持は移植の完成条件に含めず、各環境の標準のコンテキスト管理に従います。具体的な翻訳・実行条件・制約は [Claude Code への翻訳](docs/claude-code-translation.md) と [Codex への翻訳](docs/codex-translation.md) に記載しています。対象外のクラウド機能と定期タイマーによる再開は、今後の実装・検証項目に含めません。

Opus 5 / low と GPT-5.6 Luna / xhigh は検証時だけの指定です。両版の役割別モデル選択は本家 0.15.5 に合わせています。常用環境へのインストールやユーザー設定の保存は行っていません。

全ファイルの比較基点は pstack 0.15.5 です。Autopilot の code-ready head と各 patch 変更後の検証ラウンドを含む本家の更新を反映しています。移植したファイルのライセンスは [MIT](claude/LICENSE) です。

## 本家の更新への対応

[shared/skills](shared/skills) を両版のスキル本文の共通原本とします。環境固有の記述は `{{#claude}}...{{/claude}}` と `{{#codex}}...{{/codex}}` に分け、片方にしかないファイルと Claude のエージェント定義テンプレートは [shared/clients](shared/clients) に置きます。`python3 tools/generate.py` で `claude/`・`codex/` の配布ファイルと Claude の effort 別エージェント定義17件を生成します。`python3 tools/generate.py --check` は生成結果と配布ファイルの一致を確認します。

[固定元と全ファイルの対応表](maintenance/upstream.json)、[Claude の移植パッチ](maintenance/patches/claude.patch)、[Codex の移植パッチ](maintenance/patches/codex.patch) を保存しています。配布バージョンは [plugin.json](claude/.claude-plugin/plugin.json) のみで管理します。[差分の意味](docs/upstream-differences.md) と [更新手順・検証方法](docs/updating-upstream.md) を合わせて参照してください。

`tools/upstream.py` の `refresh`・`check`・`compare` は生成結果の一致を事前に確認し、保存パッチからの復元検証と、新旧本家・現行移植版の三者比較を行います。新規・削除・競合を報告し、更新候補を別ディレクトリへ出力します。配布版への反映は翻訳内容をレビューして共通原本を更新します。

# Codex への翻訳

本家 pstack v0.15.5、`cursor/plugins@ecc249f1e306fc64ddf83c7bed16cacf7c2239db` を基準とする。2026-09-28 更新。以下の実行記録は、それぞれの実施時点の移植版で入口・委任・設定保存・コメント編集などを検証した結果であり、0.15.5 更新後の全手順の実行試験を意味しない。実行環境の制約と未検証の範囲も記録する。

ユーザー指定により、クラウドは使用しない。本家のクラウド worker はローカルの `spawn_agent` に対応づける。担当の人数・役割・モデル選択・結果集約は維持する。クラウド専用の定期起動、routine、クラウドセッションの継続・回収は対象外とし、未完了の開発項目には数えない。

2026-09-20 のユーザー指定により、ローカルを含む定期タイマーによるターン終了後の再開も対象外とする。Autopilot の30分ごとの起動と計画テンプレートの定期起動手順、Orchestrate と Autonomous run の予備 heartbeat を削除した。監査内容は残し、別の自動起動条件は追加しない。`check-plan.mjs` も30分の定期処理を必須にしない。子の完了通知や watcher の出力イベントとは別の除外指定である。 定期起動を含まない両版の計画テンプレートは検証を通り、goal 作成を除いた計画は該当項目で失敗した。記録は `tmp/experiments/no-timed-resume/`。

## 配置と明示起動

`codex/.agents/` を対象プロジェクトの `.agents/` として配置するプロジェクト用の構成。CLI V1 では `.codex/config.toml` の `[agents]` に `max_depth = 3` を設定する。同梱の `codex/.codex/config.toml` はその設定だけを持つ。既存のプロジェクト設定がある場合は、このキーを統合し、ファイル全体を上書きしない。常用環境にはインストールしていない。

```text
codex/
  LICENSE
  .codex/config.toml
  .agents/skills/poteto-mode/
    SKILL.md
    agents/openai.yaml
    playbooks/
    references/
    scripts/
    internal/
      how/instructions.md
      why/instructions.md
      unslop/instructions.md
      principle-*/instructions.md
      agents/poteto-agent.md
      agents/comment-sicko.md
      ...
  .agents/skills/setup-pstack/
    SKILL.md
    LICENSE
```

公開スキルは `poteto-mode` と `setup-pstack`。その他45個の下位スキルは通常の内部ファイルとして配置し、元の参照資料とスクリプトも保持する。`poteto-mode` は `agents/openai.yaml` の `allow_implicit_invocation: false` で明示起動専用にし、入口を `$poteto-mode` とする。モデル設定は `$setup-pstack` から起動する。[公式のスキル登録と呼び出しポリシー](https://developers.openai.com/ja-JP/docs/build-skills)。`mode`、`icon`、`color` は Codex の同名機能として扱わない。`reminder` と `readonly` の権限制限はユーザー指定で対象外。本文にある調査の作業範囲は保持する。

## 委任の対応

| 本家の操作 | Codex の操作 | 残る制約 |
| --- | --- | --- |
| `Task`、背景実行 | `spawn_agent` による非同期の子起動と完了待機 | ユーザー指定によりローカル実行に限定。 |
| `generalPurpose` | poteto-agent 本文を付けない通常の `spawn_agent` | how の人数・複雑度分岐・テンプレートは維持。 |
| `poteto-agent`、`comment-sicko` | 内部のエージェント定義を読み、その本文を子への `message` に渡す | ネイティブ custom agent と同じ指示優先度になるとは主張しない。既存の子を再開する description は親が読むファイル内に保持するが、native metadata による自動ルーティングはない。 |
| モデル名に含まれる effort | `model` と `reasoning_effort` の別引数 | 実行可能なモデルは現在のツールで確認する。 |
| `inherit-parent` / `auto` | 親のモデルと effort を明示して子へ渡す | Codex の別途設定された子の既定値に変わることを避け、元の意味を保持する。 |
| why の MCP 発見 | 利用可能ツール・リソース記述と、公開されていればツール検索 | 実サービスを使った why 全体は未検証。 |

公式ドキュメントには `.codex/agents/*.toml` のカスタムエージェントがある。[公式仕様](https://developers.openai.com/ja-JP/docs/agent-configuration/subagents)。一方、実機の Codex CLI 0.155.0 では `spawn_agent` に `agent_type` が公開されていなかった。TOML を置いた試験でも、その定義を選んで子へ渡すことは確認できなかった。製品に動かない種別名を指定せず、既存のエージェント本文を依頼に渡す操作へ翻訳した。新しい行動規範、実行ラッパー、起動フックは作成していない。

実行時 API の質問結果は `tmp/experiments/codex-translation/runtime/schema.jsonl`。CLI の V1 ツールは `message`、`items`、`model`、`reasoning_effort`、`fork_context` を示した。アプリの V2 では `fork_turns` などに違いがある。製品の実行試験は V1 で行った。現在のスキル本文は独立した子コンテキストを求め、具体的な引数名は指定しない。

本家の orchestrate が示す深さ3の委任に対し、CLI V1 は `[agents] max_depth = 3` を使う。[公式設定 schema](https://developers.openai.com/codex/config-schema.json) にあるネイティブ設定で、V2 では無視される。モデルや権限制限はこのファイルに設定しない。試験ではプロジェクト設定の自動読込と切り離して `-c agents.max_depth=3` を渡し、同じ値での実行を確認する。

## 役割別モデル

本家の Grok・GPT・Claude の役割表、パネル人数、予算ラベルを保持する。検証時だけ親子を GPT-5.6 Luna / xhigh に指定する。利用できない本家モデルをすべて Luna に置換する設定は作らない。

setup は、本家モデルの選択を利用可能な同じモデルの ID と effort に対応づける。`unlimited` は各役割の effort を維持する。保存する値は共通形式の `{"model": "...", "effort": "..."}` とし、親を使う指定は元の二つの別名のままとする。設定は対象プロジェクト直下の `AGENTS.md` の共通区画へ保存し、他の指示を保持する。同じ場所の `CLAUDE.md` は `AGENTS.md` への相対シンボリックリンクにする。新しい保存先とリンク作成を含む setup の対話全体は未検証。

2026-09-27 に一時ディレクトリへ2スキルを導入し、Codex CLI の読み取り専用実行で `$setup-pstack` が4つの予算選択肢を返すことを確認した。設定ファイルへの保存は試験していない。

この環境で公開された子のモデル一覧は OpenAI のモデルであり、本家の Grok や Claude を呼び出せる根拠はない。モデル選択を定義として保持したことと、全既定値を実行できることは別である。`interrogate` のモデル拒否時の代替選択は本家にもある手順であり、移植側で新設した処理ではない。

## 実行環境の制約

以下を Codex 対応済みとは扱わない。実行環境の機能差として記録し、追加実装待ちの項目にはしない。

- watcher の出力イベントで終了済みのターンを再開する経路。CLI の待機だけでは同じ機能にならない。定期タイマーによる再開はユーザー指定で対象外。
- Cursor mode 固有の有効期間・解除操作との同等性。

コンパクション後の全文保持は移植の完成条件に含めない。明示起動後のコンテキスト管理は Codex の標準機能に従う。全文保持を未完了項目にした以前の判断は撤回し、そのための追加試験・保持機構は作らない。

`make-bot-ui` はクラウド routine を必要とするため対象外。以前調べた `codex cloud exec` と Cloud API による対応案は採用しない。ローカルの独自サービスで routine を代替する実装も追加しない。

Cursor の実行環境はない。本家ファイルの要求と、Codex 上の観測結果を比較する。元の機能がない箇所を名前だけ置換して同等と扱わない。

## goal と質問 UI

Autopilot-full、Autopilot-stack、Multi-phase plan の goal 作成を `create_goal`、再読を `get_goal` へ翻訳した。`tmp/experiments/native-runtime/codex/evidence.json` に、実際の作成・取得、一時ファイルの書込と読取、`update_goal(status="complete")` の成功を保存した。実行モデルは GPT-5.6 Luna / xhigh。定期タイマーの除外で goal 操作は変更しない。

同梱 `check-plan.mjs` の goal 必須項目も `create_goal` に対応させた。翻訳後の計画テンプレートが通り、goal 作成を欠く計画はその項目だけで失敗することを Node.js 25.1.0 で確認した。記録は `tmp/experiments/native-runtime/plan-validator/`。

実行パスは配布先の `.agents/skills/poteto-mode/` に合わせた。一時プロジェクトへコピーし、プロジェクトルートから計画検証が動くことも確認した。Orchestrate の store は既存の `ORCH_STORE` で `orchestrate/<project-slug>/` を指定する。Codex のシステムプロンプトに Cursor の store path があるとは仮定しない。

`automate-me` はチャットに4〜6候補を番号付きで示し、複数の番号・カテゴリ名を受け取る。CLI とアプリの質問ツールの違いに依存せず、元の1〜2質問、複数カテゴリ選択、選択後の掘り下げを保持する。チェックボックスによる複数選択 UI の再現ではない。setup の4つの予算候補も元のラベルをそのまま提示する。

CLI 0.155.0 と同じ [release tag の完了通知実装](https://github.com/openai/codex/blob/rust-v0.155.0/codex-rs/core/src/agent/control.rs) では、子の完了は V1 で `inject_fragment_without_turn`、V2 で `trigger_turn: false` を使う。子を sleep させて終了させても、終了済みの親ターンを起こす定期実行の代わりにはならない。この方式の代替実装は追加していない。

## 履歴と依存指示書

`recall`、`reflect`、`automate-me`、session pickup、eval、判断記録、worktree 監査を Codex の JSONL rollout 形式へ変更した。`session_meta.payload.cwd` で対象 workspace を限定し、公開されたメッセージ・ツール記録を読む。現在の履歴は `CODEX_THREAD_ID` と `session_meta.payload.id` で対応づける。子のシェル環境にも自身の thread ID が渡ることを確認した。

worktree 監査では、一致する記録の後に無関係な行があっても検出すること、似た名前の worktree・別 workspace・非公開の reasoning 記録を一致と扱わないことを fixture で検証した。履歴を利用する各ワークフロー全体の実行試験ではない。

`cursor-team-kit` の `deslop`・`control-cli`・`control-ui` は、同じ固定コミットの原本を `internal/dependencies/cursor-team-kit/` に MIT ライセンスとともに同梱した。各プレイブックは必要時にそのファイルを読む。別の指示書への代替ではない。ブラウザや CLI ハーネスの実行環境は、対象プロジェクトに必要。

スキル作成は Codex の `skill-creator` を参照する。`automate-me` と `reflect` が要求する description の改善ループは保持する。native skill-creator は description の識別力を確認し、実利用や実証された失敗を基に改善する手順を持つ。同名の専用スクリプトがないことは、この作業を実行できない根拠にはならない。移植側で試験回数や合格条件を足していない。

## 設定保存とコメント編集の実行結果

`tmp/experiments/completion/` に依頼文・起動引数・実行ログ・結果ファイルを保存した。両試験の親子は、保存済み `turn_context` で GPT-5.6 Luna / xhigh を確認した。

- `codex-setup`：検証用として確認済みのモデル値を渡し、17役割と各パネル4人の設定を一時ファイルへ保存した。既存の本文を保持し、pstack の区画は一つ。自然な質問応答によるモデル選択やグローバル設定の自動読込までは試していない。
- `codex-comments`：内部 Comment Sicko の本文を読んで子へ委任し、冗長な説明コメントを削除した。著作権・ライセンスコメントと関数の動作は保持した。

常用環境の設定は変更していない。検証用モデルを配布版の既定値にもしていない。

## 検証

### スキル作成の一連の実行

`tmp/experiments/end-to-end/codex-authoring/` で、`$poteto-mode` から CSV を JSON に変換するスキルを作成した。入口、Authoring プレイブック、native `skill-creator`、内部の設計指示を読み、設計・実装・検証を委任して成果物を作成した。親と子孫の計7タスク、8個の `turn_context` はすべて GPT-5.6 Luna / xhigh。記録は `runtime-evidence.json`。

初回は試験に指定した `workspace-write` が `.agents` への書込を拒否した。また「検証時だけ」という試験依頼の表現を、実装時の委任禁止と解釈した。これらは移植の不具合に数えない。同じタスクを一時プロジェクトの作業として再開し、試験用の sandbox 設定と「今回の全作業・全役割が指定モデルによる検証」という依頼を訂正した。製品のスキル本文に追従を強める指示は追加していない。初回の実行条件は `command.json`、訂正後は `resume-command.json` に保存した。

生成物を別途実行し、引用されたカンマ、引用符、空文字、先頭ゼロの保持と、重複ヘッダーの非ゼロ終了・JSON 出力なしを確認した。生成物の標準ライブラリによるテスト6件も成功した。native validator は試験プロセスの Python に `yaml` がなく失敗したため、こちらで `uv run --with pyyaml` を使って実行し、成功を確認した。根拠は `independent-verification.json` と `resume.jsonl`。これは試験条件を訂正した後の成功であり、初回から無条件に完走したという意味ではない。

### 初期の読み込み・委任試験

移植した `poteto-mode` に対する `skill-creator` の `quick_validate.py` は成功。これは登録メタデータの検証であり、手順の実行成功ではない。

実行試験は `tmp/experiments/codex-translation/` 以下。プロジェクトを分けた `explicit` と `ordinary` で同じ6行の関数を質問し、`agent-body` ではエージェント本文を子へ渡す操作を確認する。CLI の成功終了と、本家の手順に従ったかを別々に判定する。

`ordinary` は pstack の内部ファイルを読まず、直接回答した。`explicit` は入口、Investigation、how、explainer のテンプレート、unslop を読み、説明担当を一人起動して完了を待った。親はテンプレートより短い依頼文を組み立てたが、質問・調査対象・確認する動作・回答構成は渡している。テンプレートは質問に応じた調整を認めており、短さだけを理由にした「独自要約による不合格」の判定は撤回する。今回の短縮が必要な意味を損なったとは確認していない。todo を作らなかったことは別の観測であり、これだけで移植の欠陥とは判定しない。

同じセッションを再開して理由を質問した。エージェントは、原文転記を省略し、短い依頼文を自作したと回答した。この自己評価だけで移植の不具合とは断定しない。テンプレートを読まなかったという当初の見立ても誤りで、元の実行ログに取得コマンドと全文出力がある。質問記録は `explicit/question.jsonl`。この後追いの確認を初回試験の成功には含めない。

初回試験は CLI 0.155.0 の非対話 `codex exec`、Luna / xhigh、`--ignore-user-config`、`workspace-write`、承認要求なし、ネットワーク制限ありで実行した。6行の関数と移植版 `.agents/` を置いた一時 Git プロジェクトを使用したが、保存ログには既存の AGENTS.md 指示とユーザースキル一覧も含まれる。pstack だけの隔離環境ではない。ユーザー入力は `$poteto-mode` に続く関数の挙動の質問と検証時モデル指定で、入口本文は CLI が添付した。`max_depth=3` はこの初回試験では未指定。

初回試験後、how/why のモデル指定欄で `model` と `reasoning_effort` の両方を明記し、how のテンプレート内の Read/Grep/Glob というツール名をシェルでの読込・検索・列挙へ翻訳した。これらを手順省略の修正とは扱わない。

`explicit` の実 spawn 引数は `fork_context: true` だった。初稿の「独立した子コンテキスト」という指定と異なり、親の履歴も継承している。監査では子固有の `turn_id` と実行開始位置で親の履歴を除外し、子自身も入口・Investigation・how・unslop・テンプレートを新たに読んだことを確認した。初回試験後は native fork 引数を本文に明記したが、現在は引数名を外し、独立した子コンテキストという要件だけを残す。

`agent-body` の実 spawn は `fork_context: false`、`model: gpt-5.6-luna`、`reasoning_effort: xhigh`。親が渡した定義の本文と、子が受け取った本文を確認した。子は入口138行を実際に読んだ。一方、how を読んだ後の説明担当の起動は省略しており、本文の受け渡しの成功をワークフロー全体の成功には扱わない。親子のモデル・effort は子の自己申告ではなく、保存済み `turn_context` でも確認する。

この子を再開して理由を聞くと、利用可能ツールを検索しても `spawn_agent` が見つからず、起動不能と判断したと説明した。初回実行ログにも `ALL_TOOLS` の検索と結果 `[]` があり、実際の spawn 呼び出しや拒否はない。`nested-depth` は `--strict-config -c agents.max_depth=3` で親→子→孫を各一人起動する設定の試験で、`NESTED_OK` の完了が返った。親と子の実 spawn、および各階層固有の `turn_context` で Luna / xhigh を確認した。設定をユーザー共通ファイルへ保存していない。

製品のエージェント本文を使う `agent-body-depth3` でも、子が孫を起動して回答を返した。ただし、この試験では親が検証依頼を展開する際に、孫の起動を子の依頼文へ明示した。製品本文への追加ではないが、この結果を入口だけから自然に how の委任へ進んだ証拠にはしない。確認対象は、実際の本文を渡した子からさらに委任できることまで。

この試験も親・子・孫それぞれの `turn_context` が Luna / xhigh で、二段階の実 spawn はいずれも `fork_context: false` だった。監査記録は `tmp/experiments/codex-translation/evidence.json`。後追いの質問ターンを初回試験の判定に含めていない。

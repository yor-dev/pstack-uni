# 本家との差分監査

2026-09-20。比較対象は `cursor/plugins` のコミット `e31650eea443aaea1e84cc15d88c13f40080b275` にある pstack 0.15.2 と、このリポジトリの `claude/`・`codex/`。本家の最新版との比較ではない。本家チェックアウトの HEAD を確認し、配置変更を対応づけてファイルを比較した。

意図した移植差分に加え、一般名詞の誤置換、内部ファイル化の反映漏れ、除外理由の誤記が見つかった。直前の「実装完了」という断言には、これらを見落とした問題がある。下記3種類の不備は監査後に両版の該当箇所を修正した。

## 読み込みと実行の差分

| 項目 | 本家 | Claude Code 版 | Codex 版 |
| --- | --- | --- | --- |
| 公開するスキル | `skills/` の47スキル。下位スキルも個別に明示起動可能 | 公開は `/pstack:poteto-mode` 一つ。下位46個は `internal/<name>/instructions.md` | 公開は `$poteto-mode` 一つ。下位46個は同じ内部ファイル構成 |
| 内部化の意味 | 下位スキルをネイティブスキルとして呼ぶ | 内部ファイルを読み、その指示を適用する。個別のネイティブコマンドとしては登録しない | 同左 |
| 登録設定 | `disable-model-invocation`、`mode`、`reminder`、`icon`、`color` | 入口の明示起動フラグを保持。`mode/icon/color` は除去。`reminder` はユーザー指定で除外 | `agents/openai.yaml` の `allow_implicit_invocation: false`。`mode/icon/color` は移さず、`reminder` は除外 |
| 委任 | `Task`、`generalPurpose`、`poteto-agent`、Comment Sicko | native `Agent` と `pstack:` 名前空間。`is_background` を `background` へ変更 | native `spawn_agent`。エージェント本文を内部ファイルから読み、子の `message` に渡す |
| 指示の優先度 | ネイティブエージェント定義 | ネイティブエージェント定義を使う。本文なしの custom general-purpose と組み込み general-purpose の同一性は未実証 | エージェント本文を依頼メッセージで渡すため、ネイティブ定義と同じ指示優先度とは主張しない |
| 独立した子の文脈 | Cursor の subagent 実行 | Claude の標準 subagent 実行 | V1 は `fork_context: false`、V2 は `fork_turns: "none"` |
| 委任の深さ | Orchestrate は coordinator→track→worker | 通常の対話 CLI で親→子→孫、子での集約を実行確認。非対話では子が先に終了すると孫の結果は親へ直接届く | V1 向けに `[agents] max_depth = 3` を同梱。V2 ではこのキーは無視される |
| モデル・effort | Cursor のモデル名に effort を含む。役割別モデル・パネルを指定 | `{model, effort}` に分離。3系統×5 effort の native agent 定義を追加 | `{model, reasoning_effort}` に分離 |
| モデル設定の保存先 | `~/.cursor/rules/pstack-models.mdc` | `~/.claude/rules/pstack-models.md` | `~/.codex/AGENTS.md` の pstack 専用区画 |
| 質問 | `AskQuestion` | `AskUserQuestion`。4候補はツール、5〜6候補は番号付きチャット。カテゴリの複数選択条件を維持 | `automate-me` は4〜6候補を番号付きチャットで提示。setup は利用可能な質問ツールまたはチャット |
| 履歴 | Cursor の transcript 配置・形式 | `~/.claude/projects/`、親子の JSONL、文字列・content block の両形式 | `~/.codex/sessions/` の rollout。session ID、cwd、可視メッセージ・ツール入力を参照 |
| MCP 発見 | Cursor の `mcps/` 等 | 利用可能ツールと `ToolSearch` | 利用可能ツール・リソースと、公開されている場合のツール検索 |
| スキル作成 | Cursor 組み込み `create-skill` | 公式 `skill-creator:skill-creator` へ接続。外部プラグインが必要 | native `skill-creator` へ接続 |
| 作成するスキルの配置 | `.cursor/skills/` 等 | `.claude/skills/` 等。`automate-me` は直接の skill ディレクトリへ配置 | `.agents/skills/`、`~/.codex/skills/` 等 |
| 外部依存の指示 | 別プラグイン cursor-team-kit の `deslop`、`control-cli`、`control-ui` | 3指示書と MIT ライセンスを内部同梱 | 同左 |

本家の役割別モデル選択・パネル人数・予算ラベルは保持している。ただし、それらのモデルを Claude Code や Codex からすべて起動できるという意味ではない。setup は同一モデルの利用可能な指定へ解決し、存在しない選択はユーザーに選択を求める。一方、Interrogate に元からある「モデル指定を拒否された場合に近いモデルへ差し替える」手順は維持している。Opus 5 / low と GPT-5.6 Luna / xhigh は検証時の指定であり、配布版の全役割の既定値ではない。

creator の接続先は本家と異なるため、作成処理の実装自体が同一ではない。description 改善や反復を求める指示は本家由来であり、専用の同名コマンドがないことだけを移植の不具合とは扱わない。

## ユーザー指定で除外・変更した機能

- `reminder` を削除。本文やフックへの移し替えはしていない。
- `readonly` と agent mode の権限指定を削除。本家本文の「調査者はコードを書かない」等の作業範囲は残す。
- クラウド worker をローカル子エージェントへ変更。コードを書く worker は個別の local worktree を使い、開始 branch とパスを依頼へ渡す。
- クラウド URL、teleport、VM、cloud-sleeper、クラウドセッションの継続・回収を除外。ローカルプロセス終了後もクラウドで継続する性質は再現しない。
- `make-bot-ui` の実行手順を除外説明と固定した本家リンクへ置換。したがって、内部ファイルが46個あっても46個すべての元手順を提供しているわけではない。
- 30分ごとの起動、sleep による起動通知、予備の heartbeat を削除。監査の内容は残し、別の自動起動条件は追加していない。計画テンプレートの tick prompt は定期起動を伴わない監査項目へ整理。
- `check-plan.mjs` から30分の定期処理を必須とする条件を削除。Codex 版は goal 必須マーカーを `/goal` から `create_goal` へ変更。

コンパクション後の全文保持は移植側で保証しない。各環境の標準のコンテキスト管理に従う。本家 Cursor の実行環境はないため、Cursor が常に全文を保持するとも主張しない。

## 再現できていない操作と、現在の本文

| 操作 | 現在の状態 |
| --- | --- |
| Claude の agent 自身による goal 設定・取得 | 利用できる操作を確認できず、実際の `Skill(goal)` は UI コマンドとして拒否された。Autopilot-full / stack / Multi-phase plan は冒頭に非対応注記があるが、その下には本家の arm/read goal 手順が残る。その部分を実行可能とは説明できない |
| Codex の watcher 通知による終了済みターンの再開 | 確認した CLI では再現できない。Autonomous run、Babysit、Shipping、Bug fix、Visual parity は冒頭で非対応を明記し、本文には `/loop` を使う指示が残る。実行中に待つ操作とは異なる |
| Claude のイベント監視 | Babysit / Shipping を native の動的 `/loop` と `Monitor` へ翻訳。有限コマンドの出力後に親の応答が再開することは検証済み。実際の PR watcher の長期運用を検証したという意味ではない |

定期タイマーの除外と、イベント通知の上記制約は区別する。これらの非対応操作は独自サービスで補っていない。

## 比較で確認し、修正した不備

1. **一般名詞 Task の誤置換を修正。** 両版の計画テンプレートを、本家の `## <Task as a verb phrase> (<PR id>)` に戻した。ここはツール名ではなく、作業を動詞句で記す見出しである。[本家](https://github.com/cursor/plugins/blob/e31650eea443aaea1e84cc15d88c13f40080b275/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md#L79)、[Claude](../claude/skills/poteto-mode/playbooks/multi-phase-plan.md)、[Codex](../codex/.agents/skills/poteto-mode/playbooks/multi-phase-plan.md)。
2. **reflect の内部ファイルへの対応漏れを修正。** 使用実績の検出と Routing が、登録された `SKILL.md` と内部の `instructions.md` を扱うよう整合させた。カタログの未発火に対する description 改善は登録スキルに適用する。内部ファイルが選択されなかった場合は、選択を担う呼出元の既存指示を本文修正の対象とする。reviewer・synthesizer・親の適用手順を揃え、登録用 validator に内部ファイルを直接渡す対象指定も修正した。本家の証拠・採否基準と承認手順は維持する。[Claude reviewer](../claude/skills/poteto-mode/internal/reflect/references/judgment-reviewer.md)、[Codex reviewer](../codex/.agents/skills/poteto-mode/internal/reflect/references/judgment-reviewer.md)。
3. **Claude の make-bot-ui 除外理由のプラットフォーム名を修正。** 誤っていた `Claude Code cloud routines` を、実際の依存先である Cursor cloud routines に直した。クラウド機能を除外する扱いは維持する。[修正ファイル](../claude/skills/poteto-mode/internal/make-bot-ui/instructions.md)。

修正後の両計画テンプレートを既存の `check-plan.mjs` で検証し、どちらも `0 problems`。Claude の plugin manifest は `claude plugin validate`、Codex の入口は `quick_validate.py` に合格した。Reflect は指示間の整合を確認したもので、今回の修正後にワークフロー全体の実行試験を行ったという意味ではない。

Cursor の組み込み babysit を使わないという文や、worktree cleanup の `.cursor/worktrees`・Cursor cache の例も残る。後者は他アプリの実在する掃除対象にもなり得るため、Cursor という語が残るものを一律に実行不能とは判定しない。

## 本文を変更していない部分と同梱物

- 23原則の本文は、登録用 frontmatter と内部リンク化を除き維持している。6原則には参照先ファイル名変更や名前へのリンク追加があり、残り17原則の本文はそのまま。両移植版の原則ファイルは同内容。
- 23プレイブックはすべて存在する。ただし上記の除外・非対応操作を含むため、全プレイブックが本家どおり完走するという意味ではない。
- 同梱スクリプトの変更は `check-plan.mjs` と `worktree-audit.sh`。後者を各環境の履歴形式に合わせて変更した。Orchestrate と PR watcher の実装・テスト、bootstrap、package / lockfile、decision-log script は本家のファイルを保持している。
- cursor-team-kit の3指示書は、同じ固定コミットにある依存元の本文を変更せず同梱している。
- 本家の README、`docs/guide/` と画像、ロゴ、`.gitignore` はそのまま同梱していない。移植版の README・翻訳記録を別途作成している。
- 本家の `automations/benny/` は未同梱。これは Slack 報告の triage と再現・修正を扱う2つの Cursor automation 用セットで、47個の登録スキルとは別である。
- Claude manifest は `.claude-plugin/plugin.json`、移植版の version は `0.1.0`。本家 manifest の displayName / homepage / repository / logo / category / tags と明示的な探索パスは持たない。Codex はこの manifest を使わず、skill UI 設定とプロジェクトの agent 設定を同梱する。MIT ライセンスと原著者表記は保持する。

## 正式な差分と更新手順

現在の固定コミット・全ファイル対応・除外理由・移植専用ファイルは [maintenance/upstream.json](../maintenance/upstream.json)、現在の完全な変更は [Claude パッチ](../maintenance/patches/claude.patch) と [Codex パッチ](../maintenance/patches/codex.patch) に保存している。対応表どおりに配置した原文へ各パッチを適用し、現在の配布版を復元できることを確認した。

本家更新時の三者比較、追加・削除・競合の処理、反映後の検証は [更新手順](updating-upstream.md) に記載する。この整備では本家のバージョンや実行時のスキル本文は変更していない。

## 過去の監査用の生差分

修正前の監査時点の配置対応一覧は `tmp/experiments/upstream-audit/inventory.json`、生差分は同ディレクトリの `claude-raw.patch` と `codex-raw.patch`。今回の修正前ファイルは `tmp/experiments/upstream-fixes/before/`、修正差分は `tmp/experiments/upstream-fixes/fixes.diff` に保存した。追加された effort 定義・依存ファイルは inventory の extra に列挙する。これらの一時ファイルは git 管理対象外。ファイル数は変更の重大さを表さず、上記の意味の差分と合わせて読む。

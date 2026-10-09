# 本家との差分監査

2026-09-20 に監査し、2026-10-10 に更新。全ファイルの比較基点は `cursor/plugins` のコミット `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a` にある pstack 0.15.9 と、このリポジトリの `claude/`・`codex/`。0.15.5 から 0.15.9 への変更と、環境固有の翻訳・ユーザー指定の除外は下記に記録する。

意図した移植差分に加え、一般名詞の誤置換、内部ファイル化の反映漏れ、除外理由の誤記が見つかった。直前の「実装完了」という断言には、これらを見落とした問題がある。下記3種類の不備は監査後に両版の該当箇所を修正した。

## 読み込みと実行の差分

| 項目 | 本家 | Claude Code 版 | Codex 版 |
| --- | --- | --- | --- |
| 公開するスキル | `skills/` の50スキル。下位スキルも個別に明示起動可能 | `/pstack:poteto-mode` と `/pstack:setup-pstack`。その他48個は `internal/<name>/instructions.md` | `$poteto-mode` と `$setup-pstack`。その他48個は同じ内部ファイル構成 |
| 内部化の意味 | 各スキルをネイティブスキルとして呼ぶ | ワークフロー用の内部ファイルを読み、その指示を適用する。`setup-pstack` はネイティブスキルとして登録する | 同左 |
| 登録設定 | `setup-pstack` 以外の49スキルに `disable-model-invocation`。`poteto-mode` には `mode`、`reminder`、`icon`、`color` もある | `poteto-mode` は明示起動専用。`setup-pstack` は自動選択を禁止しない。`mode/icon/color` は除去し、`reminder` はユーザー指定で除外 | `poteto-mode` の `agents/openai.yaml` は `allow_implicit_invocation: false`。`setup-pstack` に同設定は置かない。`mode/icon/color` は移さず、`reminder` は除外 |
| 委任 | `Task`、`generalPurpose`、`poteto-agent`、Comment Sicko | native `Agent` と `pstack:` 名前空間。`is_background` を `background` へ変更 | native `spawn_agent`。エージェント本文を内部ファイルから読み、子の `message` に渡す |
| 子の起動指示 | `Task` の `subagent_type` と `run_in_background` を本文で指定 | 役割、effort 別の定義、非同期実行、新しい子の文脈を指示。`Agent` の引数名は指定しない | 役割の本文、非同期実行、新しい子の文脈を指示。`spawn_agent` の引数名は指定しない |
| 指示の優先度 | ネイティブエージェント定義 | ネイティブエージェント定義を使う。本文なしの custom general-purpose と組み込み general-purpose の同一性は未実証 | エージェント本文を依頼メッセージで渡すため、ネイティブ定義と同じ指示優先度とは主張しない |
| 独立した子の文脈 | Cursor の subagent 実行 | 新しい子の文脈を本文で要求 | 新しい子の文脈を本文で要求。V1 の `fork_context: false` と V2 の `fork_turns: "none"` は本文から削除 |
| 委任の深さ | Orchestrate は coordinator→track→worker | 通常の対話 CLI で親→子→孫、子での集約を実行確認。非対話では子が先に終了すると孫の結果は親へ直接届く | V1 向けに `[agents] max_depth = 3` を同梱。V2 ではこのキーは無視される |
| モデル・effort | Cursor のモデル名に effort を含む。役割別モデル・パネルを指定 | `{model, effort}` に分離。3系統×5 effort の native agent 定義を追加 | 同じ `{model, effort}` を保存 |
| モデル設定の保存先 | `~/.cursor/rules/pstack-models.mdc` | 対象プロジェクトの `AGENTS.md` の共通区画。`CLAUDE.md` はそこへの相対シンボリックリンク | 同じ共通区画 |
| 質問 | `AskQuestion` | `AskUserQuestion`。4候補はツール、5〜6候補は番号付きチャット。カテゴリの複数選択条件を維持 | `automate-me` は4〜6候補を番号付きチャットで提示。setup は利用可能な質問ツールまたはチャット |
| 履歴 | Cursor の transcript 配置・形式 | `~/.claude/projects/`、親子の JSONL、文字列・content block の両形式 | `~/.codex/sessions/` の rollout。session ID、cwd、可視メッセージ・ツール入力を参照 |
| MCP 発見 | Cursor の `mcps/` 等 | 利用可能ツールと `ToolSearch` | 利用可能ツール・リソースと、公開されている場合のツール検索 |
| スキル作成 | Cursor 組み込み `create-skill` | 公式 `skill-creator:skill-creator` へ接続。外部プラグインが必要 | native `skill-creator` へ接続 |
| 作成するスキルの配置 | `.cursor/skills/` 等 | `.claude/skills/` 等。`automate-me` は直接の skill ディレクトリへ配置 | `.agents/skills/`、`~/.codex/skills/` 等 |
| 外部依存の指示 | 別プラグイン cursor-team-kit の `deslop`、`control-cli`、`control-ui` | 3指示書と MIT ライセンスを内部同梱 | 同左 |

本家 0.15.9 の役割別モデル選択・3人構成のパネル・予算ラベルを保持している。ただし、それらのモデルを Claude Code や Codex からすべて起動できるという意味ではない。setup は同一モデルの利用可能な指定へ解決し、存在しない選択はユーザーに選択を求める。モデル指定が後から拒否された場合の本家 0.15.9 の代替手順も、対応する下位ファイルへ移した。Opus 5 / low と GPT-5.6 Luna / xhigh は過去の実行検証時の指定であり、配布版の全役割の既定値ではない。

creator の接続先は本家と異なるため、作成処理の実装自体が同一ではない。description 改善や反復を求める指示は本家由来であり、専用の同名コマンドがないことだけを移植の不具合とは扱わない。

## 0.15.5 更新で反映した動作

0.15.2 から 0.15.5 で本家の対象162ファイルのうち45ファイルが変更され、新規・削除はなかった。両環境に配布する本文では、Autopilot の検証を code-ready head と以後の patch 変更ごとに開始し、self-proof・CI・babysit と並行させた。merge 直前の rebase とその head の CI、複数の独立監査 lane、指摘に対する red test または再現記録、子エージェントの `children.tsv` と停滞監査、Shipping の patch-id に基づく lane 結果の再利用条件も反映した。

`setup-pstack` は廃止された役割行を再実行時に落とし、その行をユーザーへ示す。本家 README の「0.15.3以前の rule」は Cursor の旧設定を指し、その行の削除と再実行を案内している。移植版の初期0.15.2も旧既定値をグローバル設定へ保存し得た。旧既定値から移行する場合は、`~/.claude/rules/pstack-models.md` の pstack 役割行と `~/.codex/AGENTS.md` の pstack 区画だけを削除し、対象プロジェクトで setup を再実行する。他の指示は残し、個別に選んだモデルは再実行時に選び直す。setup スキルに旧グローバル設定を操作する手順は加えない。判断記録の `log.sh` は既存ログを上書きしない追記方式へ更新した。クラウド worker と30分タイマーの除外は継続する。

## 0.15.9 更新で反映した動作

0.15.5 から 0.15.9 の本家差分は21ファイル。新規3ファイル、既存18ファイルの変更で、削除はない。`correct`、`benchmark-checklist`、`principle-explain-the-number` を内部ファイルとして追加し、50スキルのうち公開2・内部48、原則24の構成とした。

- `correct` は履歴から反復する失敗を抽出し、設計・型・lint/CI・テストの順で防止策を検討する。本文は公開設定の除去と配置に伴う変更を除き、本家の内容を保持した。
- 性能測定のチェックリストと `explain-the-number` 原則を追加し、Perf issue と Hillclimb のボトルネック確認・測定条件・試行順序を更新する。
- `architect` の設計資料に、エージェントが間違えにくい構造を選ぶ基準を追加する。
- 子エージェントは新規起動を原則とし、再開は移すのが難しい状態が必要な場合など、本家が指定する例外に限定する。入口・エージェント定義・Swarm の参照を揃える。
- Autopilot-full / stack と Multi-phase plan から goal の設定・取得を削除する。途中成果の push とマージ直前の rebase 条件も本家に合わせる。本家の定期監査は1時間へ変わったが、既存のユーザー指定に従って定期タイマーの起動指示と検査条件は除外する。
- Opening a PR の本文・作成手段、Technical writing、TypeScript のスキーマ検証の指針を更新する。

本更新の検証結果は [更新記録](updating-upstream.md#0159-への更新記録) に記録し、過去の試験成功を本更新の実行成功とは扱わない。

## ユーザー指定で除外・変更した機能

- 2026-10-09 のユーザー指定により、`poteto-mode` 本文先頭に Claude Code / Codex の相互呼出しについて3段落を追加した。明示されていないタイムアウト・思考上限等の制限を禁止し、一貫したトピックではセッションID・スレッドIDでコンテキストを維持する。本家由来の指示ではない。
- `reminder` を削除。本文やフックへの移し替えはしていない。
- `readonly` と agent mode の権限指定を削除。`why` の調査者等にある書込禁止は保持する。ただし `how` の explainer 本文の `read-only access` も削除されており、その explorer / explainer prompt には別の明示的な書込禁止がない。
- クラウド worker をローカル子エージェントへ変更。コードを書く worker は個別の local worktree を使い、開始 branch とパスを依頼へ渡す。
- クラウド URL、teleport、VM、cloud-sleeper、クラウドセッションの継続・回収を除外。ローカルプロセス終了後もクラウドで継続する性質は再現しない。
- `make-bot-ui` の実行手順を除外説明と固定した本家リンクへ置換。したがって、内部ファイルが48個あっても48個すべての元手順を提供しているわけではない。
- 定期監査の起動、sleep による起動通知、予備の heartbeat を削除。監査の内容は残し、別の自動起動条件は追加していない。計画テンプレートの tick prompt は定期起動を伴わない監査項目へ整理。
- `check-plan.mjs` から定期監査を必須とする条件を削除。goal 必須条件は 0.15.9 の本家でも削除されており、移植版に残さない。

コンパクション後の全文保持は移植側で保証しない。各環境の標準のコンテキスト管理に従う。本家 Cursor の実行環境はないため、Cursor が常に全文を保持するとも主張しない。

## 再現できていない操作と、現在の本文

| 操作 | 現在の状態 |
| --- | --- |
| Claude の agent 自身による goal 設定・取得 | 過去の試験では `Skill(goal)` が UI コマンドとして拒否された。0.15.9 の本家が Autopilot-full / stack / Multi-phase plan から goal 操作を削除したため、移植版も当該手順と非対応注記を削除した |
| Codex の watcher 通知による終了済みターンの再開 | 確認した CLI では再現できない。Autonomous run、Babysit、Shipping は非対応を明記する。Codex 向けの5プレイブックから `/loop` の実行指示を除いた。実行中に待つ操作とは異なる |
| Claude のイベント監視 | Babysit / Shipping を native の動的 `/loop` と `Monitor` へ翻訳。有限コマンドの出力後に親の応答が再開することは検証済み。実際の PR watcher の長期運用を検証したという意味ではない |

定期タイマーの除外と、イベント通知の上記制約は区別する。これらの非対応操作は独自サービスで補っていない。

## 比較で確認し、修正した不備

2026-10-09 に、Perf issue 手順3の `Review the diff.` を共通原本と両配布版に復元した。これは共通原本を導入したコミット `d494fd2` で削除された、本家由来のレビュー工程である。環境対応による除外ではなく、0.15.9 更新時にも見逃していた欠落だった。この修正で、以下に記載するその他の移植差分が解消したわけではない。

1. **一般名詞 Task の誤置換を修正。** 両版の計画テンプレートを、本家の `## <Task as a verb phrase> (<PR id>)` に戻した。ここはツール名ではなく、作業を動詞句で記す見出しである。[本家](https://github.com/cursor/plugins/blob/ecc249f1e306fc64ddf83c7bed16cacf7c2239db/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md)、[Claude](../claude/skills/poteto-mode/playbooks/multi-phase-plan.md)、[Codex](../codex/.agents/skills/poteto-mode/playbooks/multi-phase-plan.md)。
2. **reflect の内部ファイルへの対応漏れを修正。** 使用実績の検出と Routing が、登録された `SKILL.md` と内部の `instructions.md` を扱うよう整合させた。カタログの未発火に対する description 改善は登録スキルに適用する。内部ファイルが選択されなかった場合は、選択を担う呼出元の既存指示を本文修正の対象とする。reviewer・synthesizer・親の適用手順を揃え、登録用 validator に内部ファイルを直接渡す対象指定も修正した。本家の証拠・採否基準と承認手順は維持する。[Claude reviewer](../claude/skills/poteto-mode/internal/reflect/references/judgment-reviewer.md)、[Codex reviewer](../codex/.agents/skills/poteto-mode/internal/reflect/references/judgment-reviewer.md)。
3. **Claude の make-bot-ui 除外理由のプラットフォーム名を修正。** 誤っていた `Claude Code cloud routines` を、実際の依存先である Cursor cloud routines に直した。クラウド機能を除外する扱いは維持する。[修正ファイル](../claude/skills/poteto-mode/internal/make-bot-ui/instructions.md)。

修正後の両計画テンプレートを既存の `check-plan.mjs` で検証し、どちらも `0 problems`。Claude の plugin manifest は `claude plugin validate`、Codex の入口は `quick_validate.py` に合格した。Reflect は指示間の整合を確認したもので、今回の修正後にワークフロー全体の実行試験を行ったという意味ではない。

Cursor の組み込み babysit を使わないという文や、worktree cleanup の `.cursor/worktrees`・Cursor cache の例も残る。後者は他アプリの実在する掃除対象にもなり得るため、Cursor という語が残るものを一律に実行不能とは判定しない。

## 0.15.9 全文監査で確認した既存の内容差分

2026-10-09 に本家165ファイルと配布版284ファイルを照合した。全対応先277件と移植専用7件を確認し、未配置・重複・実行権限差はなかった。各版49ファイルはバイト一致。24原則は登録設定・リンク・強調表記以外の本文が一致した。環境置換という分類は、意味の同一性を示すものではない。

以下は本家の本文と異なる実行条件であり、先頭注意事項以外も一言一句同じという状態ではない。2026-10-10 に差分を報告したうえで更新PRの作成指示を受けたため、この更新では保持する。特記のないものは両版共通。

| 箇所 | 本家との差分 |
| --- | --- |
| Shipping | 本家の当該手順にない `or a named driver where none exists` という検証手段の例外を追加 |
| Reflect | 未選択の内部ファイルについて、対象の description 改善の代わりに呼出元の選択指示を本文編集する分岐を追加。validator 対象を native 登録スキルに限定 |
| モデル解決 | エラー内の同系 slug の探索を利用可能モデル一覧へ変更し、同系もなければユーザーに選択を求める分岐を追加。`auto` / `inherit-parent` は親のモデルと effort を継承 |
| Codex Interrogate | 代替モデルの「同系統の最高推論レベルを優先する」条件が欠落。Claude 版は保持 |
| Setup pstack | グローバル rule からプロジェクトの `AGENTS.md` 区画へ保存先・適用範囲を変更。`CLAUDE.md` のリンク化、既存指示の統合、競合時の質問を追加。質問ツール優先指定は省略 |
| Swarm | コードを書くローカル worker の個別 worktree と、開始 branch / path の受渡しを必須化 |
| Orchestrate | `ORCH_STORE` を初期化前に絶対パスで設定し全呼出しで共有。子の完了時に結果を読んでから inbox に投入する手順を具体化 |
| Codex Orchestrate | 子の統括役の `durable` 指定を削除。次の一群を「単一メッセージで起動」から「並列起動」へ変更。worker のローカル例外内にあった runtime control skill の列挙も省略するが、他段落の実物検証指示は保持 |
| Codex Autonomous run | watcher の結果が返るまで親ターンを維持する指示を追加 |
| Claude Automate-me | 本家と Codex 版が許容する personal category の階層配置を禁止し、直下の skill ディレクトリに限定 |
| Automate-me の質問 | Claude は4択を質問ツール、5〜6択を番号付きチャットへ変更。Codex は番号付きチャットへ変更 |
| Codex Recall | 話題を grep する手順を可視のユーザー発言の先行検査へ変更。assistant / tool にしか出ない話題では候補集合が変わり得る |
| 履歴・作成・委任 | 各環境の可視履歴形式、別の creator 実装、内部本文の読取へ変更。Codex の役割本文のメッセージ渡しは native 定義と同じ指示優先度を保証しない |

上記に加え、プレイブックの8ファイル・計16箇所で Markdown リンクが code span 内に残り、クリック可能なリンクとして機能しない。参照先ファイルは存在する。これは本文の条件変更とは別の表記不備であり、本更新では保持する。

原文・配布文・行番号・各ファイルのハッシュを含む監査記録は `tmp/experiments/content-verification-2026-10-09/` に保存した。一時記録は git 管理対象外。配布本文の完全な差分は管理対象の `maintenance/patches/` で確認できる。

## 同梱物と対象範囲

- 24原則はすべて配置している。本家 0.15.9 の `explain-the-number` 原則も反映し、登録用 frontmatter と内部リンクは移植版の配置に合わせている。両移植版の共通部分は同内容。
- 23プレイブックはすべて存在する。ただし上記の除外・非対応操作を含むため、全プレイブックが本家どおり完走するという意味ではない。
- 同梱スクリプトの移植固有の変更は `check-plan.mjs` と `worktree-audit.sh`。後者を各環境の履歴形式に合わせて変更した。0.15.5 で本家が更新した `check-plan.mjs` と decision-log の `log.sh` も反映している。Orchestrate と PR watcher の実装・テスト、bootstrap、package / lockfile は本家のファイルを保持している。
- cursor-team-kit の3指示書は、同じ固定コミットにある依存元の本文を変更せず同梱している。
- 本家の README、`docs/guide/` と画像、ロゴ、`.gitignore` はそのまま同梱していない。移植版の README・翻訳記録を別途作成している。
- 本家の `automations/benny/` は未同梱。これは Slack 報告の triage と再現・修正を扱う2つの Cursor automation 用セットで、50個の登録スキルとは別である。
- Claude manifest と移植版の version の正本は [plugin.json](../claude/.claude-plugin/plugin.json)。本家 manifest の displayName / homepage / repository / logo / category / tags と明示的な探索パスは持たない。Codex はこの manifest を使わず、skill UI 設定とプロジェクトの agent 設定を同梱する。MIT ライセンスと原著者表記は保持する。

## 正式な差分と更新手順

現在の固定コミット・全ファイル対応・除外理由・移植専用ファイルは [maintenance/upstream.json](../maintenance/upstream.json)、移植差分は [Claude パッチ](../maintenance/patches/claude.patch) と [Codex パッチ](../maintenance/patches/codex.patch) に保存している。Claude manifest の version はパッチから除外し、その他の内容と実行権限を保守ツールで検証する。

本家更新時の三者比較、追加・削除・競合の処理、反映後の検証は [更新手順](updating-upstream.md) に記載する。保守基点は 0.15.9 である。

## 過去の監査用の生差分

修正前の監査時点の配置対応一覧は `tmp/experiments/upstream-audit/inventory.json`、生差分は同ディレクトリの `claude-raw.patch` と `codex-raw.patch`。今回の修正前ファイルは `tmp/experiments/upstream-fixes/before/`、修正差分は `tmp/experiments/upstream-fixes/fixes.diff` に保存した。追加された effort 定義・依存ファイルは inventory の extra に列挙する。これらの一時ファイルは git 管理対象外。ファイル数は変更の重大さを表さず、上記の意味の差分と合わせて読む。

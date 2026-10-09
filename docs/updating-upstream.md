# 本家の更新を取り込む

比較元の正本は [maintenance/upstream.json](../maintenance/upstream.json)。現在は `cursor/plugins` の pstack **0.15.9**、コミット `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a` に固定している。同梱する cursor-team-kit の3指示書と LICENSE も同じ固定コミットのものを使う。

この仕組みは開発者用であり、実行時にスキルへ指示を追加しない。スキル本文の正本は `shared/skills/` に置き、人が翻訳・レビューする。`claude/`・`codex/` の配布ファイルは `tools/generate.py` で生成し、パッチは生成結果を記録する。本家の変更を自動翻訳しない。

## 保存するもの

| ファイル | 役割 |
| --- | --- |
| [upstream.json](../maintenance/upstream.json) | リポジトリ、固定コミット、pstack バージョン、対象範囲、全元ファイルの配置先・除外理由、移植専用ファイルの理由 |
| [shared/skills](../shared/skills) | Claude・Codex 共通のスキル本文。固有箇所は `{{#claude}}...{{/claude}}`・`{{#codex}}...{{/codex}}` で指定 |
| [shared/clients](../shared/clients) | 片方だけに配布するファイルと Claude のエージェント定義テンプレート |
| [generate.py](../tools/generate.py) | 共通原本から両配布版と Claude の effort 別エージェント定義を生成。`--check` で生成結果との一致を確認 |
| [claude.patch](../maintenance/patches/claude.patch) | 原文を Claude の配置先へ並べた状態から、現在の Claude 配布版への変更。plugin の version は除外 |
| [codex.patch](../maintenance/patches/codex.patch) | 同じく Codex 配布版への完全な変更 |
| [upstream-differences.md](upstream-differences.md) | 変更の意味、ユーザー指定の除外、非対応機能、検証範囲 |
| [upstream.py](../tools/upstream.py) | パッチ更新・復元検証・新旧本家と移植版の三者比較 |

リポジトリ直下の [.claude-plugin/marketplace.json](../.claude-plugin/marketplace.json) は、この移植版の配布カタログとして別途管理する。本家由来の配布ファイルのパッチには含めない。配布バージョンの正本は [claude/.claude-plugin/plugin.json](../claude/.claude-plugin/plugin.json) の `version` だけとし、カタログ・ドキュメント・パッチへ番号を重複記載しない。Claude のリリース更新時はこの値を上げる。バージョンだけの変更なら、パッチの再生成は不要。

パッチの基点は本家の元ディレクトリではなく、対応表どおりに配置した原文。Claude manifest は原文・配布版ともに `version` を取り除いて JSON を整形してから差分を作る。その他の本文・メタデータ・実行権限の変更と移植専用ファイルの追加はパッチに記録する。

一つの元ファイルから複数の配置先を指定できる。Claude のエージェント定義17件も共通の役割本文から生成し、元のエージェント本文に対応づける。本家の本文変更は派生した各定義の比較対象になる。

`scopes` は pstack 全体と同梱依存のディレクトリを含む。`files` に対応先のない元ファイルも、環境ごとの除外理由を持つ。新しいファイルを黙って除外しない。移植専用の `additions` には、本文なしの general-purpose effort 定義と Codex の設定を記録する。

旧 [claude-code-vocabulary.patch](claude-code-vocabulary.patch) は初期実験の履歴資料であり、現行版の復元・更新には使わない。`tmp/experiments/` の過去の監査差分も、現在の完全パッチの正本ではない。

## 準備と現在の状態の確認

必要なのは Python 3.9 以降と Git。Python の外部ライブラリは不要。以下はリポジトリのルートで実行する。原本は Git object から読むため、取得先の現在の branch や未コミットの編集には依存しない。

配布ファイルを更新するときは、`shared/skills/` の本文を編集してから生成する。共通部分はそのまま書き、環境ごとの部分だけを `{{#claude}}...{{/claude}}`・`{{#codex}}...{{/codex}}` で囲む。片方だけにあるファイルや Claude のエージェント定義は `shared/clients/` を編集する。配布ファイルを直接編集した場合は `--check` が差分を検出する。

```sh
python3 tools/generate.py
python3 tools/generate.py --check
```

```sh
git clone --filter=blob:none https://github.com/cursor/plugins.git tmp/experiments/upstream-source
python3 tools/upstream.py check --source tmp/experiments/upstream-source
```

既に clone があればそのパスを使う。固定コミットを持たない shallow clone では、先にそのコミットを fetch する。

`check` はまず生成結果と配布ファイルの一致を確認する。続けて元ファイル・配布ファイルの対応漏れ、重複する配置先、本家と `upstream.json` のバージョン不整合を検出する。さらに一時ディレクトリへ原文を配置し、保存パッチを適用して、配布版の内容・ファイル集合・実行権限を検証する。Claude manifest は配布バージョンと JSON の整形差を検証対象から外し、その他のフィールドは検証する。配布物は変更しない。未記録の配布ファイル変更があれば失敗する。symlink 等の未対応ファイル形式も黙って落とさず失敗する。

## 更新候補を作る

まず新しい本家の対象コミットを取得する。以下の `NEW_COMMIT` は、採用候補のコミット ID に置き換える。指定 ref は解決した完全なコミット ID としてレポートに保存する。

```sh
git -C tmp/experiments/upstream-source fetch origin NEW_COMMIT
python3 tools/upstream.py compare \
  --source tmp/experiments/upstream-source \
  --to NEW_COMMIT \
  --out tmp/experiments/upstream-update
```

出力先には存在しないディレクトリを指定する。`compare` は最初に生成結果の一致と現在のパッチを検証し、次の3点を出力する。配布版と固定コミットは更新しない。

- `report.json`：新旧コミット・新バージョン、追加・削除・変更、各配置先の比較結果。
- `upstream.patch`：旧本家から新本家への差分。同梱依存や除外ファイルの変更も含む。
- `candidate/claude/`・`candidate/codex/`：現在の配布版を基に三者比較した候補。新規元ファイルは配置が未決定なので自動追加しない。

Claude manifest の三者比較では、本家のバージョン変更から切り離して、現在の配布版の `version` を候補に保持する。

| 結果 | 対応 |
| --- | --- |
| `upstream-only` | 本家だけの変更、または既に移植版と同じ変更。新しい本文・リンク・ツール名を確認する |
| `port-only` | 内容が本家と同じままで、移植差分を保持した箇所 |
| `merged-needs-review` | 原文・移植版の変更がテキスト上は統合できた。翻訳と意味のレビューは必要 |
| `text-conflict` | 候補の競合マーカーと旧原文・新原文・現行移植版を読み、解決する |
| `delete/modify-conflict` | 本家は削除、移植版は変更済み。削除するか別の元ファイルに対応づけるかを判断する |
| `binary-review` | 両側で変わったバイナリ。候補には現行版を保持し、人が選ぶ |
| `classify-new-source` | 新規ファイルの配置先または除外理由を決める |
| `review-exclusion` | 除外していた元ファイルの変更。除外理由が引き続き成り立つか確認する |

改名は削除＋追加として表示する。ファイル名の類似だけで対応先を決めない。本家が削除し移植側に変更がないファイルは候補から削除されるが、参照元の修正も確認する。Claude 専用 manifest など片側だけが採用する元ファイルは、対応表で他方の除外理由も確認する。

競合マーカーがないことは、正しく翻訳できた証拠ではない。新しい Cursor API、読み込み条件、内部参照、モデル選択、テンプレートや手順の変更を確認する。`poteto-mode` と `setup-pstack` を登録し、その他の48スキルを内部ファイルにする構成と、ユーザー指定の除外範囲は維持する。プラットフォームで実現できない操作は、独自の行動指示やサービスで補わず非対応として記録する。

## レビュー結果を配布版へ反映する

1. レポートの全変更を確認し、候補の競合を解決する。追加・削除・改名と複数配置先への影響を処理する。`candidate/` 全体を未確認で上書きしない。
2. 確認した変更を `shared/skills/` に反映し、必要な固有箇所を両環境のブロックへ翻訳する。`python3 tools/generate.py` で `claude/`・`codex/` を更新する。
3. `maintenance/upstream.json` の対応・除外・追加ファイルを更新し、`commit` と `version` を新しい本家の値へ更新する。同梱依存も同じ新コミットから比較される。
4. README、両環境の翻訳記録、本家との差分一覧を更新する。本文中の固定した本家リンクは新コミットの該当箇所を確認する。過去の試験や引用のリンクは履歴として保持する。
5. 生成結果の一致を確認し、パッチを更新して復元を検証し、変更経路に応じた試験を行う。

```sh
python3 tools/generate.py --check
python3 tools/upstream.py refresh --source tmp/experiments/upstream-source
python3 tools/upstream.py check --source tmp/experiments/upstream-source
python3 -m unittest discover -s tools -p 'test_*.py'
```

`refresh` は生成結果の一致を事前に確認し、レビュー済みの配布版から両パッチを作り直す。本文を翻訳するコマンドではない。対応漏れがある状態では作成しない。通常の移植修正でも、同じ固定コミットのまま `refresh` と `check` を使う。共通原本・配布版・manifest・パッチ・説明資料を一つの変更としてレビューし、履歴に残す。

## 更新時の検証

復元検証とツールの試験は保守機構の検証であり、スキルの実行試験とは区別する。

| 変更対象 | 検証 |
| --- | --- |
| 登録設定・配置 | `claude plugin validate ./claude` と Codex の native skill validator。明示起動と変更した内部参照を確認 |
| 導入経路 | `claude plugin validate .` で marketplace を検証し、一時設定で marketplace の追加・plugin の導入を確認。Codex は一時プロジェクトで README の `npx skills add` を実行し、内部ファイル・ライセンス・スクリプトの実行権限まで配置を確認 |
| 入口・プレイブック・委任 | 影響する実タスクで、必要な指示の読み込み、子への入力、結果の受け渡しをログで確認 |
| 計画テンプレート・check-plan | テンプレートから計画を取り出して各版の `scripts/check-plan.mjs` に渡す。検査条件を変えた場合は、その条件を欠く計画が失敗することも確認 |
| 同梱スクリプト | 対象スクリプトの既存テストと、変更した入出力の検証 |
| モデル・effort | 配布版は本家の役割選択を維持。実行試験の親子は Claude Opus 5 / low、Codex GPT-5.6 Luna / xhigh を指定し、実ログでも確認 |

実行試験は `tmp/experiments/` の一時プロジェクトで行う。モデルの事後説明だけを成功の証拠にせず、依頼文・設定・呼出引数・結果を記録する。全工程を試していない場合は、試した範囲を明記する。クラウド、定期タイマーによる終了後の再開、reminder、readonly の権限指定、コンパクション後の全文保持は検証要件へ戻さない。

## 初回の整備記録

2026-09-20：pstack の158ファイルと同梱依存の4ファイルを分類し、当時の Claude 145ファイル・Codex 131ファイルを完全パッチから復元した。元エージェントから派生する effort 定義も対応表に含む。当時は本家のバージョン自体を更新していない。

保守ツールの6テストも合格した。固定 Git object の読込、バイナリ・実行権限・追加ファイルの復元、未分類ファイルの検出、複数配置先への統合、本文の競合、追加・削除・除外ファイルの変更を、一時的な Git リポジトリで検証した。将来の本家リリースそのものを取り込んだ試験ではない。

同日の導入経路整備で marketplace を追加し、Codex のスキル単体にも本家 LICENSE を配置した。Codex 配布版は132ファイル、`npx skills add` の対象スキル内は130ファイルとなった。LICENSE の配置先は同じ本家ファイルへの対応として manifest に記録している。

## 0.15.5 への更新記録

2026-09-28：0.15.2 から 0.15.5 の対象162ファイルを比較した。変更は45ファイルで、新規・削除はなかった。共通原本で本文とスクリプトの変更を反映し、両版274ファイルを生成した。本家 README と guide、および配布版独自の version を持つ manifest は、対応表の除外・正規化方針どおりに扱った。Claude 145ファイル・Codex 133ファイルのパッチを新基点から復元検証した。

## 0.15.9 への更新記録

2026-10-05：0.15.5 から 0.15.9 の差分は21ファイルで、新規3ファイル、既存18ファイルの変更、削除なし。新規の `correct`、`benchmark-checklist`、`principle-explain-the-number` は既存の下位スキルと同じ内部ファイル構成へ配置した。既存本文の変更と翻訳判断は [差分一覧](upstream-differences.md#0159-更新で反映した動作) に記録した。

両版280ファイルを生成し、生成結果の一致と全ファイル対応を確認した。Claude 148ファイル・Codex 136ファイルのパッチ復元と実行権限の検証、保守ツール13テスト、Claude plugin validator、Codexの両入口のnative skill validatorに合格した。変更した配布本文のリンクはすべて解決した。新規3指示書は登録設定の除去・内部リンクの変換以外、本家本文と一致する。計画検証は両環境でgoal・定期起動を含まない正例と、trunk読取・status message・live laneをそれぞれ欠く負例、計8例で期待した結果を確認した。JavaScriptの構文検査も両版で通った。

Codex CLI 0.160.0 の一時プロジェクトで `$poteto-mode` を明示起動し、generatorを反復しない測定スクリプトを1回の概算として評価した。親子はGPT-6.1 Solを使用し、子は親のモデルを継承した。入口・benchmark-checklist・explain-the-numberの読み込み、新規の子への委任、子のコード調査と結果受け渡しを実ログで確認した。親は約0.012916 msの測定値を得たが、対象の10万件処理が実行されていないとして性能値の採用を拒否した。macOSでは `nproc` がなく、read-only sandboxでは `sysctl` のコア数取得も拒否された。配布本文へ独自の代替手順は追加していない。

Claude CLI 2.1.278 の同じ試験は、初回はOAuth認証の期限切れにより実行前に失敗した。ログイン後の再試行では、Claude Opus 5 / lowでプラグイン登録、benchmark-checklist・explain-the-numberの読み込み、1回の測定、general-purposeの子1人の非同期起動を実ログで確認した。測定値は約0.012833 msだった。試験用の `subprocess.run` に `timeout=300` を設定していたため、子の結果を親が受け取る前に終了した。これは試験実施者が設定した制限であり、Claudeや実行環境の制限ではない。この試行では結果受け渡しと最終判定は未確認である。再試行ログは `runtime/claude/retry-events.jsonl`。correctの修正工程、architectの設計工程、Autopilotの実PR運用、marketplace・skills CLIによる導入も今回未検証である。構造検証や上記の限定試験を、全ワークフローの実行成功とは扱わない。

その後、`subprocess.run` の timeout を取り除いて再実行し、終了コード0、stderr空で完了した。`runtime/claude/unbounded-events.jsonl` では native `Agent` による `pstack:poteto-agent` の起動、子の報告の受け渡し、親の最終判定を確認した。約0.01225 msという測定値について、generatorを反復しておらず測定対象の処理が走っていないとして採用を拒否した。これは先頭注意事項を追加する前の限定試験であり、Claude Code / Codex のCLI相互呼出しやIDによる文脈維持を検証したものではない。

依頼文・呼出引数・実ログは `tmp/experiments/upstream-0.15.9/runtime/`、計画検証は同ディレクトリの `autopilot-validation/results.json`、検証概要は `verification.json` に保存した。一時記録はgit管理対象外であり、この節を検証範囲の記録とする。

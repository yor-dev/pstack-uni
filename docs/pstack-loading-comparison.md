# pstack の読み込みと pstack-claude の変更

調査日: 2026-09-18。これは移植のための比較資料であり、移植実装や動作保証ではない。

この資料は初期調査の記録。以後、ユーザーの指定により、Claude 版では `poteto-mode` を入口として登録し、下位スキルをその内部ファイルとして配置する方針に変更した。本家の登録構造そのものを維持することは移植要件にしない。現在の実装は `claude/`、試験と制約は [Claude Code への翻訳](claude-code-translation.md) を参照。

本家のスキル本文、登録設定、エージェント定義、参照先を比較した。pstack-claude は調査手順の一部を維持しているが、起動条件、スキルの公開方法、継続モード、Codex での委譲方法を変更している。これらをまとめて「ツール名の違い」とは扱えない。

以前の `tmp/experiments/loading-routing/` は独自の入口と追加指示を使った実験である。本家との同等性の証拠には採用しない。証拠保全のためファイルとログはそのまま残す。

## 比較対象と判定の範囲

| 記号 | 対象 | 固定コミット |
| --- | --- | --- |
| U | pstack-claude が移植元として固定している本家、v0.14.8 | `e8d856f0273b42ebafe0ec3546bd645709e7c1b0` |
| P | 調査済み pstack-claude、v0.9.34 | `430a4f5d1fdcba0750ffa21e441ced5114f7d8ce` |
| N | 前回調査で取得した本家、v0.15.2 | `e31650eea443aaea1e84cc15d88c13f40080b275` |

P の移植元は [tools/upstream.json:3–19][P-pin] で確認した。まず U と P を比較し、U から N への本家の更新は別に扱った。N を現在のリモートの最新コミットと主張するものではない。

- ファイル上の事実。固定コミットから取得した本文・設定で確認した内容。
- 公開仕様。調査日に取得した各製品の公式文書に記載された内容。
- 未確認。実際のランタイムでの注入順序、適用範囲、継続・解除など、静的比較では確定できない内容。

今回 Cursor、Claude Code、Codex で pstack を実行して比較してはいない。ファイルを全文取得した事実と、ネイティブスキルとして起動した事実と、指示を実行した事実を区別する。追加確認で、この端末の PATH と通常のアプリ配置場所に Cursor は見つからず、ユーザーからも Cursor の実行環境はないと回答を得た。本家の実機検証は実施できていない。

## 本家が文書で定めている経路

本家のプラグインは `skills: "./skills/"` と `agents: "./agents/"` を宣言している。[U-manifest:29–30][U-manifest]。宣言上の対象はこの2ディレクトリである。実際に各定義がどう発見・提示されるかは実機で確認していない。

本家の説明では、`poteto-mode` が入口となり、原則の索引を読み、依頼に合うプレイブックを選び、必要なスキルを使う。プレイブックの手順はタスク一覧に原文で転記し、省略する手順も理由付きで残す。[U-guide:1–28][U-guide]、[U-mode:114–120][U-playbooks]

調査の場合は次の手順が明記されている。

1. `how` を使う。動機を調べる質問なら `why` も使う。
2. 読み取り専用調査であることを throughput checkpoint に記す。
3. 説明または比較・推奨をまとめる。
4. 返答に `unslop` を適用する。[U-investigation:7–10][U-investigation]

これは要求される手順であり、すべての文書がその順番でネイティブ注入されるというランタイム仕様ではない。

`how` は小さい質問でも説明担当を一人起動する。複雑な質問では探索担当を2〜4人起動し、その後に説明担当を起動する。説明担当のプロンプトには専用の参照資料を使う。[U-how:11–48][U-how]

プレイブックの手順内で行う一般の作業委譲には `poteto-agent` を使うよう指定されている。そのエージェント定義は、作業前に `poteto-mode` 全文と原則索引を読むよう指示している。一方、`how`、`why` などが指定するエージェント種別は尊重する。すべての子を `poteto-agent` に統一する指示ではない。[U-agent:1–9][U-agent]、[U-mode:89–95][U-subagents]

`how` と `why` はスキルであり、それぞれの本文が、起動する子の種別に `generalPurpose`、作業指示に専用プロンプトを指定している。本家の `agents/` にある定義は `poteto-agent` と `comment-sicko` の2個で、専用の `how-agent` / `why-agent` は存在しない。

## 対応表

| 項目 | 本家 U の仕様・記述 | pstack-claude P の実装・変更 | 今回の移植で維持すべき点／未確認事項 |
| --- | --- | --- | --- |
| 入口の起動制限 | `poteto-mode` に `disable-model-invocation: true`。[U-mode:1–8][U-mode] | 当該フラグを削除。生成時にも削除し、残っていると検証を失敗させる。[P-generate:210–215][P-invariant]、[424–449][P-derive] | ユーザーが合意した明示起動を維持する。フラグ名を別製品でそのまま使えば同じになるとは判断しない。 |
| 起動時の追加誘導 | 明示起動用メタデータと、起動後のプレイブック選択がある。 | `startup`・`clear`・`compact` でフックを発火し、複数ファイル・設計判断・原因不明のバグ・性能問題を自動誘導する。小さい作業や質問は直接処理する指示も追加。[フック定義][P-hook]、[注入本文][P-hook-text] | 起動後の振り分けと、起動前の自動誘導は別。本家の入口をこの条件に置き換えない。フックを off にしても、スキル側で削除済みのフラグは戻らない。 |
| 原則の登録と呼び出し | 23個の `principle-*` に `disable-model-invocation: true` が記載され、索引には適用する原則の全文を読む指示がある。[U-mode:37–75][U-principles] | 23個とも `user-invocable: false` に置換。これはモデルからの呼び出し制限と同じではない。変更履歴も自動選択の可能性を認めている。[P-changes:228–232][P-leaf-change] | ユーザーメニューでの表示、モデルへの説明の提示、本文の取得、適用条件を別々に確認する。本文が常時全部ロードされるとまでは言えない。 |
| 原則の段階的な読み込み | 索引は `poteto-mode` 本文内。適用する原則の leaf を全文読み、読んだ原則だけ引用する。[U-mode:13, 37–75][U-principles] | この指示は残る。[P-mode:16, 40–78][P-mode] | 維持できている本文として扱う。ただし前項の登録変更により、同じ条件で読まれることは未証明。 |
| プレイブックとタスク一覧 | プレイブックを選び、その手順を原文で転記する。[U-mode:114–120][U-playbooks] | 選択・原文転記の指示は残る。タスクツールがない場合の `todo.md` 作成を追加。[P-mode:12, 117–123][P-mode] | 原文転記と skip の記録を維持する。ファイル作成という代替動作は本家の要件そのものとは区別する。 |
| 調査プレイブック | `how`、必要なら `why`、指定の出力、`unslop`。[U-investigation][U-investigation] | `investigation.md` は U とバイト単位で一致。 | このプレイブックは参考にできる。入口の自動誘導が質問を直接処理させることと、明示起動後の調査手順を混同しない。 |
| `how` と説明用資料 | 小規模でも説明担当を起動。専用テンプレートを使う。[U-how][U-how] | 複雑度分岐・委譲・資料参照は残る。`generalPurpose` を `general-purpose` に変更し、モデル節と Codex 対応資料へのリンクを追加。呼び出し制限は削除。[P-how][P-how] | 委譲を省略しない要件は本家にすでにある。独自の強制文を入口に追加せず、本文が届く経路と実際の実行を分けて確認する。U の explorer/explainer テンプレートは P と完全一致。 |
| 一般委譲と専門委譲 | プレイブック手順内の一般委譲は `poteto-agent`。`how` / `why` 等は各スキル指定の種別。[U-subagents][U-subagents] | Claude プラグイン用の `pstack:poteto-agent` を指定し、エージェント定義の本文も保持。[P-mode:94][P-subagents]、[P-agent][P-agent] | 名前空間の対応は参考にできる。親子それぞれに何が読まれるかと、専門委譲の例外を維持する。単発起動が必ずこのエージェントに入るかは未確認。 |
| エージェントの継続と背景実行 | 定義の説明に既存 `poteto-agent` の再開を指定。`is_background: true` と、Task の `run_in_background: true` がある。[U-agent][U-agent]、[U-subagents][U-subagents] | 再開指示と呼び出し時の背景実行指示は残るが、定義の `is_background` は削除。[P-agent][P-agent] | 定義の設定と呼び出し引数を分けて対応させる。現在の Claude には `background` があるため、「対応機能なし」で終わらせない。再開・背景実行の実機同等性は未確認。 |
| モードの継続・適用除外 | `mode: true` と `reminder`。新タスクでは再判定、雑談や opt-out では適用しない旨がある。ガイドは sticky と説明。[U-mode][U-mode]、[U-guide:40–64][U-guide] | `mode` / `reminder` 等を削除。履歴では SessionStart フックで代替したと説明。[P-changes:226][P-mode-change] | 会話の開始時に誘導文を入れることは、アクティブなモードを維持することと同一ではない。雑談で手順を適用しないことと、モードを解除することも区別する。 |
| 読み取り専用と MCP | `how` の子は `readonly: true`。`why` は MCP を保持するため `readonly: false` としつつ、書き込みをしないと指示。[U-how][U-how]、[U-why:79–90][U-why] | `how` / `why` にはその設定表現が残る。一般方針には「MCP を失う種別を選ばない」と書き換え。[P-how][P-how]、[P-why:81–92][P-why] | これを Claude の有効な引数と確認したわけではない。ツール利用可否と「書かない」という作業指示は別。過去の CHANGES にある「readonly を削除済み」と現物は一致しない。 |
| 外部スキルへの依存 | Cursor 組み込み `create-skill`、cursor-team-kit の `deslop`・`control-cli`・`control-ui` 等を参照。[U-mode:26–30][U-mode] | `plugin-dev:skill-development`、同梱 `deslop`、Claude の `run` やプロジェクト `verify` に変更。[P-mode:27–31][P-mode] | パスや名前の修正だけで同等としない。各依存先の仕事・利用条件・実行可能性を個別確認する必要がある。 |
| Codex の本文取得 | U 自体は Cursor 用。Codex の対応仕様は持たない。 | 共有スキルを登録し、スキル起動の対応を「Skills load natively」と説明。[P-codex:15][P-codex] | 発見・本文取得・実行を分ける必要がある。この一文だけでは、明示限定の下位スキルをどう取得するかが決まらない。 |
| Codex の委譲 | 一般委譲のエージェント定義がある。[U-agent][U-agent] | 独自種別を登録せず、一般の `spawn_agent` に全文を読むよう指示する方式。委譲機能がなければ単一の逐次処理に縮退。[P-codex:23–40][P-codex] | 読むよう毎回指示する方式や、委譲を消す代替処理を同等としない。現在の Codex の独自エージェント機能で何を再現できるか確認する。 |
| 原則・返答の意味 | 本家の原則本文・返答形式がある。 | 23原則中3個の本文を独自変更。返答で見出しを使わない指示も追加。[P-changes:5–14][P-forks]、[P-mode:107][P-writing] | 移植とは別の改善・方針変更として除外する。良い変更かどうかと、本家に忠実かどうかは別。 |

## 数え上げと、維持されている資料

`skills/<name>/SKILL.md` のフロントマターを固定コミットから数えた結果。

| 対象 | スキル数 | `disable-model-invocation: true` | `user-invocable: false` |
| --- | ---: | ---: | ---: |
| U | 47 | 46 | 0 |
| N | 47 | 46 | 0 |
| P | 54 | 0 | 23 |

U / N で当該フラグが記載されていない例外は `setup-pstack`。P は本家の `make-bot-ui` を除外し、7個の cursor-team-kit スキルと独自の `babysit` を追加している。[P-pin][P-pin]、[P-readme:174–185][P-readme]

本家のスキルすべてが自動呼び出し禁止、と言い切るのも正確ではない。

U と P で完全一致した資料は、`investigation.md` と `how` の `explorer-prompt.md` / `explainer-prompt.md`。原則はフロントマターを除いた本文で20個が一致し、次の3個が異なった。

- `principle-attack-the-premise`
- `principle-prove-it-works`
- `principle-test-behavior-not-implementation`

P の変更履歴は、原則の変更や追加の運用指示をローカルの変更として記録している。[P-changes:5–14, 92–100][P-forks]。これは本家の更新に追いついていないこととは別である。

## 本家の版の差は別に扱う

U から N に進んでも、47スキルの構成、46個の `disable-model-invocation: true`、`poteto-mode` の `mode` / `reminder`、`poteto-agent` の定義、`how` の委譲構造、調査プレイブックは維持されている。

一方、N の `poteto-mode` は各主張に証拠または不確実性の表示を求める行を追加している。[N-mode:107][N-evidence]。`how` の説明用テンプレートにも句読点の変更がある。P がこの新しい行を持たないことを、U から移植するときに削除したとは扱わない。

`setup-pstack` は説明文だけでなく、reasoning budget の選択・反映・保存を追加し、設定用テンプレートの bug-fix / perf-issue / hillclimb のモデルも変更している。[N-setup:16–52][N-setup]。入口の発見文言とモデル設定処理に関係する本家の更新として、P の独自変更と分ける。

U → N の本文差分には多数のファイルが含まれる。今回確認した読み込み仕様の継続性から、全更新が文体のみ、あるいは全ワークフローが同じ、と一般化しない。

## 移植先の公開仕様と、まだ決まらない部分

以下は各ランタイムの公開仕様であり、pstack の同等性を証明するものではない。

| ランタイム | 確認した公開仕様 | この調査での意味 |
| --- | --- | --- |
| Cursor | 通常の `/` 選択は一つのメッセージへの添付。Custom Mode は別の選択操作で、退出まで毎ターン文脈に保持する。[公式説明][D-cursor-mode] | 本家の `mode: true` が通常の起動操作をどう変えるかは、この説明だけでは決まらない。実機観測が必要。 |
| Cursor | `disable-model-invocation` は自動適用を制限する。[公式説明][D-cursor-skills] | 本家が指定する下位スキルへの内部ルーティングについて、実際の取得手段を確認する必要がある。 |
| Claude Code | `disable-model-invocation: true` はモデルの Skill 呼び出しも拒否し、`user-invocable: false` はモデルから呼べる状態を残す。[公式説明][D-claude-skills] | 全フラグを復元すれば本家と同等になるとは、この仕様だけでは判断できない。全削除は呼び出し条件を変える。下位スキルの登録と取得の設計が未解決。 |
| Claude Code | 起動済みスキルの本文は後続ターンにも残る。コンパクション後の保持には上限がある。[公式説明][D-claude-lifecycle] | 継続性の確認はこの実機構を基準にする。単なるファイル Read と同じ保持を保証するとは書かれていない。 |
| Claude Code | `context: fork` は独立した子にスキル本文を渡す。エージェントの `skills` による事前読込では、モデル呼び出し禁止スキルを読込対象にできない。[skills][D-claude-fork]、[subagents][D-claude-preload] | 親のモードをそのまま子に継承する仕組みとはみなせない。入口を fork にすれば解決する、とは判断しない。 |
| Claude Code | 独自エージェントの `background: true` がある。[公式説明][D-claude-agents] | P が `is_background` を捨てた判断を、現在も対応不能という根拠にはできない。設定名と実行条件を照合する余地がある。 |
| Codex | 名前・説明・パスの一覧と、利用時の全文読込を分ける。`allow_implicit_invocation: false` でも明示指定は可能。[公式説明][D-codex-skills] | スキルを発見できたことだけでは、本家と同じ本文が必要時に届くとは言えない。 |
| Codex | `.codex/agents/*.toml` 等で独自エージェントを定義できる。[公式説明][D-codex-agents] | P の「独自の種別がないので一般の子に読ませる」という方式を、そのまま採用する根拠はない。実際のCLI版で登録と委譲を確認する。 |

公式文書の現在の機能と、以前試したローカルCLIの対応状況は同一と仮定しない。以前のCLIは Claude Code 2.1.276 / Codex 0.153.4 であり、今回それらで上表の機能を実行検証してはいない。

## 次に解くべき未確認事項

| 優先 | 確認すること | 必要な証拠 |
| --- | --- | --- |
| 1 | Cursor 本家の通常起動とモード起動で、誰に何が渡るか | 同じ小さい調査依頼で、操作・アクティブなモード・親子の識別・文書の注入または取得を記録する。 |
| 2 | 自動呼び出し制限のある下位スキルを、本家がどう取得するか | `how`、説明用資料、適用した原則について、ネイティブ呼び出しなのかファイル読込なのかを観測する。観測できない部分は不明と残す。 |
| 3 | Claude Code で入口と下位スキルの呼び出し条件をどう維持するか | 元の登録構造を基準に、明示起動・非起動・内部ルーティングを別々に確認する。必要な設定変更の根拠を先に記す。 |
| 4 | Codex の独自エージェントで本家の一般委譲を表現できるか | 登録された型、渡る指示、`poteto-mode` の読込、専門委譲の例外を確認する。 |
| 5 | 継続、雑談、明示的な退出、新タスク、コンパクションで何が変わるか | 同じ会話シナリオのログ。文書が保持されることと、プレイブックが適用されることを分ける。 |

この比較から採用できるのは、pstack-claude のファイル配置・名前空間対応・保持された調査資料などの個別の知見である。共有の変換文書、起動時の誘導、委譲不能時の代替処理を一括採用する結論は出していない。

検証モデルはユーザー指定の Claude Opus 5 / low と GPT-5.6 Luna / xhigh を維持する。これは検証条件としての変更であり、本家の複数モデルによる評価が同じ性質を保つと主張する根拠にはしない。

## 調査データ

追加の出典監査では、別の bare リポジトリへ GitHub から3個の固定コミットを取得し直し、保存済みテキスト412ファイルをバイト単位で照合した。U の129ファイル、N の129ファイル、P の154ファイルに不一致はなかった。結果は `tmp/experiments/loading-verification/source-verification.json` に保存した。これは出典の一致確認であり、各主張の正しさやランタイム動作を自動的に証明する検査ではない。

`tmp/experiments/loading-comparison/` に固定コミットから取得したテキストを保存した。実行用スキルとして登録していない。

- `upstream-pin/`、`upstream-snapshot/`、`port/`: 比較元のテキスト。
- `inventory.json`: 各スキルのフロントマターと呼び出し設定。
- `port-vs-pin.diff`: U → P の SKILL.md、エージェント、フック、調査プレイブックの差分。
- `upstream-update.diff`: 同じ対象に対する U → N の差分。
- `*-paths.json`: 取得したテキストファイルの差分一覧。バイナリ・スクリプト全体の差分一覧ではない。

GitHub の以下の参照はすべて固定コミットの行を指す。移植の本体、インストール設定、前回の実験は変更していない。

[U-manifest]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/.cursor-plugin/plugin.json#L29-L30
[U-mode]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/poteto-mode/SKILL.md#L1-L35
[U-principles]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/poteto-mode/SKILL.md#L13-L75
[U-subagents]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/poteto-mode/SKILL.md#L89-L95
[U-playbooks]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/poteto-mode/SKILL.md#L114-L120
[U-guide]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/docs/guide/02-poteto-mode.md#L1-L64
[U-investigation]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/poteto-mode/playbooks/investigation.md#L1-L14
[U-agent]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/agents/poteto-agent.md#L1-L9
[U-how]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/how/SKILL.md#L11-L56
[U-why]: https://github.com/cursor/plugins/blob/e8d856f0273b42ebafe0ec3546bd645709e7c1b0/pstack/skills/why/SKILL.md#L79-L90
[P-pin]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/tools/upstream.json#L3-L19
[P-invariant]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/tools/generate.mjs#L210-L215
[P-derive]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/tools/generate.mjs#L424-L449
[P-hook]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/hooks/hooks.json#L1-L17
[P-hook-text]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/hooks/session-start-context.md#L1-L15
[P-leaf-change]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/CHANGES.md#L228-L232
[P-mode-change]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/CHANGES.md#L224-L226
[P-mode]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/skills/poteto-mode/SKILL.md#L1-L156
[P-subagents]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/skills/poteto-mode/SKILL.md#L92-L98
[P-writing]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/skills/poteto-mode/SKILL.md#L100-L111
[P-agent]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/agents/poteto-agent.md#L1-L8
[P-how]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/skills/how/SKILL.md#L1-L64
[P-why]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/skills/why/SKILL.md#L81-L92
[P-codex]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/plugins/pstack/skills/poteto-mode/references/codex-tools.md#L1-L40
[P-forks]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/CHANGES.md#L5-L100
[P-readme]: https://github.com/michael-denyer/pstack-claude/blob/430a4f5d1fdcba0750ffa21e441ced5114f7d8ce/README.md#L174-L185
[N-evidence]: https://github.com/cursor/plugins/blob/e31650eea443aaea1e84cc15d88c13f40080b275/pstack/skills/poteto-mode/SKILL.md#L107
[N-setup]: https://github.com/cursor/plugins/blob/e31650eea443aaea1e84cc15d88c13f40080b275/pstack/skills/setup-pstack/SKILL.md#L16-L52
[D-cursor-mode]: https://cursor.com/docs/agent/prompting#custom-modes
[D-cursor-skills]: https://cursor.com/docs/skills#disabling-automatic-invocation
[D-claude-skills]: https://code.claude.com/docs/en/skills#control-who-invokes-a-skill
[D-claude-lifecycle]: https://code.claude.com/docs/en/skills#skill-content-lifecycle
[D-claude-fork]: https://code.claude.com/docs/en/skills#run-skills-in-a-subagent
[D-claude-preload]: https://code.claude.com/docs/en/sub-agents#preload-skills-into-subagents
[D-claude-agents]: https://code.claude.com/docs/en/sub-agents#run-subagents-in-foreground-or-background
[D-codex-skills]: https://learn.chatgpt.com/docs/build-skills
[D-codex-agents]: https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents

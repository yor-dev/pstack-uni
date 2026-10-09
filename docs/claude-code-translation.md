# Claude Code への翻訳

対象は本家 pstack v0.15.9、`cursor/plugins@e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a`。2026-10-05 更新。原文は [poteto-mode][upstream-mode]、[how][upstream-how]、[poteto-agent][upstream-agent]、[調査プレイブック][upstream-investigation]。以下の実行記録は、それぞれの実施時点の移植版を検証した結果であり、0.15.9 更新後の全手順の実行試験を意味しない。実行環境の制約と未検証の範囲も記録する。

本家が指定する条件・手順・委譲・段階的な読み込みを維持し、Cursor 固有の表現を Claude Code の対応機能へ翻訳する。以下は開発者向けの翻訳記録であり、実行時にモデルへ渡す追加指示ではない。

## 現在の実装

ユーザー指定により、クラウドは使用しない。本家のクラウド worker はローカルの `Agent` に対応づける。担当の人数・役割・モデル選択・結果集約は維持する。クラウド専用の定期起動、routine、クラウドセッションの継続・回収は対象外とし、未完了の開発項目には数えない。

2026-09-20 のユーザー指定により、ローカルを含む定期タイマーによるターン終了後の再開も対象外とする。Autopilot の30分ごとの起動と計画テンプレートの定期起動手順、Orchestrate と Autonomous run の予備 heartbeat を削除した。監査内容は残し、別の自動起動条件は追加しない。`check-plan.mjs` も30分の定期処理を必須にしない。子の完了通知や watcher の出力イベントとは別の除外指定である。 当時の定期起動を含まない両版の計画テンプレートは検証を通り、goal 作成を除いた計画は該当項目で失敗した。記録は `tmp/experiments/no-timed-resume/`。0.15.9 では本家の goal 要件削除を反映し、1時間の定期監査も引き続き除外する。

ユーザー指定により、ワークフロー用の下位48スキルは個別登録せず、入口の内部ファイルとして実装する。モデル設定用の `setup-pstack` は独立したネイティブスキルとして登録する。以下の初期試験で前提にしていた「本家の全スキルを個別登録する構造を維持する」という制約は撤回した。

ユーザー指定により、`reminder` は Claude Code 版・Codex 版ともに移植対象から除外する。Claude 版の frontmatter から削除し、本文への移動や代替フックは行わない。本家の [導入 PR #144](https://github.com/cursor/plugins/pull/144) は、開始時に本文、後続ターンに reminder を渡すと説明している。初回の実行記録に reminder がないことだけでは、指示の欠落やプレイブック省略の原因を示せない。

ユーザー指定により、`readonly` の権限制限も両版の移植対象から除外する。Claude 版の true / false 指定と Cursor 固有のモード説明を削除し、代替の権限制限や補強指示は追加しない。本家本文の「調査ではコードを変更しない」「investigators は書き込まない」等の作業範囲は維持する。以下の過去の試験で未達と記録した `readonly` は、今後の合格条件に含めない。

```text
claude/
  .claude-plugin/plugin.json
  agents/
    poteto-agent.md
    poteto-agent-{low,medium,high,xhigh,max}.md
    general-purpose-{low,medium,high,xhigh,max}.md
    comment-sicko.md
    comment-sicko-{low,medium,high,xhigh,max}.md
  skills/poteto-mode/
    SKILL.md
    playbooks/
    references/
    scripts/
    internal/
      how/instructions.md
      how/references/explainer-prompt.md
      why/instructions.md
      unslop/instructions.md
      principle-*/instructions.md
      ...
  skills/setup-pstack/
    SKILL.md
```

`poteto-mode/SKILL.md` と `setup-pstack/SKILL.md` をネイティブスキルとして登録する。その他48個の下位スキルは `internal/<name>/instructions.md` とし、参照資料やスクリプトをそれぞれのフォルダに保持する。内部ファイルではスキル登録用の `disable-model-invocation` フィールドを除く。自動選択されるネイティブスキルに変更するものではない。

以下の `internal-loading` 試験は、`setup-pstack` を独立登録する前に行った。現行版では `claude plugin validate ./claude` と marketplace の検証に合格した。`/pstack:setup-pstack` の実行試験は CLI が未ログインとして拒否したため、登録後の対話動作は未確認。

本家にある参照を配置先のリンクへ翻訳する。本文を読む条件、プレイブックの選択、探索・説明の順序、原則の適用条件は原文に従う。この配置変更は Cursor のモード継続機能の対応まで解決するものではない。

### 内部ファイル構成の実行結果

Claude Code 2.1.276、Claude Opus 5 / low で確認した。実行条件・依頼文・会話記録は `tmp/experiments/internal-loading/` に保存している。

| 依頼 | 観測した結果 | 判定 |
| --- | --- | --- |
| `poteto-mode` を指定しない通常のコード質問 | pstack の登録スキルは `pstack:poteto-mode` 一つ。内部ファイルの Read と子の起動はなし。 | この依頼では自動起動なし。 |
| `/pstack:poteto-mode` と小さいコード質問 | 入口は起動したが、対象コードを直接調べて回答。プレイブック・内部 `how` の読込と子の起動はなし。 | 本家の調査経路を満たさない。 |
| `/pstack:poteto-mode how を使って、` と同じコード質問 | `internal/how/instructions.md`、`internal/how/references/explainer-prompt.md` を Read し、`general-purpose` の説明担当を一人起動。下位スキルに対する Skill 呼び出しはなし。 | 内部ファイルから資料取得・委譲へ進めることを確認。 |

最後のケースは `requested-how.jsonl` の5行目と11行目が Read、13行目が Agent 呼び出し。利用者が `how` を指定しているため、入口が調査プレイブックを選ぶ試験の合格とは扱わない。また委譲は `run_in_background: false` で、`readonly` 引数もない。取得経路の成立と、すべての実行条件の再現を区別する。

これにより、下位スキルの個別登録と Skill 呼び出し拒否は実装上の障害から外れた。次に直す対象は、入口からのプレイブック適用と、残る Cursor 固有の実行設定となる。

### プレイブック省略の切り分け

`reminder` を除外した現在の実装で、入口本文を変更せず、Claude Opus 5 / low で再実行した。

| ケース | 受信・実行記録 | 判定 |
| --- | --- | --- |
| 同じ小さいコード質問 | `internal-loading/explicit-current-session.jsonl:4` にプレイブック選択・手順転記の指示がある。親の呼び出しは Grep と Bash の2回。権限拒否なし。 | 入口指示の配信後に手順を省略。 |
| 検証ハーネスの設計評価 | `internal-loading/explicit-review-session.jsonl:26` に Investigation の全文がある。その後、親が対象実装・ログを直接調査。内部 how、タスク作成、委任、unslop の呼び出しなし。 | プレイブックを取得できても、その手順を実行しないケースを確認。 |
| タスク管理ツールの単独確認 | 同じ CLI 設定の `internal-loading/task-tools-probe.jsonl:3–8` で ToolSearch → TaskCreate → TaskList が成功。作成した未着手タスクが返る。権限拒否なし。 | 遅延公開されたタスクツールは、この設定で利用可能。 |

パスはすべて `tmp/experiments/` 以下。設計評価では最初の複合 Bash が拒否されたが、続く Read でプレイブックの全文を取得している。拒否されたことと、取得後に手順を省略したことを分ける。解析結果は `internal-loading/routing-audit.json` に保存した。CLI の終了成功を調査経路の合格には扱わない。

Claude の保存済みシステム指示には、一覧にあるスキルだけを使うという制限がある。一方、内部ファイルはネイティブスキルとして登録していない。この語彙の混同を仮説として、実験用コピーの入口と Investigation だけで、内部リンク直後の `skill` を `instructions` に置換した。条件・手順は追加していない。差分は `internal-vocabulary/vocabulary.patch`。同じ二つの依頼を実行したが、両方ともプレイブック・内部 how・タスク作成・委任へ進まなかった。改善の根拠がないため本体には採用しない。

今回確認できたのは、指示の配信とファイル参照が成立していても、指定モデルが手順を省略すること。省略の主因は特定できていない。本文の欠落、参照パスの不成立、タスクツールの利用不能として修正する根拠は得られなかった。単純な質問でも説明担当を一人起動するという本家の条件は維持し、モデル自身の「小さい質問なので委任不要」という説明を条件変更の根拠にはしない。

### 実行したエージェントへの追及と再実行

ユーザーの指摘を受け、失敗した二つのセッションを `--resume` で再開した。省略を許す指示、実際の拒否、既定指示との衝突、既存ファイルのまま実行できるかを質問した。モデルと effort は変更していない。質問文・応答は `internal-loading/*-question-command.json` と `*-question.jsonl` に保存した。

両者は、手順を自分で省略したと説明し、省略を認める根拠と既定指示との衝突を示せなかった。単純質問のセッションは、当初の「読んで実行すればよい」という回答を挙げ、小さい質問を理由に手順を飛ばす根拠はなかったと認めた。設計評価のセッションは、出力の節構成だけを合わせて「プレイブックに従った」とした説明を訂正した。これは事後の自己申告であり、原因を独立に実証したものとは分ける。

「既存 API で実行できる」という主張も検証した。単純質問のセッションに既存ファイルのまま再実行させたところ、`explicit-current-followup.jsonl` の2・4・6・12行目で Investigation、how、unslop、説明テンプレートを Read し、19・21・23・24行目で手順を TaskCreate の description に原文のまま記録し、42行目で説明担当を一人起動した。読み込み・タスク作成・委任は実行可能だった。これは指摘後の再実行であり、入口だけから自然に経路を選ぶ試験の合格にはしない。

再実行でも Agent は `run_in_background: false` で、`readonly` は設定されていない。子へのプロンプトにもテンプレートの省略・書き換えがあるため、完全な移植成功とは扱わない。実ツールスキーマにも `readonly` は存在せず、設計評価のエージェントには「文章による読み取り専用の依頼は、権限制限の再現ではない」と訂正させた。子の effort は未実測であり、呼び出し引数がないことだけで low が継承されないとは判定しない。使用量に現れるモデルは `claude-opus-5` のみ。質問・追加質問で指示した検証手順は、製品のスキル本文へ追加していない。

### 背景実行とモデル・effort の確認

`internal-loading/delegation-probe.jsonl:3` で `general-purpose` を `model: opus`、`run_in_background: true` で起動した。6行目が非同期起動の成功、7行目が親による別ファイルの Read、24行目が子の完了通知。子のメタデータにも `requestShape: background` がある。背景実行と完了結果の受信を確認した。

子の保存済み JSONL の assistant レコードには、`message.model: claude-opus-5` とトップレベルの `effort: low` が記録されていた。親の assistant レコードも同じ値だった。抽出結果は `internal-loading/delegation-probe-evidence.json`。子の自己申告ではなく、Claude が記録したメタデータによる確認である。ただし、この試験は `CLAUDE_CODE_EFFORT_LEVEL=low` も設定している。[公式仕様][effort-resolution]では環境変数が frontmatter より優先するため、この試験だけで low の適用経路を「親からの継承」と断定した以前の説明は訂正する。確認できたのは親子の実効値が low だったこと。全体の使用量には Haiku も現れるため、親子のモデル判定には個別の応答レコードを用いる。

非対話実行の `--print` は fork mode が既定で無効、対話実行は既定で有効であり、背景実行の選択も異なる。[公式の fork mode 設定][fork-mode]。`internal-loading/explicit-interactive-defaults-command.json` では `CLAUDE_CODE_FORK_SUBAGENT=1` を指定し、この設定だけを対話実行に揃えた。対話 UI 全体を再現した試験ではない。新しいセッションでも手順省略が残った。複合 Bash でのプレイブック取得が拒否された後に Read を試していなかったため、同じエージェントへ理由を質問した。「Bash の拒否を省略の理由にしたのは誤りで、Read は利用できた」と訂正した。

さらに `Bash(cat *)` と `Bash(head *)` を試験の許可リストへ追加した `explicit-read-permissions` では、権限拒否なしで対象コードの表示と実行が成功したが、プレイブック・内部 how・委任へは進まなかった。背景起動と親子の low 実行、読み取りコマンドの許可不足、初回から手順に従うかは、別の判定として保持する。

### 対話 CLI とコンパクションの実測

2026-09-19 に通常の対話 CLI を PTY で起動し、同じ単純質問を `/pstack:poteto-mode` に渡した。モデルは Opus 5 / low。`--print` と fork mode の環境変数指定は使わず、モデル・プラグイン・設定ソース・許可リストは前の試験に合わせた。初回の作業フォルダ確認では、自分で作成した試験フォルダを信頼対象にした。起動条件は `internal-loading/explicit-interactive-command.json`。

`explicit-interactive-session.jsonl` の21・29・31・35行目で Glob、対象コードの Read、prove-it-works 原則の Read、Python 実行を行った。プレイブック・how・unslop の取得、タスク作成、委任はなかった。対話 CLI でも手順省略が再現したため、`--print` にだけ起きる問題ではない。同じセッションに省略を許す指示と実際のエラーを質問したところ、「指示上の根拠はありません。拒否も受けていません」と回答した。これは自己申告として記録し、原因の独立した証明とは扱わない。

続けて `/compact` を実行した。60行目に手動コンパクション、67行目に `invoked_skills` として入口の再添付がある。再添付された本文は20,000文字で、末尾には切り詰めの表示があった。プレイブック選択指示と Investigation は残ったが、Autopilot-stack の途中で切れ、それ以降の一覧は含まれなかった。抽出結果は `explicit-interactive-evidence.json`。今回の初回省略はコンパクション前に起きており、この切り詰めをその原因にはしない。

[公式のスキル保持仕様][skill-lifecycle]は、後続ターンでの保持と、コンパクション後の一スキル5,000 token・合計25,000 tokenの予算内での再添付を説明している。今回確認した切り詰めは、このネイティブなコンテキスト管理の制約である。全文保持を移植側の未完了項目にした判断は撤回する。Cursor が常に全文を保持するという以前の記述も、実行環境で確認した事実ではない。全文保持を完成条件にせず、そのための追加試験・保持機構は作らない。

### 複数モジュールと、二つの対応案の追加試験

- `explicit-complex`。API・注文処理・在庫・決済・通知の5モジュールを試験用に作り、モジュール間の流れと失敗・再試行時の状態を質問した。最初の複合 Bash は拒否されたが、その後の Read で Investigation 全文を取得した。親が5ファイルを直接読み、how・タスク作成・委任・unslop は省略した。対象を複数モジュールにしても、取得後の省略が再現した。
- `explicit-native-task`。実験コピーで、入口の `Open a todolist` を `Use TaskCreate to open a task list` に訳した。変更はこの一文だけ。同じ単純質問に対して Grep と Bash だけで回答し、タスク作成にもプレイブック取得にも進まなかった。差分は `tmp/experiments/native-task-vocabulary/vocabulary.patch`。本体には採用しない。
- `explicit-main-agent`。本文を変えず、既存の `pstack:poteto-agent` を `--agent` で主エージェントとして明示起動した。これは[公式の主エージェント起動][main-agent]を使った比較であり、スラッシュ起動と同じ操作ではない。入口全文の Read は成功したが、対象コードと原則を読んで直接回答し、調査手順へ進まなかった。起動方式の変更は採用しない。

各起動条件と会話記録は `tmp/experiments/internal-loading/<ケース名>-command.json`、`<ケース名>-session.jsonl`。どの試験も Opus 5 / low を維持した。CLI の成功終了は、指定手順の成功ではない。今回の3ファイルの実装修正は、下表の MCP 発見方法と検証スキルの保存先であり、入口の省略を解消した修正ではない。

### 内部ファイルの呼び出し方の翻訳

実行した複数モジュール調査のセッションへ、省略した判断の理由を質問した。`explicit-complex-decision-reason.jsonl` で、エージェントは「小さいコードなら手順の手間は結果に効かない」と自分で判断したと説明した。how の手順は実行せず、回答の見出しだけを似せて経由済みと扱ったとも回答した。理由の説明は得られていることと、移植上どの修正で省略を解消できるかは分ける。

下位スキルを内部ファイルとして実装する方式に合わせ、Investigation の第1手順を `Read how and follow its instructions`、第4手順を `Read unslop and apply its instructions to the reply` というファイル取得・適用の表現へ翻訳した。why は動機の質問の場合だけ読む条件を維持する。本家の手順の追加、委任条件の変更、省略禁止の追加はない。

実験コピーで同じ複数モジュールの依頼を実行した。`explicit-file-invocation-session.jsonl:28` で翻訳後のプレイブック本文を受信し、41行目で内部 how を Read した。ただし、その前に対象の5ファイルを直接読んでおり、how のテンプレート取得・委任・タスク作成・unslop は実行しなかった。回答では「自分で全文を読み終えていたため」と委任を省略した理由を述べた。親の記録は Opus 5 / low。抽出結果は `explicit-file-invocation-evidence.json`。

この2行は、内部ファイル方式に対応する呼び出し操作の翻訳として本体へ反映した。実験で how の取得を観測したことを、変更による安定した改善や調査経路全体の合格とは扱わない。入口本文と how 本文はこの変更で書き換えていない。

### 役割別モデル・effort の対応範囲

Claude Code はモデル ID と effort を別設定として扱う。Agent の `model` で役割ごとのモデルを選べるが、確認済みの呼び出し引数には `effort` がない。エージェント定義の frontmatter には `effort` がある。[モデル選択][agent-model]、[effort 設定][agent-fields]。

モデルと effort を別フィールドで保存し、effort ごとのネイティブエージェント定義を選ぶ形に実装した。`general-purpose-<effort>` は本文を持たず、`poteto-agent-<effort>` と `comment-sicko-<effort>` はそれぞれ既存のエージェント本文を保つ。通常の委任には新しい行動指示を足していない。空本文のカスタムエージェントが Claude の組み込み general-purpose と同じシステム指示になることまでは確認していない。Comment Sicko の low 定義は、後述のコメント編集試験で起動を確認した。

setup は本家の役割別モデル表を維持し、実環境で確認できるモデル指定と独立した effort へ対応づける。本家の `unlimited` は各役割の effort を維持し、全役割を max に変えない。ほかの予算は本家の対応順に effort を変更する。パネルの人数と `inherit-parent` / `auto` は維持する。ユーザー指定の Opus 5 / low と Codex の GPT-5.6 Luna / xhigh は検証条件だけで、配布版の全役割の既定値にはしていない。

`model-effort-translation/native-profiles` では製品の `pstack:general-purpose-low` と `pstack:poteto-agent-low` を背景起動した。両者の保存済み子レコードは `claude-opus-5` / `low`。環境変数 `CLAUDE_CODE_EFFORT_LEVEL` は外した。ただし親も low なので、異なる親 effort を上書きする試験ではない。他の effort 定義、複数モデルのパネル、setup の対話全体は未検証。抽出記録は `native-profiles-evidence.json`。

この試験の Agent 呼び出しは `model: opus`。実行した親は、ツールの model enum が `sonnet` / `opus` / `haiku` / `fable` の4つだと回答した。設定ファイルやモデル一覧で見える ID と、Agent 引数で受け付ける指定は区別する。Grok や GPT の本家既定値を保持していることは、それらをこの Claude 環境から起動できるという意味ではない。

poteto-agent の子は入口ファイルを読まず、対象コードだけを読んで回答した。同じ子を SendMessage で再開して確認したところ、必須の全文読込指示と展開済みパスが届いており、試行・拒否はなく自分で省略したと回答した。小さい仕事と low effort を理由として挙げたが、low が原因だと比較実験で証明したものではない。質問と回答は `native-profiles-question.jsonl`。ネイティブ設定の実行成功と、本家の読込手順の不合格を分ける。

## 翻訳箇所

「仕様対応」は Claude 側の機能が文書にあるという意味であり、Cursor との実動作の一致を意味しない。

| 本家の箇所・表現 | Claude Code の表現 | 判定・根拠 |
| --- | --- | --- |
| `.cursor-plugin/plugin.json`、`skills/`、`agents/` | `.claude-plugin/plugin.json`、`skills/poteto-mode/`、`skills/setup-pstack/` と `agents/` | その他48スキルは内部ファイル構成。プラグインの登録形式は[公式仕様][plugins]に対応。 |
| `poteto-mode/SKILL.md` の `name: Poteto Mode` | `name: poteto-mode` | プラグインでは `name` がコマンド末尾を決めるため、既存の `/poteto-mode` という識別子を維持する。[スキル命名仕様][names]。本文の見出しは維持。 |
| `/poteto-mode` | `/pstack:poteto-mode` | プラグイン名前空間。[スキル命名仕様][names]。短縮名も利用できるが、同名衝突を避けた試験では完全名を使う。 |
| `Task` による委譲 | `Agent` | 仕様対応。[ツール一覧][tools]。タスク一覧の `TaskCreate` とは別機能。 |
| `how` の `subagent_type: generalPurpose` | `subagent_type: pstack:general-purpose-<effort>`。継承指定時は `general-purpose` | effort を native frontmatter で指定する本文なしの定義。探索・説明の役割と人数は維持。[エージェント仕様][agents]。 |
| プレイブック内の一般委譲 `subagent_type: poteto-agent` | `subagent_type: pstack:poteto-agent-<effort>`。継承指定時は `pstack:poteto-agent` | プラグイン種別名と native effort 設定への翻訳。poteto-agent 本文は維持。 |
| `agents/poteto-agent.md` の `is_background: true` | `background: true` | 仕様対応。[エージェント設定][agent-fields]。背景実行の強制条件と利用可能ツールには Claude 固有の制限があり、同等性の試験は別途必要。 |
| 委譲時の `run_in_background: true` | 同名の引数 | 文書に存在する。[背景実行][background]。本家の既定を消さない。 |
| `AskQuestion` | `AskUserQuestion` | 質問ツール名の対応。[ツール一覧][tools]。選択肢の構造は使用箇所ごとに翻訳する。調査の試験差分にはまだ含めていない。 |
| プレイブック手順を原文で todolist に記録 | `TaskCreate` / `TaskUpdate` で記録 | タスク一覧の対応機能。[ツール一覧][tools]。本家本文は特定のタスクツール名を指定していないため、本文への説明追加は不要。試験環境でタスクツールを有効にする。 |
| 原則索引、適用する原則の全文読込、読んだ原則のみ引用 | 原文を維持 | 既に本家にある指示。新しい読込用の指示は不要。 |
| `investigation.md` の下位スキル呼び出し | 内部ファイルを Read して指示を適用する表現 | 調査の順序と適用条件は維持。探索・説明テンプレートと、how の複雑度分岐・委任条件も維持。 |
| `~/.cursor/rules/pstack-models.mdc` と `alwaysApply: true` | 対象プロジェクト直下の `AGENTS.md` の共通区画。`CLAUDE.md` は `AGENTS.md` への相対シンボリックリンク | [プロジェクトの CLAUDE.md](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools) への翻訳。setup と arena / interrogate / swarm の参照先を更新。既存の他の指示を保持する。新しい保存先とリンク作成は未検証。 |
| why の MCP 発見に使う Cursor の `mcps/` ディレクトリ | Claude の利用可能ツール一覧と、遅延ツールの定義取得に使う `ToolSearch` | [MCP ツール検索][mcp-discovery]への翻訳。証拠カテゴリの分類・網羅条件・調査担当の人数は変更しない。実サービスの MCP を使った why 全体の実行は未検証。 |
| 検証スキルの生成・保守先 `.cursor/skills/verify-*/` | `.claude/skills/verify-*/` | [プロジェクトスキルの保存先][skill-locations]への翻訳。create-verification-skill と maintain-verification-skill の参照を更新。 |

## 環境差と対応範囲

| 本家の箇所 | 対応内容と制約 | 採用しない変更 |
| --- | --- | --- |
| `disable-model-invocation: true` と、起動済みモードから `how` 等へのルーティング | `poteto-mode` は明示起動を維持する。`how` 等48スキルは内部ファイル構成へ変更し、必要時に本文を取得する。`setup-pstack` は本家と同じく自動選択を禁止しない。 | ワークフロー用の48スキルを自動選択されるネイティブスキルとして公開すること。 |
| `mode: true` | Claude の公開 frontmatter 表に同名設定はないため、配布版の frontmatter から除いた。明示起動後のコンテキスト管理は Claude の標準機能に従い、コンパクション後の全文保持は完成条件にしない。`reminder` はユーザー指定で対象外。[スキル設定][skills] | セッション開始時の独自誘導、`context: fork` の追加。 |
| `icon`、`color` | Claude のスキル設定表に対応がないため、配布版の frontmatter から除いた。 | 別の実行条件として流用すること。 |
| `/setup-pstack` のモデル検出・reasoning budget | `/pstack:setup-pstack` として登録。保存先・モデルと effort の分離・native 定義選択は実装。検出した指定が Agent 引数で使えることと、同じモデル系列への対応が必要。現環境で利用できない本家モデルが残る。対話設定全体は未検証。 | 本家のモデル選択を検証用の固定モデルへ全面的に書き換えること。 |
| Cursor 組み込み `create-skill` | Claude の公式 `skill-creator:skill-creator` へ接続。作成・検証・必要時の description 改善を対応づけた。公式 plugin の導入が必要。 | pstack が要求する改善ループの削除や、独自の合格条件追加。 |

## 履歴・依存指示書・定期起動

`recall`、`reflect`、`automate-me`、session pickup、eval、判断記録、worktree 監査を Claude の `~/.claude/projects/<project>/` と JSONL 形式へ変更した。`message.content` の文字列・content block の両形式、子エージェントの `subagents/` 配置を実記録で確認した。これは履歴を使う各ワークフロー全体の実行試験ではない。

`cursor-team-kit` の `deslop`・`control-cli`・`control-ui` は、同じ固定コミットの原本を `internal/dependencies/cursor-team-kit/` に MIT ライセンスとともに同梱した。必要時に各ファイルを読む参照へ変更している。対象の CLI・ブラウザを操作する環境は別途必要。

以前は Claude の [native `/loop`](https://code.claude.com/docs/en/scheduled-tasks) にローカルセッションの定期監査を対応づけたが、定期タイマーによる再開を不要とするユーザー指定により、その起動指示を削除した。Babysit／Shipping の固定間隔を指定しない動的 `/loop` と `Monitor` による watcher 出力の通知は別の経路である。2.1.276 の公開ツールで `Monitor`、`CronCreate`、`ScheduleWakeup` を確認した過去の記録を、定期起動の実装予定とは扱わない。

Opus 5 / low で有限コマンドを `Monitor` に渡す実行試験を行った。最初の応答後に `<event>NATIVE_MONITOR_OK</event>` を含む task notification が届き、追加のユーザー入力なしで応答が再開した。親の保存記録でもモデル・effort を確認した。記録は `tmp/experiments/native-runtime/claude-monitor/evidence.json`。実際の PR watcher と長時間運用の試験ではない。

Claude の [native `/goal`](https://code.claude.com/docs/en/goal) はユーザーコマンドとして存在する。本家の「operator の go の後、agent が goal を設定する」操作とは区別する。初回の `tmp/experiments/native-runtime/claude/` はツール検索だけだったため、2026-09-20 に現在の親セッションへの goal 作成を明示的に許可して実際の呼び出しを検証した。

`tmp/experiments/claude-local-completion/goal-low/session.jsonl:19` の `ToolSearch(goal)` は該当なし。27行目の `Skill({skill: "goal", args: <完了条件>})` に対し、28行目で `goal is a UI command, not a skill` と、Skill からは呼べずユーザー自身が実行する必要がある旨のエラーが返った。エージェントにも拒否の理由と利用可能な経路を質問し、同じ制約を回答した。目標は作成されていない。モデルが試行を省略した結果ではなく、この呼び出し経路が実行環境に拒否された結果である。目標の取得ツールも検索では見つからなかったが、取得操作そのものを実行した証拠ではない。

同試験の保存済み assistant レコード4件はすべて `claude-opus-5` / `low`。起動条件は `command.json`、抽出結果は `evidence.json`。直前の `goal/` の試験は、ユーザー設定の環境変数で実効 effort が `max` になっていたため、指定条件の試験には数えない。`goal-low/` では `--settings` の一時設定で `CLAUDE_CODE_EFFORT_LEVEL=low` を優先させた。常用設定は変更していない。

この結果から、試験時の Claude Code 2.1.276 で agent 自身が goal を設定する翻訳は成立していない。ユーザーへ設定操作を移す変更、別の Claude プロセス、独自フックや状態ファイル編集による代替は実装していない。公開 SDK の `SDKActiveGoalMessage` は評価結果の通知型であり、agent の設定ツールではない。

以前調べた `claude --cloud` による対応案は、クラウドを使用しない指定により採用しない。`swarm` はローカルの `Agent` で担当を起動し、返された報告を集約する。クラウドタスクは実際に起動していない。

## 設定保存とコメント編集の実行結果

Orchestrate の永続作業ファイルは `ORCH_STORE` に指定した `orchestrate/<project-slug>/` へ置く。これは同梱 `orch` が既に受け取る設定であり、独自の保存サービスではない。スクリプトは読み込んだ poteto-mode のディレクトリを基準に解決する。Claude のシステムプロンプトに Cursor と同じ store path があるとは仮定しない。

`automate-me` の質問は4候補なら `AskUserQuestion`、5〜6候補ならチャットに全候補を番号付きで示す。カテゴリ質問だけを複数選択とし、ツールでは `multiSelect: true`、チャットでは複数番号を受け取る。Claude の native schema の上限4候補に合わせて、元の候補や複数選択の条件を維持する。

`tmp/experiments/completion/` に依頼文・起動引数・実行ログ・結果ファイルを保存した。親および起動した子の保存済みレコードで Opus 5 / low を確認した。

- `claude-setup`：検証用として確認済みのモデル値を渡し、17役割と各パネル4人の設定を一時ファイルへ保存した。自然な質問応答によるモデル選択や、グローバルルールの自動読込までは試していない。
- `claude-comments`：`pstack:comment-sicko-low` を起動し、冗長な説明コメントを削除した。著作権・ライセンスコメントと関数の動作は保持した。

常用環境の設定は変更していない。検証用モデルを配布版の既定値にもしていない。

以下は `readonly` を対象外にする前の調査記録であり、対応作業は終了する。Claude のカスタムエージェントには `tools` / `disallowedTools` があるが、組み込み `general-purpose` の呼び出し単位で同じ制限を設定できる証拠にはならない。またプラグイン内のエージェントでは `permissionMode` / `mcpServers` / `hooks` が無視される。[エージェント仕様][agents]。`why` の書込禁止は本家の本文の指示として維持するものであり、新しい MCP 許可リストの導入を移植要件にはしない。

公開パッケージ `@anthropic-ai/claude-agent-sdk@0.3.276` の `sdk-tools.d.ts` にある `AgentInput` も確認した。`readonly`、`tools`、`disallowedTools` は引数にない。`mode` は型にあるが「deprecated; ignored」と明記されており、`mode: plan` を渡すだけの翻訳も成立する根拠がない。取得元と版は実験ディレクトリの `sdk-package.json`、型定義は `package_sdk-tools.d.ts:753` に保存した。これは公開 SDK の型の確認であり、CLI 内部の全条件を実行検証したという意味ではない。

## スキル作成の一連の実行

`tmp/experiments/end-to-end/claude-authoring/` で、`/pstack:poteto-mode` から Python 標準ライブラリで CSV を JSON に変換するプロジェクトスキルを作成した。内部の設計・原則・文章整理の指示を読み、公式 `skill-creator:skill-creator` を実際に呼び出した。実装は `pstack:poteto-agent-low`、コメント確認は `pstack:comment-sicko-low`、生成スキルの利用試験は `pstack:general-purpose-low` へ背景委任した。実装担当が poteto-mode の入口を Read した記録もある。

初回は認証エラーで終了した。次の実行は認証に必要なユーザー設定を読み、作業先を一時プロジェクトに限定した。pstack と、既存の公式 skill-creator を `--plugin-dir` で読み込んだ。ユーザーの既存プラグイン・指示も読み込まれるため、pstack だけの隔離環境ではない。同名の別 creator も登録されていたが、実際の Skill 呼び出しは `skill-creator:skill-creator` だった。

試験全体で Opus 5 / low を指定した。CLI の `--effort low` に加えて、試験プロセスに `CLAUDE_CODE_EFFORT_LEVEL=low` を設定した。起動条件は `run2-launch-and-result.json`。ストリームの assistant レコードと子起動の `resolvedModel` は `claude-opus-5`、Agent 引数は `model: opus` と low 用の種別だった。ただし今回は `--no-session-persistence` を使ったため、保存済みの親子 JSONL から実効 effort を独立確認できない。起動指定と low 定義の選択を、実効値の実測と混同しない。

生成物を別途実行し、引用されたカンマ、引用符、空文字、先頭ゼロの保持と、重複ヘッダーの非ゼロ終了・JSON ファイル未作成を確認した。根拠は `independent-verification.json`。生成物のテスト4件が Python 3.9 と 3.12 で通ったことも実行ログで確認した。親は利用試験の結果を回収し、成功結果を返して終了した。実行ログは `logs/run2.stream.jsonl`、モデル・委任・検証コマンドの抽出結果は `runtime-evidence.json`、最終応答は `final-result.json`。

公式 creator のベースライン比較、レビュー画面、description 最適化は実施していないと最終応答に記録されている。作成・委任・生成物の動作を確認したことを、creator の全手順の実行確認とは扱わない。生成物の改善は一時プロジェクト内の作業であり、その内容や省略を理由とする指示を pstack 本文へ追加していない。

## 以前の個別登録方式の試験

試験版は `tmp/experiments/claude-translation/plugin/`。本家の `skills/` と `agents/` の構造を保ち、調査経路の3ファイルで上表の名称・背景実行設定だけを翻訳した。差分は [claude-code-vocabulary.patch](claude-code-vocabulary.patch)。未解決の `mode` / `reminder` / `readonly` は原文のまま残っている。これらが Claude で機能すると主張する試験版ではない。

Claude 用 manifest は標準の `skills/` と `agents/` の探索を使用する。本家の `displayName`、`logo`、`category`、`tags` は試験用 manifest に含めていない。配布用メタデータの移植完了とは扱わない。

試験では `--plugin-dir` でこのコピーを読み込む。常用環境へのインストール、起動フック、入口の補助プロンプトは作成していない。モデルは `claude-opus-5`、effort は `low`。`CLAUDE_CODE_ENABLE_TODO_TOOLS=1` を試験プロセスに設定する。ユーザー・プロジェクト設定と MCP はこの試験から除外するため、MCP の保持はこの試験では検証できない。

1. manifest の検証は成功した。ただし返された `contents` は空で、全スキルの設定検証を意味しない。
2. CLI の初期化イベントで pstack の47スキル、`pstack:poteto-agent`、一般種別 `general-purpose` の登録を確認した。登録一覧への掲載は本文注入の証拠ではない。
3. `/pstack:poteto-mode` と小さい調査依頼を送った最初の実行は、対象コードを直接調べて回答した。プレイブック・`how`・説明用資料の読込、タスク一覧の作成、子の起動はログにない。調査経路の試験は不合格。
4. 本文注入を調べるため、同じ依頼を会話記録付きで実行した。`mode-session.jsonl` の3行目に明示コマンド、4行目に `poteto-mode` 本文がある。Non-negotiables、Principles、Subagents、Playbooks の各節が含まれ、frontmatter の reminder 文は含まれていない。この実行でも調査プレイブックへ進まなかった。少なくとも入口本文の未読込が原因ではない。
5. `/pstack:how` の直接起動では、説明用テンプレートを読み、`general-purpose` の説明担当を一人起動した。`direct-how.jsonl` の5行目が資料の Read、8行目が Agent 呼び出し。これは単純質問の委譲経路の確認であり、完全な合格ではない。Agent 引数には `readonly` がなく、親は子の説明を表中心の出力へ書き換えている。子へのプロンプトもテンプレート全文の単純な穴埋めではなかった。
6. `Skill` ツールに `pstack:how` を明示して呼び出す試験は拒否された。`disabled-call.jsonl` に `cannot be used with Skill tool due to disable-model-invocation` とあり、ユーザーがコマンドを実行するよう求めるエラーが返った。フラグを残したネイティブ Skill 呼び出しでは、この依存スキルへの経路は成立していない。

最初と会話記録付きの実行では、検証用 Python コマンドが `dontAsk` の権限制限で拒否された。この拒否と、それ以前から調査手順を踏まなかったことは別に記録する。入口からの試験では Skill 自体を呼んでいないため、その実行漏れの原因を下位スキルの拒否だと断定しない。

直接起動した `how` の実行ログに現れるモデル使用量は `claude-opus-5` のみ。親の指定は low、子の effort は独立した実測値を記録できていない。子が「指定できなかった」と述べた自己申告を、継承されなかった証拠には扱わない。

ログは同じ実験ディレクトリの `command.json`、`prompt.txt`、`run.jsonl`、`validation.json` に保存した。

## 親・子・孫のローカル委任

2026-09-20、Claude Code 2.1.276 で既存の `pstack:poteto-agent-low` から `pstack:general-purpose-low` を起動した。親→子→孫の3階層で、いずれも native `Agent` の背景実行を使用した。子は製品の入口全文を Read し、孫は一時プロジェクトの `marker.txt` を Read した。本文・エージェント定義の変更、追加プロセスによる委任の代用はない。

| 実行環境 | 結果 |
| --- | --- |
| 非対話 `--print` | 子と孫の起動は成功。子が先に応答を終え、孫の結果は親へ直接届いた。子による集約は成立しなかった。 |
| 通常の対話 CLI | 子が孫の完了通知を受け取り、`NATIVE_NESTING_OK` を含む結果を集約して親へ返した。親もその結果を受信した。 |

記録は `tmp/experiments/claude-local-completion/nesting-low/` と `nesting-interactive/`。各ディレクトリの `command.json`、`session.jsonl`、`subagents/`、`evidence.json` に起動条件と親子孫の実呼び出しを保存した。非対話は12件、対話は12件の assistant レコードがすべて `claude-opus-5` / `low`。対話試験ではランチャーの Python テキストも標準入力から依頼末尾へ添付されたため、実際の入力を `actual-input.txt` に保存した。親はそのコードを実行せず、実ツール記録も Agent 呼び出しだけだった。一時プロジェクトを信頼対象として起動し、完了後に `/exit` で終了した。

この環境差は[公式の nested subagent 仕様](https://code.claude.com/docs/en/sub-agents#let-subagents-spawn-their-own-subagents)と一致する。対話セッションは子が背景の孫を待つ。非対話・SDK では、起動元の子が終了済みなら孫の結果は main へ返る。通常の対話 CLI における Orchestrate の3階層委任は確認済みとする。プログラム全体の長期運用を試したものではなく、非対話で同じ集約経路が成立したという意味でもない。

深さの既定値は main の下に3層。`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` なら main→子→孫の2層を許可し、`1` なら子からの再委任を止める。今回の環境はこの値が未設定で、追加設定なしに起動できた。先行する `nesting/logs/run.stream.jsonl` は `aborted_streaming`、子の起動0件であり、成功の証拠に含めない。

## 実行環境の制約

agent 自身による goal の設定・取得は、過去に確認した実行環境では利用できなかった。0.15.9 の本家は Autopilot-full / stack と Multi-phase plan から goal の設定・取得を削除しており、移植版もその変更を反映する。コンパクション後の全文保持は未完了項目から除く。Orchestrate の3階層委任は上記の対話 CLI 試験で確認した。クラウド worker と cloud-sleeper は対象外。`make-bot-ui` もクラウド routine を必要とするため対象外とし、ローカルの独自サービスで代替する実装は追加しない。元の指示が残っていることを、Claude で実行できる証拠にはしない。

モデルによる手順省略の観測と、これらの未翻訳の実行指示は別の問題である。前者だけを根拠に、本家の行動指示を増やす修正は行わない。

Cursor の実行環境はない。本家のファイルから確認した要求と Claude で観測した結果を比較するところまでが、この環境で証明できる範囲となる。

[plugins]: https://code.claude.com/docs/en/plugins-reference
[names]: https://code.claude.com/docs/en/skills#how-a-skill-gets-its-command-name
[skills]: https://code.claude.com/docs/en/skills#frontmatter-reference
[tools]: https://code.claude.com/docs/en/tools-reference
[agents]: https://code.claude.com/docs/en/sub-agents
[agent-fields]: https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields
[background]: https://code.claude.com/docs/en/sub-agents#run-subagents-in-foreground-or-background
[fork-mode]: https://code.claude.com/docs/en/sub-agents#turn-fork-mode-on-or-off
[effort-resolution]: https://code.claude.com/docs/en/model-config#set-the-effort-level
[agent-model]: https://code.claude.com/docs/en/sub-agents#choose-a-model
[main-agent]: https://code.claude.com/docs/en/sub-agents#invoke-subagents-explicitly
[skill-lifecycle]: https://code.claude.com/docs/en/skills#skill-content-lifecycle
[skill-locations]: https://code.claude.com/docs/en/skills#choose-where-skills-load
[mcp-discovery]: https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search
[upstream-mode]: https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/poteto-mode/SKILL.md
[upstream-how]: https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/how/SKILL.md
[upstream-agent]: https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/agents/poteto-agent.md
[upstream-investigation]: https://github.com/cursor/plugins/blob/e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a/pstack/skills/poteto-mode/playbooks/investigation.md

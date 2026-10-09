# このリポジトリの保守

## 編集方針

- 変更前に関連ファイルを全文読む。簡潔さを優先し、依頼外の機能や互換処理を加えない。
- README は利用者向けの概要・導入・使い方・制約に絞る。保守指示はこのファイル、移植差分と検証記録は `docs/` に置く。
- `CLAUDE.md` は `AGENTS.md` を指す相対シンボリックリンクとし、指示の正本はこのファイルにする。
- 一時的な実験は直接実行するか `tmp/experiments/` で行う。常用環境の設定を試験で変更しない。

## 原本と配布ファイル

- 共通のスキル本文は `shared/skills/` を編集する。環境固有の本文は `{{#claude}}...{{/claude}}` と `{{#codex}}...{{/codex}}` に分ける。
- 片方だけに配布するファイルと Claude のエージェント定義テンプレートは `shared/clients/` を編集する。
- `claude/skills/`・`claude/agents/`・`codex/.agents/skills/` は `python3 tools/generate.py` で生成する。生成ファイルを直接編集しない。
- 移植元の固定コミット・バージョン・全ファイルの対応先・除外理由は `maintenance/upstream.json` を正本とする。
- 配布バージョンは `claude/.claude-plugin/plugin.json` の `version` のみで管理する。上流のバージョンと混同しない。
- 配布カタログは `.claude-plugin/marketplace.json`、移植パッチは `maintenance/patches/claude.patch` と `maintenance/patches/codex.patch`。配布バージョンのみの変更ではパッチの再生成は不要。
- 原著者の著作権表示と MIT ライセンスを保持する。同梱依存も移植元と同じ固定コミットから取得する。

## 移植の範囲

`poteto-mode` と `setup-pstack` を登録し、その他48スキルは内部ファイルとして保持する。クラウド worker はローカル子エージェントへ対応づける。

クラウド実行、クラウド専用の routine、定期タイマーによるターン終了後の再開、reminder、readonly の権限指定は対象外。コンパクション後の全文保持も保証しない。非対応の操作を独自サービスや代替フックで補わない。

## 上流の更新

保守ツールには Python 3.9 以降と Git が必要。外部 Python ライブラリは不要。既存の clone がなければ、次で取得する。

```sh
git clone --filter=blob:none https://github.com/cursor/plugins.git tmp/experiments/upstream-source
```

1. `maintenance/upstream.json` の固定コミットと上流の manifest を確認する。バージョンは実物を根拠に記載する。
2. 新しい対象コミットを fetch し、三者比較で更新候補を作る。以下の `NEW_COMMIT` は採用候補のコミット ID に置き換え、出力先には存在しないディレクトリを指定する。

   ```sh
   git -C tmp/experiments/upstream-source fetch origin NEW_COMMIT
   python3 tools/upstream.py compare \
     --source tmp/experiments/upstream-source \
     --to NEW_COMMIT \
     --out tmp/experiments/upstream-update
   ```

3. `report.json` と候補の全変更を確認する。追加・削除・改名・複数配置先への影響・除外理由を処理し、競合を解決する。競合がなくても翻訳の意味と内部参照をレビューする。候補を未確認で配布版へ上書きしない。
4. レビューした内容を `shared/` に反映し、配布版を生成する。`maintenance/upstream.json` の固定コミット・バージョン・対応表を更新する。
5. パッチを更新し、復元を検証する。利用者向けの変更は README、移植差分・検証範囲は `docs/` に反映する。

比較結果と保守ツールの詳細は [更新手順](docs/updating-upstream.md)、既存の移植判断は [差分一覧](docs/upstream-differences.md) を参照する。`refresh` はレビュー済みの配布版からパッチを作る操作であり、自動翻訳ではない。通常の移植修正でも同じ固定コミットで実行する。

## 検証

共通原本や保守機構を変更したら、次を実行する。

```sh
python3 tools/generate.py
python3 tools/generate.py --check
python3 tools/upstream.py refresh --source tmp/experiments/upstream-source
python3 tools/upstream.py check --source tmp/experiments/upstream-source
python3 -m unittest discover -s tools -p 'test_*.py'
```

パッチ復元やツールのテスト成功を、スキルの実行成功とは扱わない。変更箇所に応じて次も確認する。

- 登録・配置：Claude の plugin validator と Codex の native skill validator、明示起動と内部参照。
- 導入経路：一時プロジェクトで marketplace または README の導入コマンドを実行し、内部ファイル・ライセンス・実行権限を確認。
- 委任・プレイブック：実タスクで必要な指示の読み込み、子への入力、結果の受け渡しを確認。
- スクリプト：対象の既存テストと変更した入出力を確認。計画検証の条件を変えたら、その条件を欠く計画の失敗も確認。

実行試験では依頼文・設定・呼出引数・結果を記録する。試した範囲と未検証の範囲を区別し、モデルの事後説明だけで成功と断定しない。

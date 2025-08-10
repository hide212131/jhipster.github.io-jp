# 翻訳システム移行 仕様（spec.md）
対象: `.github/llm-translation/docs/requirements.md` の要望を満たす実装仕様  
非目的: 本来のドキュメントサイト本文の編集（`docs/` 直修正は禁止。翻訳パイプライン経由のみ）

---

## 1. 用語とリポジトリ
- **upstream**: `jhipster/jhipster.github.io`（英語原文）
- **origin**: `jhipster.github.io-jp`（日本語サイト/このリポジトリ想定）
- **translation branch**: `translate/sync-YYYYMMDD-HHMM`（Actions/ローカルで生成）
- **meta branch**: `translation-meta`（翻訳管理情報：各ファイルの基準 upstream SHA 等）
- **LLM**: Google Gemini（Secrets: `GEMINI_API_KEY`）

---

## 2. スコープ/ゴール
- upstream/main の更新を定期的に検知し、**Gemini で翻訳して origin に反映**。
- **ファイル/ディレクトリ構成は upstream と完全一致**（非ドキュメントはコピーのみ、翻訳しない）。
- **ドキュメントファイルは行数・行位置を完全一致**（i 行目の原文→origin 側 i 行目の訳）。
- **一行単位の“孤立翻訳”はしない**：段落/近傍コンテキストを使って訳し、**出力段階で元の改行位置に再配置**する。

---

## 3. 対象/除外
- 翻訳対象拡張子: `.md`, `.markdown`, `.mdx`, `.html`, `.adoc`
- 非対象（コピーのみ）: 画像/バイナリ/設定/ビルド資材（例: `.png .jpg .svg .gif .yml .yaml .json .scss .css .xml .ico` 等）
- 除外パス: `_site/`, `node_modules/`, `.git/`, `vendor/` ほか生成物

---

## 4. 厳格要件（Invariant）
- `len(upstream_lines) == len(origin_lines)` を常に満たす。
- コードフェンス（``` ～ ```）は **翻訳しない**（開始/終了行も含め原文維持）。
- インラインコード `` `...` ``、URL、Markdownリンクの URL 部、HTML属性値、脚注ID、表の区切り `|` とアライメント `:`, 末尾2スペースは **プレースホルダ保護→復元**。
- 改行コードは LF 固定。空行・末尾スペースは保持。

---

## 5. 差分分類と翻訳ポリシー
upstream 旧版（meta 記録）と最新版の行オペコードで判定：
- `equal` … **既訳を温存**（API 呼び出し無し）
- `insert` … **新規挿入行だけ翻訳**し、同位置に N 行挿入
- `delete` … 対応する訳行を **同数削除**
- `replace`
  - 軽微変更（`SequenceMatcher.ratio ≥ 0.98` かつトークン数同等、句読点/空白/typo 程度）→ **既訳温存**
  - それ以外 → **該当範囲を再翻訳**（段落文脈を与える）
  - 曖昧時は LLM に **YES/NO** で「意味変化の有無」を判定し、YES なら再翻訳

---

## 6. 翻訳アルゴリズム
### 6.1 セグメンテーション（段落翻訳→行再配置）
1. 翻訳対象ファイルを読み込み、**段落境界（空行/見出し/箇条書き/表/HTMLブロック）**でブロック分割。
2. 各ブロックに対して：
   - **近傍前後ブロック**をコンテキストとして LLM に入力（「一行ごとではなくブロック単位で文意把握」）。
   - ただし **コードフェンス/非対象要素は生のまま**。
   - LLM 出力を受け取り、**原文の改行位置に一致するよう**に**再分割（reflow）**して**行ロック出力**を得る。  
     ※ reflow では**語の切断禁止**、幅超過時は次行へ繰り下げ、**総行数はブロック原文と一致**。
3. プレースホルダを復元。**最終出力は元行数と完全一致**。

### 6.2 マイクロバッチ/並列
- 連続ブロック（または 16–64 行相当）を **1 リクエストにまとめ**、**件数・順序固定**のプロトコルで返させる。  
  破綻時は自動でバッチ分割→最終的に単ブロック/単行にフォールバック。
- 同時実行はセマフォで制御（例: 8 並列）。指数バックオフで再試行。

### 6.3 出力禁則/検証
- 返答に改行が混入した場合は **空白に正規化**。件数不一致・プレースホルダ破損は**バッチ分割で再試行**。
- すべての対象ファイルについて **行数一致/構成一致/フェンス整合/表整合**を機械検証。失敗時は**非ゼロ終了**。

---

## 7. PR 仕様
- **更新がある場合のみ** translation branch を push。
- **PR本文必須項目**：
  - 更新ファイル名 **全件**（追加/変更/削除/非対象コピーを分類）
  - 各ファイルの変更種別（insert/replace/delete/copy_only）、行数差、採用戦略（keep/retranslate/insert/delete）、基準 upstream SHA
  - **リンク**：原文の変更コミット / 翻訳ブランチのコミット（人間レビュー用）
  - 検証結果の要約（行数一致OK/NG、NGなら対象ファイル）
- PR は人間がレビューし `origin/main` へマージ。

---

## 8. 実装配置
- スクリプト（暫定・後で削除可）：`tools/`（ルート直下、または `.ops/migration/tools/` でも可）
- メタ管理ブランチ：`translation-meta` に `manifest.json`
- 移行仕様ドキュメント：`.github/llm-translation/docs/requirements.md`, `spec.md`

推奨ディレクトリ（例）:
````

tools/
config.py
git\_utils.py
file\_filters.py
placeholder.py
segmenter.py
reflow\.py
line\_diff.py
llm.py
translate\_blockwise.py
discover\_changes.py
apply\_changes.py
pr\_body.py
verify\_alignment.py
run\_sync.py

````

---

## 9. CLI/スクリプト仕様（Issue 化しやすい粒度）
### 9.1 `discover_changes.py`
- 入力: `--upstream-ref <ref>`（既定: upstream/main）, `--meta-branch translation-meta`
- 出力: 変更一覧 JSON（ファイル単位の opcodes、対象/非対象）
- DoD: 非対象は `copy_only`、対象は `equal/insert/delete/replace` がレンジで列挙される

### 9.2 `translate_blockwise.py`
- 入力: ソース本文、ブロック境界設定、コンテキスト幅
- 出力: **原文と同行数**の翻訳テキスト
- DoD: コードフェンス無翻訳、プレースホルダ無破損、行数一致

### 9.3 `apply_changes.py`
- 入力: `discover_changes` の指示＋既存訳
- 動作: ポリシーに従い keep/insert/delete/retranslate を適用
- 出力: 更新後の訳と更新ファイル一覧
- DoD: 更新後に `verify_alignment` を通過

### 9.4 `verify_alignment.py`
- 検査: 行数一致、構成一致、フェンス整合、表パイプ/アライメント一致、末尾2スペース保持
- 失敗時: 非ゼロ終了＋ズレ起点をレポート
- DoD: サンプルフィクスチャで NG ケースを検出

### 9.5 `pr_body.py`
- 入力: 変更ファイル一覧、戦略、SHA
- 出力: `tools/.out/pr_body.md`
- DoD: すべての更新ファイルが表に列挙され、原文/訳コミットへのリンクを含む

### 9.6 `run_sync.py`
- モード: `ci` / `dev`
- 共通引数: `--branch`, `--before <upstream_sha>`, `--limit N`, `--paths 'docs/**'`
- `ci`: 変更検出→翻訳→検証→ブランチ作成→ `PR_NEEDED=1` を `GITHUB_ENV` に書く
- `dev`: ローカルで絞り込み実行（指定 SHA **以前**の未翻訳のみ、N 件限定）
- DoD: `--limit` と `--before` が効いて対象件数が制御できる

---

## 10. GitHub Actions（薄いラッパー）
`.github/workflows/sync.yml`
- トリガ: `schedule`（cron）＋ `workflow_dispatch`
- 権限: `contents: write`, `pull-requests: write`
- 環境: `GEMINI_API_KEY`（Secrets）, `GITHUB_TOKEN`
- 手順: checkout → upstream 追加/fetch → meta 取得 → `python tools/run_sync.py --mode ci ...` → `if PR_NEEDED==1 then gh pr create --body-file tools/.out/pr_body.md`
- ガード: 必要なら「上流のみ有効」条件を `if:` に設定（fork では schedule 無効）

---

## 11. セキュリティ/可用性
- `GEMINI_API_KEY` は **Actions Secrets** のみで扱い、PR イベントでは使用しない。
- 例外/レート制限: セマフォ＋指数バックオフ。最大リトライ回数を超えたらファイル単位でスキップし PR に明記。
- キャッシュ: `(path, upstream_sha, block_id/hash)` キーで SQLite キャッシュ（再実行時の LLM 呼び出し削減）

---

## 12. メトリクス/ログ
- `tools/.out/report.json` にファイル単位の統計を出力：`{inserted, replaced, kept, deleted, nondoc_copied, llm_calls, retries}`
- Actions のアーティファクトとして保存。PR本文に合計値を要約。

---

## 13. Issue 化テンプレ（粒度見本）
- **tools 雛形**：ファイル生成、`requirements.txt`、`Makefile`、`--help` 実装（DoD: `make dev` が動く）
- **セグメンテーション/再配置**：`segmenter.py`/`reflow.py` 実装（DoD: サンプル2件で原文行数=訳行数）
- **プレースホルダ保護**：URL/インラインコード/脚注ID/表/末尾2スペース（DoD: 6 ケースのユニットテスト）
- **差分検出/適用**：equal/insert/delete/replace、軽微変更スキップ、意味判定（DoD: フィクスチャで4種すべて通過）
- **検証器**：行数/構成/フェンス/表（DoD: 失敗例で必ず落ちる）
- **PR本文生成**：全更新列挙＋リンク（DoD: マルチファイル更新で表が正しく埋まる）
- **Actions**：cron＋手動、PR作成（DoD: dry-run でドラフトPRが出来る）
- **開発モード**：`--before`/`--limit`/`--paths`（DoD: 指定件数で止まる）
- **キャッシュ/リトライ**：LLM 呼び出し削減（DoD: 再実行で llm_calls 減少）

---

## 14. 開発モード（要件の反映）
- 目的: **Actions を何度も回さず**ローカルで安全に検証。
- コマンド例:
  ```bash
  pip install -r requirements.txt
  python tools/run_sync.py --mode dev --before <upstream_sha> --limit 3 --paths 'docs/getting-started/**'
  python tools/verify_alignment.py
  ```

* 期待: 指定 SHA **以前**の未翻訳のみ対象化、最大 3 件で停止、検証パス。

---

## 15. 退役

* 移行完了後、スクリプト/移行専用ドキュメントは必要に応じて削除または `.github/records/` へアーカイブ。
* 運用は Actions（定期同期）のみを残す。


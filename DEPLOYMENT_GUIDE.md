# LLM翻訳パイプライン 使用・デプロイガイド

## 🚀 概要

このガイドでは、LLM翻訳パイプラインの使用方法、デプロイ手順、および運用方法について説明します。

## 📋 前提条件

### 必要な環境
- Python 3.12+
- Git
- GitHub account with Actions enabled
- Google Gemini API key

### リポジトリ構成
- **upstream**: `jhipster/jhipster.github.io` (英語原文)
- **origin**: `hide212131/jhipster.github.io-jp` (日本語サイト)

## 🛠️ 初期セットアップ

### 1. ローカル開発環境

```bash
# リポジトリクローン
git clone https://github.com/hide212131/jhipster.github.io-jp.git
cd jhipster.github.io-jp

# 開発環境セットアップ
cd tools
make dev

# すべてのテスト実行
make test
```

### 2. GitHub Secrets設定

以下のSecretsをリポジトリに追加してください：

```
GEMINI_API_KEY: [Your Google Gemini API Key]
```

**設定方法**:
1. GitHub リポジトリ → Settings → Secrets and variables → Actions
2. "New repository secret" をクリック
3. Name: `GEMINI_API_KEY`, Value: [APIキー] を入力

### 3. upstream リモート追加

```bash
git remote add upstream https://github.com/jhipster/jhipster.github.io.git
git fetch upstream
```

## 🎯 使用方法

### 開発モード（ローカルテスト）

開発モードでは、制限付きで翻訳をテストできます：

```bash
cd tools

# 最大3ファイルまで処理（dry-run）
python run_sync.py --mode dev --limit 3 --dry-run

# 特定パスのみ処理
python run_sync.py --mode dev --paths "docs/getting-started/**" --limit 2

# 特定のupstream SHAまでの変更のみ処理
python run_sync.py --mode dev --before abc1234567 --limit 5

# 実際に翻訳を実行（注意：API使用）
python run_sync.py --mode dev --limit 1
```

**開発モードオプション**:
- `--limit N`: 処理ファイル数を制限
- `--before SHA`: 指定SHAより前の変更のみ処理
- `--paths PATTERN`: パスパターンで絞り込み
- `--dry-run`: 実際の翻訳をせずプレビューのみ

### 本番モード（GitHub Actions）

#### 自動実行
- **スケジュール**: 毎週月曜01:00 UTC（10:00 JST）に自動実行
- **処理**: 変更があれば自動でPR作成

#### 手動実行
1. GitHub リポジトリ → Actions → "LLM Translation Sync"
2. "Run workflow" をクリック
3. オプション設定：
   - `dry_run`: true（ドラフトPR作成）/ false（通常PR作成）
   - `upstream_ref`: upstream/main（デフォルト）

## 📊 出力と結果確認

### ローカル実行時

```bash
# 結果ファイル確認
ls -la tools/.out/
cat tools/.out/sync_results.json

# PR本文プレビュー
cat tools/.out/pr_body.md

# メトリクス確認
cat tools/.out/report.json
```

### GitHub Actions実行時

1. **Actions ログ**: 実行概要とエラー確認
2. **Artifacts**: 詳細ログとファイル一覧（30日保存）
3. **PR**: 自動作成されたPull Request

## 🔍 トラブルシューティング

### よくある問題

#### 1. GEMINI_API_KEY が設定されていない
```
Error: GEMINI_API_KEY secret is not configured
```
**解決方法**: GitHub Secrets に API キーを追加

#### 2. upstream取得エラー
```
Error: Could not fetch from upstream
```
**解決方法**: upstream リモートを追加
```bash
git remote add upstream https://github.com/jhipster/jhipster.github.io.git
git fetch upstream
```

#### 3. 行数不一致エラー
```
Error: Line count mismatch in file docs/example.md
```
**解決方法**: verify_alignment.pyで詳細確認
```bash
python verify_alignment.py --file docs/example.md --verbose
```

#### 4. LLMレート制限
```
Warning: Rate limit reached, retrying...
```
**解決方法**: 自動リトライが動作するまで待機（通常自動回復）

### デバッグ用コマンド

```bash
# 特定ファイルの差分確認
python discover_changes.py --file docs/example.md --verbose

# 翻訳アライメント検証
python verify_alignment.py --file docs/example.md

# プレースホルダテスト
python test_placeholder_verification.py

# 完全パイプラインテスト
python test_complete_pipeline.py
```

## 📈 運用監視

### 定期チェック項目

1. **GitHub Actions実行状況**
   - 毎週の自動実行成功/失敗
   - エラーログの確認

2. **PR レビュー**
   - 自動作成されたPRの内容確認
   - 翻訳品質チェック
   - マージ実行

3. **メトリクス監視**
   - API使用量（Gemini API quota）
   - 処理時間とファイル数
   - キャッシュヒット率

### パフォーマンス最適化

```bash
# キャッシュ統計確認
python translate_blockwise.py --show-stats

# メトリクス詳細表示
python test_metrics_integration.py
```

## 🔧 カスタマイズ

### 設定変更

主要設定は `tools/config.py` で管理：

```python
# 並列処理数
max_concurrent_requests = 8

# リトライ設定
retry_max_attempts = 3
retry_delay = 1.0

# 翻訳対象拡張子
TRANSLATION_EXTENSIONS = ['.md', '.markdown', '.mdx', '.html', '.adoc']
```

### スケジュール変更

`.github/workflows/sync.yml` の cron 設定を変更：

```yaml
schedule:
  # 毎日午前2時に実行する場合
  - cron: '0 2 * * *'
```

## 🎯 Best Practices

### 開発時
1. **小さな変更で試す**: `--limit 1` から開始
2. **dry-run を活用**: 実際の翻訳前にプレビュー
3. **特定パスで絞り込み**: `--paths` で範囲限定
4. **定期的なテスト実行**: `make test` でregression確認

### 運用時
1. **PR レビューの実施**: 自動PRを必ず人間がチェック
2. **エラー監視**: Actions失敗時の迅速な対応
3. **API quota管理**: Gemini API使用量の監視
4. **定期的なupstream同期**: 手動実行も活用

## 🔗 関連リンク

- [開発計画](./LLM_TRANSLATION_DEVELOPMENT_PLAN.md)
- [技術仕様](./tools/spec.md)
- [要件定義](./tools/requirements.md)
- [Issue テンプレート](./.github/ISSUE_TEMPLATE/llm-translation/)
- [GitHub Actions](./.github/workflows/sync.yml)

---

*このガイドは LLM翻訳パイプライン v1.0 に対応しています*
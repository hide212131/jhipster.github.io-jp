# JHipster JP Sync Tool

このディレクトリには、JHipster日本語サイトの同期・翻訳パイプライン用のツールが含まれています。

## ファイル構成

- `run_sync.py` - メインの同期・翻訳ツール

## 使用方法

### 基本実行

```bash
# ドライランモード（PR テンプレート生成のみ）
python tools/run_sync.py --dry-run

# 実際の同期実行
python tools/run_sync.py

# 詳細ログ付き
python tools/run_sync.py --dry-run --verbose
```

### 環境変数

以下の環境変数が必要です：

- `GITHUB_TOKEN` - GitHub API アクセス用トークン
- `GEMINI_API_KEY` - 翻訳処理用 Gemini API キー
- `GITHUB_REPOSITORY` - リポジトリ名（通常は自動設定）
- `GITHUB_EVENT_NAME` - イベント名（通常は自動設定）

## 安全ガード機能

このツールには以下の安全ガード機能が組み込まれています：

### リポジトリ検出
- **フォークリポジトリ**: `hide212131/jp` での実行を想定
- **本家リポジトリ**: `jhipster/jhipster.github.io` での実行をブロック

### イベント制御
- **スケジュール実行**: フォークでの定期実行を許可
- **手動実行**: フォークでの手動実行を許可  
- **プルリクエスト**: PR イベントでの実行をブロック

### 権限管理
- PR作成はフォークからのみ許可
- 必要なシークレットの存在確認
- ドライランモードでの安全な動作確認

## 出力

### ドライランモード
- `sync_pr_template.md` - PR テンプレートファイル生成
- コンソールログによる実行状況表示

### 実際の同期モード
- 上流リポジトリからの同期処理
- 翻訳パイプラインの実行
- 変更検出時の自動PR作成

## トラブルシューティング

### よくあるエラー

1. **"Sync operation blocked by safety guard"**
   - 本家リポジトリまたは不適切なイベントでの実行
   - フォークリポジトリから適切なイベントで実行してください

2. **"GITHUB_TOKEN not found in environment"**
   - GitHub Actions シークレットの設定が必要
   - リポジトリ設定でシークレットを追加してください

3. **"GEMINI_API_KEY not found in environment"**
   - 翻訳機能用 API キーの設定が必要
   - リポジトリ設定でシークレットを追加してください
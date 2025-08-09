# JHipster日本語ドキュメント自動翻訳システム

JHipster英語ドキュメントを Google Gemini を使用して日本語に自動翻訳するシステムです。

## 🎯 概要

このシステムは、[JHipster公式サイト](https://github.com/jhipster/jhipster.github.io) の英語コンテンツを継続的に監視し、更新があった場合に自動翻訳してPRを作成します。

### 主な機能

- **自動差分検出**: upstreamの変更を検出・分類
- **Gemini翻訳**: Google Gemini APIによる高品質翻訳
- **整合性検証**: 行数・構造・フェンス整合チェック
- **PR自動生成**: 翻訳結果をPRとして自動作成
- **品質保証**: 既存日本語コンテンツの不変性保証

## 🚀 クイックスタート

### 環境セットアップ

```bash
# 依存関係をインストール
make install

# 環境変数を設定
cp .env.sample .env
# .env ファイルを編集して実際のAPIキーを設定

# テストを実行
make test
```

### 使用方法

```bash
# ドライランモード（実際の翻訳・コミット・PRなし）
make run-dry

# 実際の翻訳実行
make run

# 新規ファイルのみ翻訳
make run-new

# 選択的翻訳（衝突ファイル除外）
make run-selective
```

## 📁 ディレクトリ構成

```
.github/auto-translation/
├── scripts/           # 主要スクリプト
│   ├── run_translation_pipeline.py    # 統合パイプライン
│   ├── fetch_upstream.py              # upstream取得
│   ├── classify_changes.py            # ファイル分類
│   ├── translate_chunk.py             # Gemini翻訳
│   ├── postprocess.py                 # 後処理・検証
│   └── commit_and_pr.py               # PR作成
├── tests/             # テストファイル
├── docs/              # ドキュメント
│   ├── style-guide.md                 # 翻訳スタイルガイド
│   └── style-guide-release.md         # リリース用スタイルガイド
├── Makefile           # 開発・運用コマンド
├── pyproject.toml     # 依存関係管理
└── requirements.txt   # Python依存関係
```

## 🔧 設定

### 必要な環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `GEMINI_API_KEY` | Google Gemini APIキー | ✅ |
| `GH_TOKEN` | GitHub Token（PR作成用） | ✅ |
| `BOT_GIT_USER` | Botのユーザー名 | ✅ |
| `BOT_GIT_EMAIL` | Botのメールアドレス | ✅ |
| `LANGUAGE_TOOL_ENABLED` | 文法チェック有効化 | ❌ |
| `DRY_RUN` | ドライランモード | ❌ |

### GitHub Actions設定

システムはGitHub Actionsでも動作します：

- **手動実行**: `workflow_dispatch`イベント
- **定期実行**: 毎日03:00 UTC（予定）
- **セキュリティ**: 本家リポジトリでのみ実行される安全ガード

## 📊 翻訳プロセス

### 1. Upstream同期
```bash
python scripts/fetch_upstream.py --hash [COMMIT_HASH]
```

### 2. 変更分類
```bash
python scripts/classify_changes.py --output-format json
```

ファイルは以下のカテゴリに分類されます：
- **a**: 新規翻訳対象ファイル
- **b-1**: 軽微変更（既訳維持）
- **b-2**: コンフリクトファイル（手動翻訳）
- **c**: 非翻訳対象ファイル

### 3. 翻訳実行
```bash
python scripts/translate_chunk.py --classification classification.json --mode selective
```

### 4. 後処理・検証
```bash
python scripts/postprocess.py --classification classification.json
```

### 5. PR作成
```bash
python scripts/commit_and_pr.py --classification classification.json
```

## 🧪 テスト

```bash
# 全テスト実行
make test

# 特定テスト実行
python -m pytest tests/test_translate_chunk.py -v

# コード品質チェック
make lint
```

## 📋 翻訳ルール

### 基本方針
- 「です・ます調」を使用
- 技術文書として客観的な表現
- 既存日本語コンテンツの不変性保証

### 対象ファイル
- `.md`, `.mdx`, `.adoc`, `.html`
- コードフェンス内容は非翻訳
- プレースホルダの保護・復元

詳細は [style-guide.md](docs/style-guide.md) を参照してください。

## 🚨 トラブルシューティング

### よくある問題

1. **APIキーエラー**
   ```bash
   export GEMINI_API_KEY=your_actual_api_key
   ```

2. **テスト失敗**
   ```bash
   make clean
   make test
   ```

3. **Git権限エラー**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

## 📚 詳細ドキュメント

- [システム仕様](spec.md)
- [タスク一覧](tasks.md)
- [翻訳スタイルガイド](docs/style-guide.md)

## 🤝 コントリビューション

1. フォークしてブランチを作成
2. 変更を実装
3. テストを実行して確認
4. PRを作成

## 📄 ライセンス

Apache 2.0 License - JHipsterプロジェクトに準拠
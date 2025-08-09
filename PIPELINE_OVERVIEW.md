# JP自動同期・Gemini翻訳パイプライン導入（EPIC）

## 概要
このEPICは、upstream（英語）→ origin（日本語）への自動同期と翻訳パイプラインの導入を追跡します。最終の公開先は jhipster/jp です。

## 実装状況

### ✅ 完了項目
- [x] 基本ディレクトリ構造の作成（tools/）
- [x] Python依存関係の定義（requirements.txt）
- [x] 自動化タスクの定義（Makefile）
- [x] 翻訳パイプライン用GitHubワークフロー（.github/workflows/sync.yml）
- [x] 翻訳メタデータブランチ構造（translation-meta）
- [x] 基本テスト環境のセットアップ
- [x] ログ管理とディレクトリ構造

### 🔄 実装中項目（子Issue参照）
- [ ] Issue #2: 詳細な同期スクリプト実装
- [ ] Issue #3: Gemini API クライアント実装
- [ ] Issue #4: コンテンツ処理ユーティリティ
- [ ] Issue #5: 翻訳品質検証機能
- [ ] Issue #6: 競合解決自動化
- [ ] Issue #7: パフォーマンス最適化
- [ ] Issue #8: エラーハンドリング強化
- [ ] Issue #9: 統合テスト
- [ ] Issue #10: ドキュメント完成

## ディレクトリ構造

```
.
├── tools/                      # 翻訳パイプライン tools
│   ├── README.md              # Tools ドキュメント
│   ├── sync/                  # 同期関連スクリプト
│   │   └── sync_upstream.py   # アップストリーム同期
│   ├── translation/           # 翻訳関連スクリプト
│   │   └── translate_content.py # Gemini翻訳
│   ├── common/                # 共通ユーティリティ
│   │   └── config.py          # 設定管理
│   ├── tests/                 # テストスイート
│   │   └── test_sync.py       # 同期機能テスト
│   └── logs/                  # ログファイル
├── .github/workflows/
│   └── sync.yml               # 翻訳パイプライン ワークフロー
├── requirements.txt           # Python依存関係
├── Makefile                  # 自動化タスク
└── .gitignore               # ツール関連除外設定追加
```

## 設定環境変数

### 必須
- `GEMINI_API_KEY`: Google AI API キー
- `GITHUB_TOKEN`: GitHub アクセストークン

### オプション
- `UPSTREAM_REPO`: ソースリポジトリ（デフォルト: jhipster/jhipster.github.io）
- `TARGET_REPO`: ターゲットリポジトリ（デフォルト: jhipster/jp）

## 使用方法

```bash
# ヘルプ表示
make help

# 依存関係インストール
make install

# 同期実行
make sync

# 翻訳実行
make translate

# テスト実行
make test

# サイト構築
make build

# ローカル実行
make serve
```

## GitHubワークフロー

### 自動実行
- 毎週月曜日 02:00 UTC（upstream sync後）
- 手動トリガー可能（`workflow_dispatch`）

### 実行内容
1. アップストリームとの差分チェック
2. 同期・翻訳パイプライン実行
3. 翻訳結果のPR自動作成
4. ログのアーティファクト保存

## 翻訳メタデータブランチ

`translation-meta` ブランチで以下を管理：
- 翻訳進捗状況
- ファイルマッピング
- 品質スコア
- 実行履歴

## 次のステップ

1. 子Issue（#2-#10）の詳細実装
2. Gemini API キーの設定
3. 上流リポジトリでのスケジュール実行有効化
4. 初回運用PR の作成

---

**注意**: これは追跡用EPICです。個別実装詳細は各子Issueを参照してください。
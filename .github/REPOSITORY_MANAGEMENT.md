# リポジトリ管理ガイド

このドキュメントでは、JHipster日本語サイトリポジトリの管理方針と運用方法について説明します。

## ラベル管理

### 利用可能なラベル

| ラベル | 説明 | 色 | 用途 |
|--------|------|-----|------|
| `area:translation-pipeline` | 自動翻訳パイプラインと ローカライゼーション関連 | 🔵 | 翻訳システムの不具合や改善 |
| `agent:copilot` | GitHub Copilotによる支援 | 🟣 | AI支援による作業の識別 |
| `priority:P2` | 中優先度 | 🟡 | 現在のイテレーションで対応すべき課題 |
| `ci` | 継続的インテグレーション関連 | 🔵 | ビルド、テスト、デプロイ関連 |
| `security` | セキュリティ関連 | 🔴 | セキュリティの問題や強化 |

### ラベルの設定方法

#### 自動設定（推奨）
```bash
# スクリプトを実行してラベルを一括作成
./.github/scripts/setup-labels.sh
```

#### 手動設定
```bash
# GitHub CLI を使用
gh label create "area:translation-pipeline" --description "Issues related to the automatic translation pipeline and localization workflow" --color "0366d6"
gh label create "agent:copilot" --description "Issues and PRs created or assisted by GitHub Copilot" --color "7C4DFF"
gh label create "priority:P2" --description "Medium priority issue - should be addressed in current iteration" --color "fbca04"
gh label create "ci" --description "Continuous Integration related issues" --color "1d76db"
gh label create "security" --description "Security-related issues and enhancements" --color "d73a4a"
```

### ラベルの使用方法

```bash
# Issueにラベル追加
gh issue edit [issue-number] --add-label "area:translation-pipeline,priority:P2"

# PRにラベル追加
gh pr edit [pr-number] --add-label "ci"

# 複数ラベルの追加
gh issue edit [issue-number] --add-label "security,priority:P2"
```

## Secrets管理

### セキュリティポリシー

**GEMINI_API_KEY の取り扱い**:
- ✅ **上流リポジトリのみ**: メインリポジトリでのみ使用可能
- ❌ **フォーク禁止**: フォークでは自動翻訳システムは無効
- ❌ **PR制限**: プルリクエストイベントでは参照不可

### 設定済みSecrets

| Secret名 | 説明 | 使用場所 |
|----------|------|----------|
| `GEMINI_API_KEY` | Google Gemini API キー | 自動翻訳ワークフロー |
| `GH_TOKEN` | GitHub API アクセストークン | PR作成、ラベル管理 |

### Secrets運用ルール

1. **最小権限の原則**: 必要最小限のワークフローでのみ使用
2. **定期更新**: API キーは定期的に更新
3. **ログ保護**: Secrets情報がログに出力されないよう注意
4. **アクセス制限**: `pull_request` イベントでは機密情報へのアクセスを制限

## GitHub CLI 活用

### 基本的な使用方法

```bash
# 認証
gh auth login

# PR作成
gh pr create --title "機能: 新機能追加" --body "詳細な説明"

# ドラフトPR作成
gh pr create --draft --title "WIP: 作業中"

# PR状態確認
gh pr status

# Issue作成
gh issue create --title "バグ: 問題の説明" --body "再現手順..." --label "priority:P2"
```

### ワークフロー例

```bash
# 1. ブランチ作成
git checkout -b feature/new-feature

# 2. 変更作業
# ... コード変更 ...

# 3. コミットとプッシュ
git add .
git commit -m "feat: 新機能を追加"
git push origin feature/new-feature

# 4. PR作成
gh pr create --title "機能: 新機能の追加" --body "この機能は..." --label "priority:P2"

# 5. レビュー対応後、マージ
gh pr merge --squash
```

## ワークフロー管理

### 自動化されているプロセス

1. **自動翻訳**: 毎日12:00 JST に上流の変更をチェック
2. **依存関係更新**: Dependabot による自動更新
3. **デプロイ**: `main` ブランチへのプッシュ時に自動デプロイ
4. **テスト**: PR作成時の自動テスト実行

### 手動で実行可能なアクション

```bash
# ローカルでの翻訳実行
cd .github/auto-translation
make run-dry  # ドライラン

# ビルドとテスト
npm run build
npm run typecheck

# 翻訳システムのテスト
cd .github/auto-translation
make test
```

## トラブルシューティング

### よくある問題と解決策

#### 1. ラベルが作成できない
```bash
# GitHub CLI の認証確認
gh auth status

# 権限確認
gh repo view --json permissions
```

#### 2. 自動翻訳が動作しない
- `GEMINI_API_KEY` の設定確認
- API制限の確認
- ワークフローログの確認

#### 3. ビルドエラー
```bash
# 依存関係の再インストール
rm -rf node_modules package-lock.json
npm install

# キャッシュクリア
npm run clear
```

## 監視とメンテナンス

### 定期的なチェック項目

- [ ] Secrets の有効期限確認
- [ ] 依存関係の脆弱性チェック
- [ ] ワークフローの実行状況確認
- [ ] ディスク容量の確認
- [ ] ログの確認

### パフォーマンス監視

- ビルド時間: < 5分
- 翻訳処理時間: < 30分
- デプロイ時間: < 2分

これらの基準を超える場合は最適化を検討してください。
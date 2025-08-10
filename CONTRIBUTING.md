# コントリビューションガイド

JHipster日本語サイトへのコントリビューションをありがとうございます！

## 開発環境

### 必要な環境
- Node.js 20+
- npm

### セットアップ
```bash
npm install
npm start  # 開発サーバー起動
```

## コントリビューション方法

### 1. Issue作成
- バグ報告や機能要求は、まずIssueを作成してください
- 適切なラベルを選択してください：
  - `area:translation-pipeline`: 自動翻訳パイプライン関連
  - `agent:copilot`: GitHub Copilotによる支援
  - `priority:P2`: 中優先度
  - `ci`: CI/CD関連
  - `security`: セキュリティ関連

### 2. プルリクエスト
- フォークしてからfeatureブランチを作成
- 変更内容は最小限に抑制
- テストとビルドが通ることを確認

```bash
npm run build  # ビルド確認
npm run typecheck  # 型チェック
```

### 3. 翻訳作業
- 自動翻訳システムが利用可能です（`.github/auto-translation/`）
- 翻訳品質ガイドラインは `.github/auto-translation/docs/style-guide.md` を参照

### 4. GitHub CLI の使用
PR作成時にgh CLIを使用できます：

```bash
# PR作成
gh pr create --title "機能: 新機能の追加" --body "変更内容の説明"

# PR状態確認
gh pr status

# PR一覧
gh pr list
```

## レビュープロセス

1. 自動チェック（CI/CD）の完了
2. コードレビュー
3. 翻訳品質チェック（翻訳関連の場合）
4. 最終承認とマージ

## 注意事項

- セキュリティに関する問題は `SECURITY.md` を参照
- 大きな変更の場合は、事前にIssueで議論
- 翻訳の一貫性を保つため、既存のスタイルガイドに従ってください

## 質問・サポート

不明点がある場合は、Issueで質問するか、既存のディスカッションを確認してください。
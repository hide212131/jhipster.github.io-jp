# LLM翻訳パイプライン Issue テンプレート

このディレクトリには、LLM翻訳パイプラインの段階的開発を進めるためのIssueテンプレートが含まれています。

## 使用方法

各ステップのIssueを作成する際に、対応するテンプレートを使用してください。

## 開発ステージ一覧

1. [🛠️ tools雛形・開発環境整備](./01-tools-scaffold.md)
2. [✂️ セグメンテーション/再配置](./02-segmentation-reflow.md)
3. [🔒 プレースホルダ保護](./03-placeholder-protection.md)
4. [🔍 差分検出](./04-diff-detection.md)
5. [🔄 差分適用](./05-diff-application.md)
6. [🌍 翻訳実行](./06-translation-execution.md)
7. [✅ 検証器](./07-verification.md)
8. [📝 PR本文生成](./08-pr-body-generation.md)
9. [🏃 ランナー](./09-runner.md)
10. [⚙️ GitHub Actions](./10-github-actions.md)
11. [📊 メタ管理](./11-meta-management.md)
12. [🔐 セキュリティ/Secrets運用](./12-security-secrets.md)
13. [📈 メトリクス/ログ/アーティファクト](./13-metrics-logging.md)

## 注意事項

- **現在すべてのステージが完了済みです**
- これらのテンプレートは参考資料として保持されています
- 新機能追加や改善時の参考にご利用ください
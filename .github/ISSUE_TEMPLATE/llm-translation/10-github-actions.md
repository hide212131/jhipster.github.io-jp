---
name: "⚙️ Stage 10: GitHub Actions"
about: sync.ymlワークフローの実装
title: "[Stage 10] GitHub Actions: sync.yml"
labels: ["llm-translation", "github-actions", "ci-cd"]
assignees: []
---

## 📋 タスク概要
.github/workflows/sync.yml の実装（定期実行 + 手動実行対応）

## 🎯 受入基準 (DoD)
- [ ] dry-runでドラフトPRが作成できる
- [ ] 定期実行（cron）が設定されている
- [ ] 手動実行（workflow_dispatch）が可能
- [ ] セキュリティガードが適切に設定されている
- [ ] アーティファクトが適切に保存される

## 📁 対象ファイル
- [ ] `.github/workflows/sync.yml`
- [ ] セキュリティ設定
- [ ] 環境変数設定

## ✅ 実装内容
- [ ] スケジュール実行 (cron: '0 1 * * 1' - 毎週月曜01:00 UTC)
- [ ] 手動実行オプション（dry_run, upstream_ref）
- [ ] フォーク保護（only main repository）
- [ ] PR作成機能
- [ ] アーティファクト保存

## 🔐 セキュリティ要件
- [ ] `GEMINI_API_KEY` はSecrets管理
- [ ] PRイベント時のSecrets使用禁止
- [ ] フォーク環境での定期実行無効化
- [ ] セキュアなログ出力（機密情報の露出防止）

## 🧪 テスト方法
```yaml
# 手動実行テスト
# GitHub Actions UI で workflow_dispatch 実行

# dry-run テスト
# dry_run: true オプションでドラフトPR作成確認

# セキュリティテスト
# フォーク環境で定期実行が無効になることを確認
```

## 📦 成果物
- [ ] `.out/sync_results.json` - 実行結果
- [ ] `.out/pr_body.md` - PR本文
- [ ] `.out/sync.log` - 実行ログ
- [ ] アーティファクト（30日保存）

## 🔄 ワークフロー
1. **checkout** - リポジトリ取得
2. **setup** - Python環境セットアップ
3. **fetch** - upstream/metaブランチ取得
4. **sync** - LLM翻訳実行
5. **check** - PR必要性判定
6. **create-pr** - PR作成（必要時のみ）
7. **upload** - アーティファクト保存

## 🔗 関連資料
- [GitHub Actions仕様](../../../tools/spec.md#10-github-actions薄いラッパー)
- [セキュリティガイドライン](../../../tools/spec.md#11-セキュリティ可用性)
- [既存ワークフロー](.github/workflows/sync.yml)

## 📝 備考
- 既存のsync-upstream.ymlとの競合を避けるため1時間後に実行
- 本番環境でのSecrets設定が必要（GEMINI_API_KEY）
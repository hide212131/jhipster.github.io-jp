# Tools

このディレクトリには、アップストリーム同期と翻訳パイプライン用のツールが含まれています。

## run_sync.py

GitHub Actionsワークフローから呼び出されるメインスクリプトです。

### 使用方法

```bash
python tools/run_sync.py --mode ci --branch translate/sync-20240109-123456
```

### オプション

- `--mode`: 実行モード (`ci` または `local`)
- `--branch`: 対象ブランチ名
- `--before`: この時刻より前に変更されたファイルを処理
- `--limit`: 処理するファイル数の制限

### 安全ガード

このスクリプトは `jhipster/jp` リポジトリでのみ実行されます。フォークされたリポジトリでは安全ガードによりスキップされます。

## requirements.txt

Python依存関係のリストです。他のissueで実装される機能に応じて更新されます。
# JHipster差分検出・適用ツール

JHipster英語原文と日本語訳の差分検出・適用を自動化するツールセットです。

## ツール概要

### discover_changes.py
upstream英語原文と既存日本語訳との差分を検出します。

**機能:**
- difflib.SequenceMatcherを使用した高精度な差分検出
- 軽微変更の自動判定（空白・句読点のみ、トークン数ベース）
- Gemini AIによる意味変化判定（YES/NO）
- 全オペコード対応（equal/insert/delete/replace）

**使用例:**
```bash
python3 discover_changes.py source.md target.md --output diff.json
python3 discover_changes.py source.md target.md --skip-minor --api-key YOUR_GEMINI_KEY
```

### apply_changes.py
discover_changes.pyで検出された差分を既存ファイルに適用します。

**機能:**
- JSON形式の差分データを読み込み
- 全オペコード（equal/insert/delete/replace）の適用
- 自動バックアップ機能
- 適用結果の基本検証

**使用例:**
```bash
python3 apply_changes.py target.md diff.json
python3 apply_changes.py target.md diff.json --skip-minor --no-backup
```

### test_diff_system.py
全オペコードのテストを実行します。

**機能:**
- 合成フィクスチャでの全オペコードテスト
- 計算結果の妥当性検証
- 差分適用の正確性検証

**使用例:**
```bash
python3 test_diff_system.py
```

## 実装済み機能

- ✅ difflib.SequenceMatcherによる差分検出
- ✅ 全オペコード（equal/insert/delete/replace）対応
- ✅ 軽微変更判定（空白・句読点のみ、トークン数ベース）
- ✅ 差分適用機能
- ✅ テストフィクスチャとテストスイート
- ⚠️ Gemini AI意味変化判定（プレースホルダー実装）

## 軽微変更判定ロジック

以下の条件のいずれかを満たす場合、軽微変更と判定されます：

1. **空白・句読点のみの変更**: 英数字・ひらがな・カタカナ・漢字以外の文字を除去して比較し、同じ内容
2. **トークン数の類似**: 単語トークン数の差が10%以内

## ファイル構成

```
tools/
├── discover_changes.py     # 差分検出メインスクリプト
├── apply_changes.py        # 差分適用メインスクリプト
├── test_diff_system.py     # テストスイート
└── README.md              # このファイル
```

## 今後の拡張予定

- Gemini API統合による実際の意味変化判定
- より高度な軽微変更判定ロジック
- バッチ処理機能
- GUI インターフェース

## 注意事項

- ファイルはUTF-8エンコーディングで処理されます
- バックアップファイルは自動的に作成されます（--no-backupで無効化可能）
- Gemini API使用時は適切なAPIキーが必要です
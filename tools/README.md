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

### demo_workflow.py
完全なワークフローのデモンストレーションを実行します。

**使用例:**
```bash
python3 demo_workflow.py
```

## 実装済み機能

- ✅ difflib.SequenceMatcherによる差分検出
- ✅ 全オペコード（equal/insert/delete/replace）対応
- ✅ 軽微変更判定（空白・句読点のみ、トークン数ベース）
- ✅ 差分適用機能
- ✅ テストフィクスチャとテストスイート
- ✅ ヒューリスティック意味変化判定
- ✅ Gemini AI意味変化判定（テンプレート実装）

## 軽微変更判定ロジック

以下の条件のいずれかを満たす場合、軽微変更と判定されます：

1. **空白・句読点のみの変更**: 英数字・ひらがな・カタカナ・漢字以外の文字を除去して比較し、同じ内容
2. **トークン数の類似**: 単語トークン数の差が10%以内

## 意味変化判定ロジック

### ヒューリスティック判定（標準）
- 文字数変化が50%以上: 意味変化あり
- 単語数変化が30%以上: 意味変化あり
- 空文字列との比較: 意味変化あり

### Gemini AI判定（オプション）
環境変数 `GEMINI_API_KEY` を設定すると、Gemini AIによる高精度な意味変化判定が利用可能になります。

## ファイル構成

```
tools/
├── discover_changes.py     # 差分検出メインスクリプト
├── apply_changes.py        # 差分適用メインスクリプト
├── test_diff_system.py     # テストスイート
├── demo_workflow.py        # ワークフローデモ
├── gemini_integration.py   # Gemini API統合例
└── README.md              # このファイル
```

## クイックスタート

1. **差分検出とプレビュー:**
   ```bash
   python3 discover_changes.py original.md translation.md
   ```

2. **軽微変更をスキップして差分検出:**
   ```bash
   python3 discover_changes.py original.md translation.md --skip-minor
   ```

3. **差分を適用:**
   ```bash
   python3 discover_changes.py original.md translation.md -o changes.json
   python3 apply_changes.py translation.md changes.json
   ```

4. **テスト実行:**
   ```bash
   python3 test_diff_system.py
   ```

5. **デモ実行:**
   ```bash
   python3 demo_workflow.py
   ```

## 実用的なワークフロー例

### 日常的な翻訳更新
```bash
# 1. upstream英語版との差分を検出
python3 discover_changes.py upstream/english.md current/japanese.md -o changes.json --skip-minor

# 2. 意味変化のある部分のみを適用
python3 apply_changes.py current/japanese.md changes.json --skip-no-semantic

# 3. 結果を確認
git diff current/japanese.md
```

### Gemini AIを使用した高精度判定
```bash
export GEMINI_API_KEY="your-api-key-here"
python3 discover_changes.py upstream/english.md current/japanese.md --api-key $GEMINI_API_KEY
```

## 注意事項

- ファイルはUTF-8エンコーディングで処理されます
- バックアップファイルは自動的に作成されます（--no-backupで無効化可能）
- Gemini API使用時は適切なAPIキーが必要です
- 大きなファイルの処理には時間がかかる場合があります

## トラブルシューティング

### よくある問題
1. **エンコーディングエラー**: ファイルがUTF-8でない場合は事前に変換してください
2. **権限エラー**: スクリプトに実行権限があることを確認してください
3. **APIキーエラー**: Gemini API使用時は有効なAPIキーを設定してください

### ログレベルの調整
```bash
python3 discover_changes.py --help  # 使用可能なオプションを確認
```
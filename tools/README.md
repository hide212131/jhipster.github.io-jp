# Translation Alignment Verification Tool

## 概要

`verify_alignment.py` は翻訳されたファイルと元のファイルの構造的整合性を検証するツールです。行数の一致、コードフェンスの整合性、テーブル構造の比較などを行います。

## 使用方法

```bash
python3 tools/verify_alignment.py [original_file] [translated_file] [--verbose]
```

### パラメータ

- `original_file`: 元のファイルのパス
- `translated_file`: 翻訳されたファイルのパス  
- `--verbose, -v`: 詳細な出力を有効にする（オプション）

### 例

```bash
# 基本的な使用方法
python3 tools/verify_alignment.py pages/index.md pages/index.ja.md

# 詳細出力付き
python3 tools/verify_alignment.py pages/index.md pages/index.ja.md --verbose
```

## 検証項目

### エラー（非ゼロ終了の原因）

1. **行数の不一致**: 元ファイルと翻訳ファイルの行数が一致しない
2. **コードフェンスの不一致**: 
   - コードブロック数の違い
   - 言語指定の違い（例：`java` vs `python`）
3. **テーブル構造の不一致**:
   - テーブル数の違い
   - 行数の違い
   - 列数の違い
4. **ヘッダー構造の不一致**:
   - ヘッダー数の違い
   - ヘッダーレベルの違い（例：`##` vs `###`）

### 警告（終了コードに影響しない）

1. **リンク数の違い**: マークダウンリンクの数に差がある
2. **コードフェンス間隔の大きな違い**: コードブロック間の行数に大きな差がある

## 終了コード

- `0`: 全てのチェックが成功（整合性あり）
- `1`: エラーが検出された（構造的不一致あり）
- `2`: ファイルが見つからない、またはその他のシステムエラー

## 出力例

### 成功時
```
✅ All checks passed! Files are properly aligned.
```

### エラー検出時
```
❌ ERRORS FOUND:
  1. Line count mismatch: original has 39 lines, translated has 36 lines
  2. Code fence language mismatch at fence 1: original uses 'java', translated uses 'python' (starting at line 9)
  3. Table 1 row count mismatch: original has 5 rows, translated has 4 rows (starting at line 24)

⚠️  WARNINGS:
  1. Link count difference: original has 3 links, translated has 2 links

🚨 Fix the errors above before proceeding with the translation.
```

## 注意事項

- ファイルはUTF-8エンコーディングで読み込まれます
- マークダウン形式のファイルでの使用を想定しています
- コードフェンスは ` ``` ` 形式のみサポートしています
- テーブルは標準的なマークダウンテーブル形式（`|`区切り）をサポートしています
---
name: "🔍 Stage 4: 差分検出"
about: upstream/originファイル差分検出の実装
title: "[Stage 4] 差分検出 discover_changes.py"
labels: ["llm-translation", "diff-detection", "core"]
assignees: []
---

## 📋 タスク概要
discover_changes.pyによるupstream/origin間の差分検出とopcodes生成

## 🎯 受入基準 (DoD)
- [ ] フィクスチャテストで4種の変更（equal/insert/delete/replace）をすべて通過
- [ ] 非対象ファイルは `copy_only` として分類される
- [ ] 対象ファイルは適切な opcode レンジで列挙される
- [ ] JSON出力形式が正しい

## 📁 対象ファイル
- [ ] `tools/discover_changes.py`
- [ ] `tools/line_diff.py`
- [ ] `tools/file_filters.py`
- [ ] `test_discover_changes.py`

## ✅ 実装内容
- [ ] upstream ref指定機能
- [ ] translation-metaブランチ連携
- [ ] 4種類の変更検出 (equal/insert/delete/replace)
- [ ] 軽微変更の自動判定 (SequenceMatcher.ratio ≥ 0.98)
- [ ] 非対象ファイルのcopy_only分類

## 🧪 テスト方法
```bash
# 基本テスト
python test_discover_changes.py

# CLI テスト
python discover_changes.py --upstream-ref upstream/main --meta-branch translation-meta

# フィクスチャテスト（4種の変更パターン）
python -c "
import discover_changes
# equal, insert, delete, replace のテストケース実行
"
```

## 📊 出力形式
```json
{
  "changes": [
    {
      "file": "docs/example.md",
      "status": "modified",
      "operations": [
        {
          "type": "replace",
          "old_range": [10, 15],
          "new_range": [10, 20],
          "similarity": 0.85
        }
      ]
    }
  ]
}
```

## 🔗 関連資料
- [差分検出仕様](../../../tools/spec.md#5-差分分類と翻訳ポリシー)
- [SequenceMatcherドキュメント](https://docs.python.org/3/library/difflib.html)

## 📝 備考
このステップは翻訳パイプラインの心臓部です。正確な差分検出が翻訳品質を左右します。
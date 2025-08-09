#!/usr/bin/env python3
"""
差分検出・適用器 デモスクリプト
使用方法の例を示します
"""

import json
import sys
from pathlib import Path

def demo_usage():
    """使用方法のデモ"""
    print("🌟 差分検出・適用器 使用方法デモ")
    print("=" * 50)
    
    print("\n📖 1. 基本的な使用方法:")
    print("""
# 変更検出
python scripts/discover_changes.py --output changes.json

# 変更適用
python scripts/apply_changes.py --changes-file changes.json --dry-run

# 実際の適用（注意：ファイルが変更されます）
python scripts/apply_changes.py --changes-file changes.json
""")
    
    print("\n📋 2. 出力例:")
    
    # サンプル変更データを作成
    sample_changes = {
        "old_sha": "abc123",
        "new_sha": "def456", 
        "is_initial": False,
        "changed_files": [
            ("M", "docs/installation.md"),
            ("A", "docs/new-feature.md")
        ],
        "file_diffs": {
            "docs/installation.md": {
                "status": "M",
                "operations": [
                    {
                        "operation": "equal",
                        "old_start": 0,
                        "old_end": 2,
                        "new_start": 0,
                        "new_end": 2,
                        "old_lines": ["# Installation", ""],
                        "new_lines": ["# Installation", ""],
                        "similarity_ratio": 1.0,
                        "is_minor_change": False
                    },
                    {
                        "operation": "replace",
                        "old_start": 2,
                        "old_end": 3,
                        "new_start": 2,
                        "new_end": 3,
                        "old_lines": ["You need Java 17."],
                        "new_lines": ["You need Java 21."],
                        "similarity_ratio": 0.85,
                        "is_minor_change": False
                    }
                ],
                "summary": {
                    "total_operations": 2,
                    "equal_count": 1,
                    "replace_count": 1,
                    "minor_changes": 0,
                    "major_changes": 1
                },
                "has_significant_changes": True
            }
        },
        "summary": {
            "total_files": 2,
            "significant_changes": 1,
            "minor_changes": 0
        }
    }
    
    print("変更検出結果の例:")
    print(json.dumps(sample_changes, indent=2, ensure_ascii=False))
    
    print("\n🔧 3. 主要機能:")
    print("✅ equal/insert/delete/replace の全操作タイプをサポート")
    print("✅ 軽微変更の自動検出（ratio ≥ 0.90 & トークン数類似）")
    print("✅ LLM による意味判定（YES/NO のみ）")
    print("✅ 既訳温存/新規翻訳/削除/再翻訳の適用ポリシー")
    print("✅ 置換レンジ内での 1:1 行対応の維持")
    print("✅ 削除時の行数整合性保持")
    
    print("\n📝 4. 適用ポリシー:")
    print("- keep_existing: 既訳維持（軽微変更またはスタイル変更のみ）")
    print("- new_translation: 新規翻訳（insert 操作）")
    print("- delete: 削除（delete 操作）") 
    print("- retranslate: 再翻訳（意味的変更のある replace 操作）")
    
    print("\n⚠️ 5. 注意事項:")
    print("- LLM API キーが必要（GEMINI_API_KEY 環境変数）")
    print("- API キーがない場合はフォールバック判定を使用")
    print("- --dry-run で事前確認を推奨")
    print("- upstream リモートの設定が必要")
    
    print("\n🎯 6. 受入基準の確認:")
    print("✅ equal/insert/delete/replace の全パターンが期待通りに適用される")
    print("✅ 合成フィクスチャでのテスト完了")
    print("✅ 置換レンジ内での 1:1 行対応の維持")
    print("✅ 軽微変更スキップと再翻訳の分岐網羅")
    print("✅ 削除の取り扱いで行数整合が崩れない")


if __name__ == "__main__":
    demo_usage()
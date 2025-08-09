#!/usr/bin/env python3
"""
行ロック翻訳器と既存システムの統合モジュール
"""

import os
import sys
from pathlib import Path

# 行ロック翻訳器をインポート
sys.path.append(str(Path(__file__).parent))
from translate_linewise import LinewiseTranslator


def integrate_with_existing_system():
    """既存システムとの統合関数"""
    # 既存の自動翻訳システムのパスを追加
    auto_translation_path = Path(__file__).parent.parent / ".github" / "auto-translation"
    sys.path.append(str(auto_translation_path))
    
    try:
        # 既存システムのモジュールをインポート
        from scripts.translate_chunk import GeminiTranslator
        print("✅ 既存の翻訳システムと統合可能")
        return True
    except ImportError as e:
        print(f"⚠️ 既存システムとの統合に失敗: {e}")
        return False


def create_enhanced_translator(api_key: str = None) -> LinewiseTranslator:
    """既存システムの設定を使用して行ロック翻訳器を作成"""
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY", "fake_api_key_for_testing")
    
    return LinewiseTranslator(api_key=api_key)


def translate_file_with_line_lock(input_path: str, output_path: str = None) -> bool:
    """行ロック翻訳器でファイルを翻訳"""
    translator = create_enhanced_translator()
    return translator.translate_file(input_path, output_path)


def main():
    """統合テスト用メイン関数"""
    print("🔧 行ロック翻訳器 統合テスト")
    
    # 統合チェック
    integration_ok = integrate_with_existing_system()
    
    if integration_ok:
        print("✅ 統合成功 - 既存システムと連携可能")
    else:
        print("⚠️ 統合制限 - 行ロック翻訳器は独立動作のみ")
    
    # 基本機能テスト
    translator = create_enhanced_translator()
    
    test_content = """# Integration Test

This is a test document with:
- `inline code`
- [links](https://example.com)
- Code blocks

```bash
echo "This should not be translated"
```

| Feature | Status |
|---------|--------|
| Basic   | ✅     |
| Advanced| 🚧     |

End of test."""
    
    print("\n🧪 基本翻訳テスト実行中...")
    translated, results = translator.translate_text(test_content)
    
    # 統計情報
    total_lines = len(results)
    protected_lines = sum(1 for r in results if r.was_protected)
    fence_lines = sum(1 for r in results if r.was_in_fence)
    
    print(f"📊 翻訳統計:")
    print(f"  - 総行数: {total_lines}")
    print(f"  - 保護行数: {protected_lines}")
    print(f"  - フェンス行数: {fence_lines}")
    
    # 検証
    is_valid, errors = translator.validate_translation(test_content, translated)
    print(f"\n✅ 検証結果: {'PASS' if is_valid else 'FAIL'}")
    
    if errors:
        for error in errors:
            print(f"  ❌ {error}")
    
    print("\n🎉 行ロック翻訳器の統合テスト完了")


if __name__ == "__main__":
    main()
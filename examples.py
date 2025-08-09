#!/usr/bin/env python3
"""
LLM呼び出し層の使用例

Gemini API を使った翻訳とテキスト生成のサンプル
"""

import asyncio
import os
import sys
from pathlib import Path

# tools moduleをインポートできるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from tools.llm import (
    GeminiLLM,
    LLMConfig,
    GeminiModel,
    translate_text,
    generate_text
)


async def example_translation():
    """翻訳の使用例"""
    print("=== 翻訳例 ===")
    
    # 設定（ドライランモード）
    config = LLMConfig(
        dry_run=True,  # 実際のAPI使用時はFalseにして、GEMINI_API_KEYを設定
        preferred_model=GeminiModel.FLASH,
        max_concurrent=3
    )
    
    # 翻訳テキスト
    texts = [
        "Hello, how are you today?",
        "Machine learning is fascinating.",
        "Thank you for your help."
    ]
    
    # 並列翻訳実行
    tasks = [translate_text(text, "ja", config) for text in texts]
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"原文: {texts[i]}")
        print(f"翻訳: {result.content}")
        print(f"モデル: {result.model_used}, 時間: {result.execution_time:.2f}秒")
        print()


async def example_text_generation():
    """テキスト生成の使用例"""
    print("=== テキスト生成例 ===")
    
    config = LLMConfig(dry_run=True)
    
    prompts = [
        "日本の観光地を3つ教えてください",
        "プログラミング学習のコツを教えてください",
        "美味しいラーメンの作り方を簡潔に説明してください"
    ]
    
    for prompt in prompts:
        result = await generate_text(prompt, config)
        print(f"プロンプト: {prompt}")
        print(f"生成結果: {result.content}")
        print(f"成功: {result.success}, モデル: {result.model_used}")
        print()


async def example_advanced_usage():
    """高度な使用例（カスタム設定）"""
    print("=== 高度な使用例 ===")
    
    # カスタム設定
    config = LLMConfig(
        dry_run=True,
        max_concurrent=2,  # 並列数制限
        max_retries=5,     # リトライ回数増加
        base_delay=2.0,    # リトライ間隔延長
        preferred_model=GeminiModel.PRO,  # Proモデル使用
        fallback_model=GeminiModel.FLASH
    )
    
    llm = GeminiLLM(config)
    
    # 長いテキストの翻訳
    long_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, 
    in contrast to the natural intelligence displayed by humans and animals. 
    Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize 
    its chance of successfully achieving its goals.
    """
    
    result = await llm.translate(long_text.strip(), "ja")
    
    print(f"長文翻訳結果:")
    print(f"成功: {result.success}")
    print(f"使用モデル: {result.model_used}")
    print(f"リトライ回数: {result.retry_count}")
    print(f"実行時間: {result.execution_time:.2f}秒")
    print(f"翻訳: {result.content}")


async def example_real_api_usage():
    """実際のAPI使用例（参考）"""
    print("=== 実際のAPI使用例（コメントアウト） ===")
    
    # 実際にAPIを使用する場合の例
    print("""
    # 実際のAPI使用時のコード例:
    
    # 1. 環境変数でAPI Keyを設定
    # export GEMINI_API_KEY="your_api_key_here"
    
    # 2. 実際のAPI呼び出し設定
    config = LLMConfig(
        dry_run=False,  # 実際のAPI使用
        preferred_model=GeminiModel.FLASH,
        max_concurrent=5,
        max_retries=3
    )
    
    # 3. 翻訳実行
    result = await translate_text("Hello, world!", "ja", config)
    
    if result.success:
        print(f"翻訳結果: {result.content}")
    else:
        print(f"エラー: {result.content}")
    """)


async def main():
    """メイン実行関数"""
    print("LLM呼び出し層 使用例\n")
    
    await example_translation()
    await example_text_generation()
    await example_advanced_usage()
    await example_real_api_usage()
    
    print("使用例完了")


if __name__ == "__main__":
    asyncio.run(main())
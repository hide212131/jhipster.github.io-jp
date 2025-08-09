#!/usr/bin/env python3
"""
LLM呼び出し層のテストスクリプト

ドライランモードでの動作確認とレート制御、リトライ、モデル切替のテスト
"""

import asyncio
import sys
import time
from pathlib import Path

# tools moduleをインポートできるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.llm import (
    GeminiLLM,
    LLMConfig,
    GeminiModel,
    translate_text,
    generate_text
)


async def test_dry_run():
    """ドライランモードのテスト"""
    print("=== ドライランモードテスト ===")
    
    config = LLMConfig(dry_run=True)
    llm = GeminiLLM(config)
    
    # 翻訳テスト
    response = await llm.translate("Hello, world!", "ja")
    print(f"翻訳結果: {response.success}")
    print(f"内容: {response.content}")
    print(f"使用モデル: {response.model_used}")
    print(f"実行時間: {response.execution_time:.2f}秒")
    print()


async def test_concurrent_requests():
    """並列リクエストのテスト（セマフォ動作確認）"""
    print("=== 並列リクエストテスト ===")
    
    config = LLMConfig(dry_run=True, max_concurrent=3)
    
    # 5つの並列リクエスト（セマフォで3つに制限される）
    tasks = []
    for i in range(5):
        task = translate_text(f"Test message {i+1}", "ja", config)
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"5つのリクエストを {total_time:.2f}秒で処理")
    print(f"成功数: {sum(1 for r in results if r.success)}")
    print()


async def test_model_switching():
    """モデル切替のテスト"""
    print("=== モデル切替テスト ===")
    
    # Flashモデル優先設定
    config_flash = LLMConfig(
        dry_run=True, 
        preferred_model=GeminiModel.FLASH,
        fallback_model=GeminiModel.PRO
    )
    
    # Proモデル優先設定
    config_pro = LLMConfig(
        dry_run=True,
        preferred_model=GeminiModel.PRO,
        fallback_model=GeminiModel.FLASH
    )
    
    # 両方のモデル設定でテスト
    response_flash = await generate_text("Test with Flash model", config_flash)
    response_pro = await generate_text("Test with Pro model", config_pro)
    
    print(f"Flash優先: {response_flash.model_used}")
    print(f"Pro優先: {response_pro.model_used}")
    print()


async def test_convenience_functions():
    """便利関数のテスト"""
    print("=== 便利関数テスト ===")
    
    config = LLMConfig(dry_run=True)
    
    # 翻訳便利関数
    translation = await translate_text("Hello, world!", "ja", config)
    print(f"翻訳: {translation.success}, {translation.content[:50]}...")
    
    # 生成便利関数
    generation = await generate_text("日本の首都は？", config)
    print(f"生成: {generation.success}, {generation.content[:50]}...")
    print()


async def test_error_handling():
    """エラーハンドリングのテスト"""
    print("=== エラーハンドリングテスト ===")
    
    # 無効なAPI Key設定（ドライランでないとき）
    config = LLMConfig(dry_run=False, api_key="invalid_key")
    
    try:
        llm = GeminiLLM(config)
        response = await llm.generate("Test prompt")
        print(f"エラーテスト結果: 成功={response.success}, 内容={response.content[:50]}...")
    except Exception as e:
        print(f"期待されるエラー: {e}")
    
    print()


async def main():
    """メインテスト実行"""
    print("LLM呼び出し層テスト開始\n")
    
    # 各テストを実行
    await test_dry_run()
    await test_concurrent_requests() 
    await test_model_switching()
    await test_convenience_functions()
    await test_error_handling()
    
    print("全テスト完了")


if __name__ == "__main__":
    asyncio.run(main())
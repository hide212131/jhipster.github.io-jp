#!/usr/bin/env python3
"""
LLM呼び出し層の動作テスト（乾式テスト）
"""

import os
import time
import sys
from pathlib import Path

# 環境変数設定
os.environ['GEMINI_API_KEY'] = 'fake'

# パス設定
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import get_gemini_config, create_gemini_client
from scripts.translate_chunk import GeminiTranslator


def test_rate_control():
    """レート制御のテスト"""
    print("=" * 50)
    print("レート制御テスト")
    print("=" * 50)
    
    config = get_gemini_config()
    # テスト用に制限を厳しく設定
    config.requests_per_minute = 3
    client = create_gemini_client(config, mock=True)
    
    print(f"設定: {config.requests_per_minute}リクエスト/分")
    
    start_time = time.time()
    for i in range(5):
        print(f"\nリクエスト {i+1}:")
        result = client.generate_content("テストプロンプト", f"テストコンテンツ{i+1}")
        elapsed = time.time() - start_time
        print(f"  結果: {result[:30]}...")
        print(f"  経過時間: {elapsed:.2f}秒")
    
    if hasattr(client, 'get_stats'):
        stats = client.get_stats()
        print(f"\n統計: {stats}")


def test_model_switching():
    """モデル切替のテスト"""
    print("\n" + "=" * 50)
    print("モデル切替テスト")
    print("=" * 50)
    
    config = get_gemini_config()
    client = create_gemini_client(config, mock=True)
    
    # 短文テスト
    short_content = "Hello, world!"
    print(f"\n短文テスト: '{short_content}'")
    model = config.select_model(short_content)
    print(f"選択されたモデル: {model}")
    result = client.generate_content("翻訳してください", short_content)
    print(f"結果: {result}")
    
    # 長文テスト（文字数）
    long_content = "A" * 9000
    print(f"\n長文テスト（文字数）: {len(long_content)}文字")
    model = config.select_model(long_content)
    print(f"選択されたモデル: {model}")
    result = client.generate_content("翻訳してください", long_content)
    print(f"結果: {result[:50]}...")
    
    # 長文テスト（行数）
    many_lines = "\n".join([f"Line {i+1}" for i in range(250)])
    print(f"\n長文テスト（行数）: {len(many_lines.split())}行")
    model = config.select_model(many_lines)
    print(f"選択されたモデル: {model}")
    result = client.generate_content("翻訳してください", many_lines)
    print(f"結果: {result[:50]}...")
    
    if hasattr(client, 'get_stats'):
        stats = client.get_stats()
        print(f"\n統計: {stats}")


def test_translator_integration():
    """GeminiTranslatorとの統合テスト"""
    print("\n" + "=" * 50)
    print("GeminiTranslator統合テスト")
    print("=" * 50)
    
    # 新しいLLM層を使用
    translator = GeminiTranslator(use_new_llm=True)
    
    # 短文翻訳
    short_content = "This is a short test."
    print(f"\n短文翻訳: '{short_content}'")
    result = translator.translate_chunk(short_content)
    print(f"結果: {result}")
    
    # 長文翻訳
    long_content = """
# JHipster Documentation

JHipster is a development platform to quickly generate, develop, & deploy modern web applications & microservice architectures.

We support many frontend technologies, including Angular, React, and Vue.

Our goal is to provide you with a complete toolkit for developing modern applications, from the initial generation of the application to the deployment in production.

## Features

- Full stack development
- Spring Boot backend
- Modern frontend frameworks
- Microservice support
- Docker integration
- Kubernetes deployment
- Testing support
    """.strip()
    
    print(f"\n長文翻訳: {len(long_content)}文字, {len(long_content.split())}行")
    result = translator.translate_chunk(long_content)
    print(f"結果: {result[:100]}...")
    
    # コンフリクト翻訳テスト
    conflict_content = """
# JHipster Guide

<<<<<<< HEAD
これはJHipsterガイドの日本語版です。
=======
This is the JHipster guide for beginners.
>>>>>>> upstream/main

以下の内容を説明します。
    """.strip()
    
    print(f"\nコンフリクト翻訳テスト:")
    result = translator.translate_chunk(conflict_content)
    print(f"結果: {result}")


def test_retry_mechanism():
    """リトライ機構のテスト（エラーシミュレーション）"""
    print("\n" + "=" * 50)
    print("リトライ機構テスト")
    print("=" * 50)
    
    config = get_gemini_config()
    config.base_delay = 0.1  # 短い待機時間に設定
    config.max_retries = 2
    
    # モッククライアントは常に成功するので、実際のエラーは発生しない
    # しかし設定が適用されることを確認
    client = create_gemini_client(config, mock=True)
    
    print(f"リトライ設定: 最大{config.max_retries}回, 基本遅延{config.base_delay}秒")
    
    result = client.generate_content("テストプロンプト", "テストコンテンツ")
    print(f"結果: {result}")


def main():
    """メインテスト実行"""
    print("LLM呼び出し層の動作テスト（乾式テスト）")
    print("Mock Gemini Clientを使用")
    
    try:
        test_rate_control()
        test_model_switching() 
        test_translator_integration()
        test_retry_mechanism()
        
        print("\n" + "=" * 50)
        print("✅ 全てのテストが完了しました")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
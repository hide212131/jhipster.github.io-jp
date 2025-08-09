#!/usr/bin/env python3
"""
LLM呼び出し層のテスト
"""

import os
import time
import unittest
from unittest.mock import patch, Mock
from threading import Thread

# テスト用環境設定
os.environ['GEMINI_API_KEY'] = 'test_api_key'

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.config import GeminiConfig, TranslationConfig
from tools.llm import GeminiClient, MockGeminiClient, create_gemini_client, RateLimiter


class TestGeminiConfig(unittest.TestCase):
    """Gemini設定のテスト"""
    
    def setUp(self):
        self.config = GeminiConfig(api_key="test_key")
    
    def test_model_selection_short_content(self):
        """短文でのモデル選択テスト"""
        short_content = "This is a short text."
        model = self.config.select_model(short_content)
        self.assertEqual(model, "gemini-1.5-flash")
    
    def test_model_selection_long_content_by_chars(self):
        """長文（文字数）でのモデル選択テスト"""
        long_content = "A" * 9000  # 9000文字
        model = self.config.select_model(long_content)
        self.assertEqual(model, "gemini-1.5-pro")
    
    def test_model_selection_long_content_by_lines(self):
        """長文（行数）でのモデル選択テスト"""
        long_content = "\n".join([f"Line {i}" for i in range(250)])  # 250行
        model = self.config.select_model(long_content)
        self.assertEqual(model, "gemini-1.5-pro")
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'env_test_key',
            'GEMINI_MAX_CONCURRENT': '5',
            'GEMINI_REQUESTS_PER_MINUTE': '100'
        }):
            config = GeminiConfig.from_env()
            self.assertEqual(config.api_key, 'env_test_key')
            self.assertEqual(config.max_concurrent_requests, 5)
            self.assertEqual(config.requests_per_minute, 100)


class TestRateLimiter(unittest.TestCase):
    """レート制限のテスト"""
    
    def test_rate_limiting(self):
        """レート制限の動作テスト"""
        rate_limiter = RateLimiter(requests_per_minute=2)  # 1分間に2リクエストまで
        
        # 最初の2リクエストは通る
        self.assertTrue(rate_limiter.can_proceed())
        rate_limiter.record_request()
        
        self.assertTrue(rate_limiter.can_proceed())
        rate_limiter.record_request()
        
        # 3つ目は制限される
        self.assertFalse(rate_limiter.can_proceed())
        
        # 待機時間が計算される
        wait_time = rate_limiter.wait_time()
        self.assertGreater(wait_time, 0)


class TestMockGeminiClient(unittest.TestCase):
    """モッククライアントのテスト"""
    
    def setUp(self):
        config = GeminiConfig(api_key="test_key")
        self.client = MockGeminiClient(config)
    
    def test_mock_translation(self):
        """モック翻訳のテスト"""
        prompt = "以下の英語を日本語に翻訳してください:"
        content = "Hello\nWorld"
        
        result = self.client.generate_content(prompt, content)
        
        self.assertIsNotNone(result)
        self.assertIn("翻訳されたテキスト", result)
        # 行数が保持されることを確認
        self.assertEqual(len(result.split('\n')), len(content.split('\n')))
    
    def test_model_selection_tracking(self):
        """モデル選択の追跡テスト"""
        config = GeminiConfig(api_key="test_key")
        client = MockGeminiClient(config)
        
        # 短文: flash モデル
        client.generate_content("prompt", "short text")
        
        # 長文: pro モデル
        long_content = "A" * 9000
        client.generate_content("prompt", long_content)
        
        stats = client.get_stats()
        self.assertEqual(stats["total_calls"], 2)
        self.assertIn("gemini-1.5-flash", stats["model_usage"])
        self.assertIn("gemini-1.5-pro", stats["model_usage"])
    
    def test_mock_response_formats(self):
        """モックレスポンスの形式テスト"""
        client = self.client
        
        # 翻訳プロンプト
        translation_result = client.generate_content("翻訳してください", "Test content")
        self.assertIn("翻訳されたテキスト", translation_result)
        
        # 通常プロンプト
        normal_result = client.generate_content("質問に答えてください")
        self.assertEqual(normal_result, "Mock response from Gemini")


class TestGeminiClient(unittest.TestCase):
    """実際のGeminiクライアントのテスト（モック使用）"""
    
    def setUp(self):
        self.config = GeminiConfig(api_key="test_key")
    
    @patch('tools.llm.genai.GenerativeModel')
    @patch('tools.llm.genai.configure')
    def test_client_initialization(self, mock_configure, mock_model_class):
        """クライアント初期化のテスト"""
        client = GeminiClient(self.config)
        
        mock_configure.assert_called_once_with(api_key="test_key")
        self.assertEqual(client.config, self.config)
        self.assertIsNotNone(client.semaphore)
        self.assertIsNotNone(client.rate_limiter)
    
    @patch('tools.llm.genai.GenerativeModel')
    @patch('tools.llm.genai.configure')
    def test_retry_mechanism(self, mock_configure, mock_model_class):
        """リトライ機構のテスト"""
        # モックモデルの設定
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        # 最初の2回は失敗、3回目で成功
        mock_model.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            Mock(text="成功レスポンス")
        ]
        
        client = GeminiClient(self.config)
        
        # タイムアウトを避けるため、短い遅延に設定
        client.config.base_delay = 0.01
        client.config.max_delay = 0.1
        
        result = client.generate_content("テストプロンプト", "テストコンテンツ")
        
        self.assertEqual(result, "成功レスポンス")
        self.assertEqual(mock_model.generate_content.call_count, 3)
    
    @patch('tools.llm.genai.GenerativeModel')
    @patch('tools.llm.genai.configure')
    def test_exponential_backoff(self, mock_configure, mock_model_class):
        """指数バックオフのテスト"""
        client = GeminiClient(self.config)
        
        # 遅延計算のテスト
        delay1 = client._calculate_delay(0)  # 1回目
        delay2 = client._calculate_delay(1)  # 2回目
        delay3 = client._calculate_delay(2)  # 3回目
        
        self.assertGreater(delay2, delay1)
        self.assertGreater(delay3, delay2)
        self.assertLessEqual(delay3, self.config.max_delay + self.config.jitter_max)


class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    def test_create_gemini_client_mock(self):
        """モッククライアント作成のテスト"""
        config = GeminiConfig(api_key="fake")
        client = create_gemini_client(config)
        
        self.assertIsInstance(client, MockGeminiClient)
    
    def test_create_gemini_client_real(self):
        """実クライアント作成のテスト（モック）"""
        config = GeminiConfig(api_key="real_api_key")
        
        with patch('tools.llm.genai.configure'), \
             patch('tools.llm.genai.GenerativeModel'):
            client = create_gemini_client(config)
            self.assertIsInstance(client, GeminiClient)
    
    def test_concurrent_requests(self):
        """並列リクエストのテスト"""
        config = GeminiConfig(api_key="test_key", max_concurrent_requests=2)
        client = MockGeminiClient(config)
        
        results = []
        
        def make_request(i):
            result = client.generate_content(f"プロンプト{i}", f"コンテンツ{i}")
            results.append(result)
        
        # 5つの並列スレッドを作成
        threads = []
        for i in range(5):
            thread = Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # 全てのリクエストが成功したことを確認
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsNotNone(result)
        
        # 統計情報の確認
        stats = client.get_stats()
        self.assertEqual(stats["total_calls"], 5)


if __name__ == '__main__':
    unittest.main()
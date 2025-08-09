#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム - LLM呼び出し共通層
"""

import asyncio
import random
import time
from threading import Semaphore, Lock
from typing import Optional, Dict, Any
from collections import deque
from datetime import datetime, timedelta

import google.generativeai as genai

from .config import GeminiConfig


class RateLimiter:
    """レート制限管理"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = deque()
        self.lock = Lock()
    
    def can_proceed(self) -> bool:
        """リクエスト実行可能かチェック"""
        with self.lock:
            now = datetime.now()
            # 1分以上古いリクエストを削除
            while self.requests and self.requests[0] < now - timedelta(minutes=1):
                self.requests.popleft()
            
            return len(self.requests) < self.requests_per_minute
    
    def record_request(self):
        """リクエストを記録"""
        with self.lock:
            self.requests.append(datetime.now())
    
    def wait_time(self) -> float:
        """次のリクエストまでの待機時間を計算"""
        with self.lock:
            if len(self.requests) < self.requests_per_minute:
                return 0.0
            
            # 最古のリクエストから1分後まで待機
            oldest = self.requests[0]
            wait_until = oldest + timedelta(minutes=1)
            wait_seconds = (wait_until - datetime.now()).total_seconds()
            return max(0.0, wait_seconds)


class GeminiClient:
    """Gemini API呼び出しクライアント（レート制御・リトライ・モデル切替対応）"""
    
    def __init__(self, config: GeminiConfig):
        self.config = config
        
        # API設定
        genai.configure(api_key=config.api_key)
        
        # モデルインスタンスのキャッシュ
        self._models: Dict[str, Any] = {}
        
        # 並列制御用セマフォ
        self.semaphore = Semaphore(config.max_concurrent_requests)
        
        # レート制限管理
        self.rate_limiter = RateLimiter(config.requests_per_minute)
        
        print(f"✅ Gemini client initialized with max_concurrent={config.max_concurrent_requests}, "
              f"rate_limit={config.requests_per_minute}/min")
    
    def _get_model(self, model_name: str):
        """モデルインスタンスを取得（キャッシュ付き）"""
        if model_name not in self._models:
            self._models[model_name] = genai.GenerativeModel(model_name)
        return self._models[model_name]
    
    def _calculate_delay(self, attempt: int) -> float:
        """指数バックオフによる遅延時間を計算"""
        delay = self.config.base_delay * (2 ** attempt)
        delay = min(delay, self.config.max_delay)
        
        # ジッターを追加
        jitter = random.uniform(0, self.config.jitter_max)
        return delay + jitter
    
    def _wait_for_rate_limit(self):
        """レート制限に従って待機"""
        wait_time = self.rate_limiter.wait_time()
        if wait_time > 0:
            print(f"🕐 Rate limit: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
    
    def generate_content(self, 
                        prompt: str, 
                        content: str = "", 
                        model_override: Optional[str] = None) -> Optional[str]:
        """
        コンテンツを生成
        
        Args:
            prompt: プロンプト
            content: 翻訳対象コンテンツ（モデル選択に使用）
            model_override: モデル名を強制指定
            
        Returns:
            生成されたテキスト、失敗時はNone
        """
        # モデル選択
        if model_override:
            model_name = model_override
        else:
            model_name = self.config.select_model(content or prompt)
        
        # セマフォによる並列制御
        with self.semaphore:
            return self._generate_content_with_retry(prompt, model_name)
    
    def _generate_content_with_retry(self, prompt: str, model_name: str) -> Optional[str]:
        """リトライ付きでコンテンツ生成"""
        model = self._get_model(model_name)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # レート制限チェック
                self._wait_for_rate_limit()
                
                # リクエスト実行
                print(f"🤖 Calling {model_name} (attempt {attempt + 1})")
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  # 翻訳の一貫性のため低めに設定
                    )
                )
                
                # リクエストを記録
                self.rate_limiter.record_request()
                
                if response.text:
                    return response.text.strip()
                else:
                    print(f"⚠️ Empty response from {model_name}")
                    
            except Exception as e:
                print(f"❌ Error with {model_name} (attempt {attempt + 1}): {e}")
                
                # 最後の試行でない場合は待機
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    print(f"⏳ Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        print(f"❌ All attempts failed for {model_name}")
        return None


class MockGeminiClient:
    """テスト用のモッククライアント"""
    
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.call_count = 0
        self.model_usage = {}
        print("🧪 Mock Gemini client initialized")
    
    def generate_content(self, 
                        prompt: str, 
                        content: str = "", 
                        model_override: Optional[str] = None) -> Optional[str]:
        """モック実装"""
        self.call_count += 1
        
        # モデル選択をシミュレート
        if model_override:
            model_name = model_override
        else:
            model_name = self.config.select_model(content or prompt)
        
        # 使用統計を記録
        self.model_usage[model_name] = self.model_usage.get(model_name, 0) + 1
        
        print(f"🧪 Mock call #{self.call_count} using {model_name}")
        
        # プロンプトに基づくダミーレスポンス
        if "翻訳" in prompt:
            # 入力の行数を保持してダミー翻訳を返す
            input_lines = content.split('\n') if content else prompt.split('\n')
            mock_translation = '\n'.join([f"翻訳されたテキスト_{i+1}" for i in range(len(input_lines))])
            return mock_translation
        else:
            return "Mock response from Gemini"
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "total_calls": self.call_count,
            "model_usage": self.model_usage.copy()
        }


def create_gemini_client(config: GeminiConfig, mock: bool = False) -> GeminiClient:
    """Geminiクライアントを作成"""
    if mock or config.api_key == "fake" or config.api_key.startswith("test_"):
        return MockGeminiClient(config)
    else:
        return GeminiClient(config)
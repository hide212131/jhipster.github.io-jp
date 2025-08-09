#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム - 設定管理
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeminiConfig:
    """Gemini API設定"""
    api_key: str
    
    # モデル設定
    pro_model: str = "gemini-1.5-pro"
    flash_model: str = "gemini-1.5-flash"
    default_model: str = "gemini-1.5-flash"
    
    # モデル切替閾値
    pro_threshold_chars: int = 8000  # 8000文字以上でproモデル使用
    pro_threshold_lines: int = 200   # 200行以上でproモデル使用
    
    # レート制御設定
    max_concurrent_requests: int = 3  # 並列リクエスト数上限
    requests_per_minute: int = 60     # 1分あたりのリクエスト数上限
    
    # リトライ設定
    max_retries: int = 3              # 最大リトライ回数
    base_delay: float = 1.0           # 基本待機時間（秒）
    max_delay: float = 60.0           # 最大待機時間（秒）
    jitter_max: float = 0.5           # ジッター最大値（秒）
    
    # タイムアウト設定
    request_timeout: float = 120.0    # リクエストタイムアウト（秒）

    @classmethod
    def from_env(cls) -> 'GeminiConfig':
        """環境変数から設定を作成"""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            # 環境変数による設定オーバーライド
            max_concurrent_requests=int(os.environ.get('GEMINI_MAX_CONCURRENT', 3)),
            requests_per_minute=int(os.environ.get('GEMINI_REQUESTS_PER_MINUTE', 60)),
            max_retries=int(os.environ.get('GEMINI_MAX_RETRIES', 3)),
            base_delay=float(os.environ.get('GEMINI_BASE_DELAY', 1.0)),
            pro_threshold_chars=int(os.environ.get('GEMINI_PRO_THRESHOLD_CHARS', 8000)),
            pro_threshold_lines=int(os.environ.get('GEMINI_PRO_THRESHOLD_LINES', 200)),
            request_timeout=float(os.environ.get('GEMINI_REQUEST_TIMEOUT', 120.0)),
        )

    def select_model(self, content: str) -> str:
        """内容に基づいてモデルを選択"""
        char_count = len(content)
        line_count = len(content.split('\n'))
        
        # 長文または多行の場合はproモデルを使用
        if char_count >= self.pro_threshold_chars or line_count >= self.pro_threshold_lines:
            return self.pro_model
        else:
            return self.flash_model


@dataclass
class TranslationConfig:
    """翻訳設定"""
    
    # チャンク分割設定
    max_tokens_per_chunk: int = 4096
    
    # 行数チェック設定
    line_count_tolerance: float = 0.2  # 20%の行数差まで許容
    
    # 2段階翻訳設定（コンフリクト処理）
    enable_two_stage_translation: bool = True
    
    @classmethod
    def default(cls) -> 'TranslationConfig':
        """デフォルト設定を取得"""
        return cls()


def get_gemini_config() -> GeminiConfig:
    """Gemini設定を取得"""
    return GeminiConfig.from_env()


def get_translation_config() -> TranslationConfig:
    """翻訳設定を取得"""
    return TranslationConfig.default()
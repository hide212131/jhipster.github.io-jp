"""
LLM呼び出し層（Gemini / レート制御 / リトライ / モデル切替）

Gemini API を利用した翻訳実行層の実装。
レート制御や失敗時再試行、モデル切替に対応。
"""

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

try:
    import google.generativeai as genai
except ImportError:
    # Dry-run mode when google-generativeai is not available
    genai = None

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiModel(Enum):
    """利用可能なGeminiモデル"""
    PRO = "gemini-1.5-pro"
    FLASH = "gemini-1.5-flash"


@dataclass
class LLMResponse:
    """LLM応答データクラス"""
    content: str
    model_used: str
    success: bool
    retry_count: int
    execution_time: float


@dataclass
class LLMConfig:
    """LLM設定データクラス"""
    api_key: Optional[str] = None
    max_concurrent: int = 5  # セマフォによる並列制御
    max_retries: int = 3
    base_delay: float = 1.0  # バックオフ基準遅延時間
    max_delay: float = 60.0
    timeout: float = 30.0
    dry_run: bool = False
    preferred_model: GeminiModel = GeminiModel.FLASH
    fallback_model: GeminiModel = GeminiModel.PRO


class LLMError(Exception):
    """LLM関連エラー"""
    pass


class RateLimitError(LLMError):
    """レート制限エラー"""
    pass


class ModelError(LLMError):
    """モデルエラー"""
    pass


class GeminiLLM:
    """
    Gemini API を利用したLLM呼び出し層
    
    Features:
    - セマフォによる並列化制御
    - 指数バックオフによるリトライ
    - モデル自動切替（flash → pro）
    - ドライラン対応
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        
        # API キー設定
        if not self.config.api_key:
            self.config.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.config.dry_run and not self.config.api_key:
            raise LLMError("GEMINI_API_KEY が設定されていません")
        
        # セマフォによる並列制御
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # Gemini API初期化
        if not self.config.dry_run and genai:
            genai.configure(api_key=self.config.api_key)
        elif not self.config.dry_run and not genai:
            logger.warning("google-generativeai が利用できません。ドライランモードで実行します。")
            self.config.dry_run = True
    
    async def translate(self, text: str, target_language: str = "ja") -> LLMResponse:
        """
        テキスト翻訳実行
        
        Args:
            text: 翻訳対象テキスト
            target_language: 翻訳先言語コード（デフォルト: 日本語）
        
        Returns:
            LLMResponse: 翻訳結果
        """
        prompt = f"以下のテキストを{target_language}に翻訳してください：\n\n{text}"
        return await self.generate(prompt)
    
    async def generate(self, prompt: str) -> LLMResponse:
        """
        テキスト生成実行（リトライ・モデル切替対応）
        
        Args:
            prompt: 生成プロンプト
            
        Returns:
            LLMResponse: 生成結果
        """
        async with self._semaphore:
            start_time = time.time()
            
            # ドライランモード
            if self.config.dry_run:
                return await self._dry_run_response(prompt, start_time)
            
            # 通常実行（リトライ対応）
            last_error = None
            model_to_use = self.config.preferred_model
            
            for retry_count in range(self.config.max_retries + 1):
                try:
                    response = await self._call_gemini(prompt, model_to_use)
                    execution_time = time.time() - start_time
                    
                    return LLMResponse(
                        content=response,
                        model_used=model_to_use.value,
                        success=True,
                        retry_count=retry_count,
                        execution_time=execution_time
                    )
                
                except RateLimitError as e:
                    last_error = e
                    if retry_count < self.config.max_retries:
                        delay = self._calculate_backoff_delay(retry_count)
                        logger.warning(f"レート制限エラー。{delay}秒後にリトライします。(試行回数: {retry_count + 1})")
                        await asyncio.sleep(delay)
                    continue
                    
                except ModelError as e:
                    last_error = e
                    # モデル切替
                    if model_to_use == self.config.preferred_model:
                        model_to_use = self.config.fallback_model
                        logger.warning(f"モデルを切り替えます: {self.config.preferred_model.value} → {model_to_use.value}")
                        continue
                    else:
                        # フォールバックモデルでも失敗
                        break
                        
                except Exception as e:
                    last_error = e
                    if retry_count < self.config.max_retries:
                        delay = self._calculate_backoff_delay(retry_count)
                        logger.warning(f"エラーが発生しました: {e}。{delay}秒後にリトライします。")
                        await asyncio.sleep(delay)
                    continue
            
            # 全試行失敗
            execution_time = time.time() - start_time
            logger.error(f"全ての試行が失敗しました。最後のエラー: {last_error}")
            
            return LLMResponse(
                content=f"エラー: {last_error}",
                model_used=model_to_use.value,
                success=False,
                retry_count=self.config.max_retries,
                execution_time=execution_time
            )
    
    async def _call_gemini(self, prompt: str, model: GeminiModel) -> str:
        """
        Gemini API 呼び出し
        
        Args:
            prompt: プロンプト
            model: 使用モデル
            
        Returns:
            str: 生成されたテキスト
            
        Raises:
            RateLimitError: レート制限エラー
            ModelError: モデルエラー
        """
        try:
            model_instance = genai.GenerativeModel(model.value)
            
            # タイムアウト付きでAPIコール
            response = await asyncio.wait_for(
                asyncio.to_thread(model_instance.generate_content, prompt),
                timeout=self.config.timeout
            )
            
            if not response.text:
                raise ModelError(f"空の応答が返されました (model: {model.value})")
            
            return response.text.strip()
            
        except asyncio.TimeoutError:
            raise ModelError(f"タイムアウトエラー (model: {model.value})")
            
        except Exception as e:
            error_message = str(e).lower()
            
            # レート制限判定
            if any(keyword in error_message for keyword in ["rate", "quota", "limit"]):
                raise RateLimitError(f"レート制限エラー: {e}")
            
            # モデルエラー判定
            if any(keyword in error_message for keyword in ["model", "invalid", "not found"]):
                raise ModelError(f"モデルエラー: {e}")
            
            # その他のエラー
            raise LLMError(f"API呼び出しエラー: {e}")
    
    async def _dry_run_response(self, prompt: str, start_time: float) -> LLMResponse:
        """
        ドライラン用のモック応答
        
        Args:
            prompt: プロンプト
            start_time: 開始時間
            
        Returns:
            LLMResponse: モック応答
        """
        # リアルな応答時間をシミュレート
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        execution_time = time.time() - start_time
        
        # 想定フォーマットの応答を生成
        mock_content = f"[ドライラン] プロンプト処理完了: {prompt[:50]}..."
        
        return LLMResponse(
            content=mock_content,
            model_used=self.config.preferred_model.value,
            success=True,
            retry_count=0,
            execution_time=execution_time
        )
    
    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """
        指数バックオフ遅延時間計算
        
        Args:
            retry_count: リトライ回数
            
        Returns:
            float: 遅延時間（秒）
        """
        # 指数バックオフ + ジッター
        delay = min(
            self.config.base_delay * (2 ** retry_count),
            self.config.max_delay
        )
        
        # ジッター追加（±20%）
        jitter = delay * 0.2 * (random.random() - 0.5)
        
        return max(0.1, delay + jitter)


# 便利関数
async def translate_text(text: str, target_language: str = "ja", config: Optional[LLMConfig] = None) -> LLMResponse:
    """
    テキスト翻訳の便利関数
    
    Args:
        text: 翻訳対象テキスト
        target_language: 翻訳先言語
        config: LLM設定
        
    Returns:
        LLMResponse: 翻訳結果
    """
    llm = GeminiLLM(config)
    return await llm.translate(text, target_language)


async def generate_text(prompt: str, config: Optional[LLMConfig] = None) -> LLMResponse:
    """
    テキスト生成の便利関数
    
    Args:
        prompt: 生成プロンプト
        config: LLM設定
        
    Returns:
        LLMResponse: 生成結果
    """
    llm = GeminiLLM(config)
    return await llm.generate(prompt)


# CLI実行用
if __name__ == "__main__":
    import argparse
    
    async def main():
        parser = argparse.ArgumentParser(description="Gemini LLM CLI")
        parser.add_argument("--text", required=True, help="処理対象テキスト")
        parser.add_argument("--target-lang", default="ja", help="翻訳先言語")
        parser.add_argument("--dry-run", action="store_true", help="ドライランモード")
        parser.add_argument("--model", choices=["pro", "flash"], default="flash", help="使用モデル")
        
        args = parser.parse_args()
        
        # 設定
        config = LLMConfig(
            dry_run=args.dry_run,
            preferred_model=GeminiModel.PRO if args.model == "pro" else GeminiModel.FLASH
        )
        
        # 実行
        result = await translate_text(args.text, args.target_lang, config)
        
        # 結果表示
        print(f"成功: {result.success}")
        print(f"使用モデル: {result.model_used}")
        print(f"リトライ回数: {result.retry_count}")
        print(f"実行時間: {result.execution_time:.2f}秒")
        print(f"結果:\n{result.content}")
    
    asyncio.run(main())
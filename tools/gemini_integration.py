#!/usr/bin/env python3
"""
Gemini API統合例
semantic change detectionの実装例
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiSemanticAnalyzer:
    """Gemini APIを使用した意味変化分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("No Gemini API key provided. Set GEMINI_API_KEY environment variable.")
    
    def analyze_semantic_change(self, original: str, modified: str) -> Optional[bool]:
        """
        意味変化があるかどうかをGemini AIで判定
        
        Args:
            original: 元のテキスト
            modified: 変更後のテキスト
            
        Returns:
            True: 意味変化あり
            False: 意味変化なし
            None: 判定不可
        """
        if not self.api_key:
            logger.debug("Using heuristic semantic analysis (no API key)")
            return self._simple_heuristic(original, modified)
        
        # TODO: 実際のGemini API実装
        # 以下は実装例のテンプレート
        
        try:
            prompt = self._create_prompt(original, modified)
            # response = self._call_gemini_api(prompt)
            # return self._parse_response(response)
            
            # プレースホルダー: 簡単なヒューリスティック
            return self._simple_heuristic(original, modified)
            
        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
            return None
    
    def _create_prompt(self, original: str, modified: str) -> str:
        """Gemini API用のプロンプトを作成"""
        return f"""
Please analyze if there is a semantic change between these two texts.
Answer with only "YES" if there is a meaningful semantic change, or "NO" if the change is only stylistic or minor.

Original text:
{original}

Modified text:
{modified}

Answer (YES/NO):
"""
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Gemini APIを呼び出し
        
        TODO: 実際のAPI実装
        例:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
        """
        raise NotImplementedError("Gemini API integration not yet implemented")
    
    def _parse_response(self, response: str) -> bool:
        """Gemini APIのレスポンスをパース"""
        response = response.strip().upper()
        if 'YES' in response:
            return True
        elif 'NO' in response:
            return False
        else:
            logger.warning(f"Unexpected Gemini response: {response}")
            return None
    
    def _simple_heuristic(self, original: str, modified: str) -> bool:
        """簡単なヒューリスティックによる意味変化判定"""
        if len(original.strip()) == 0 and len(modified.strip()) == 0:
            return False
        
        if len(original.strip()) == 0 or len(modified.strip()) == 0:
            return True
        
        # 文字数の大幅な変化は意味変化の可能性が高い
        len_ratio = min(len(original), len(modified)) / max(len(original), len(modified))
        
        # 50%以上の文字数変化は意味変化とみなす
        if len_ratio < 0.5:
            return True
        
        # 単語数の大幅な変化
        import re
        words1 = re.findall(r'\w+', original, re.UNICODE)
        words2 = re.findall(r'\w+', modified, re.UNICODE)
        
        if len(words1) == 0 and len(words2) == 0:
            return False
        
        if len(words1) == 0 or len(words2) == 0:
            return True
        
        word_ratio = min(len(words1), len(words2)) / max(len(words1), len(words2))
        
        # 30%以上の単語数変化は意味変化とみなす
        return word_ratio < 0.7


def test_semantic_analyzer():
    """Semantic analyzerのテスト"""
    analyzer = GeminiSemanticAnalyzer()
    
    test_cases = [
        ("Hello world", "Hello world!", False),  # 軽微な変更
        ("Hello world", "Goodbye world", True),   # 意味変化
        ("", "New content", True),                # 新規追加
        ("Old content", "", True),                # 削除
        ("This is a test", "This is a test.", False),  # 句読点のみ
    ]
    
    print("Testing Semantic Analyzer:")
    for original, modified, expected in test_cases:
        result = analyzer.analyze_semantic_change(original, modified)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{original}' -> '{modified}': {result} (expected: {expected})")


if __name__ == '__main__':
    test_semantic_analyzer()
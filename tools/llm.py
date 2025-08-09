#!/usr/bin/env python3
"""
LLM integration for JHipster translation tools.
Handles interaction with Gemini API for translation tasks.
"""

import google.generativeai as genai
from typing import List, Optional
from tools.config import config


class LLMTranslator:
    """Handles translation using Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM translator with API key."""
        self.api_key = api_key or config.get_gemini_api_key()
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "ja") -> str:
        """Translate text from source language to target language."""
        prompt = self._create_translation_prompt(text, source_lang, target_lang)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Translation failed: {e}")
    
    def translate_lines(self, lines: List[str], source_lang: str = "en", target_lang: str = "ja") -> List[str]:
        """Translate multiple lines of text."""
        if not lines:
            return []
        
        # Join lines for batch translation
        text = '\n'.join(lines)
        translated_text = self.translate_text(text, source_lang, target_lang)
        
        # Split back into lines
        return translated_text.split('\n')
    
    def _create_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """Create translation prompt for Gemini."""
        lang_names = {
            'en': 'English',
            'ja': 'Japanese'
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        return f"""Translate the following {source_name} text to {target_name}.
Preserve all markdown formatting, code blocks, links, and technical terms.
Keep the same structure and formatting as the original.

Text to translate:
{text}

Translation:"""
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        try:
            return bool(self.api_key)
        except Exception:
            return False


class MockLLMTranslator:
    """Mock translator for testing without API calls."""
    
    def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "ja") -> str:
        """Mock translation - just adds [JA] prefix."""
        return f"[JA] {text}"
    
    def translate_lines(self, lines: List[str], source_lang: str = "en", target_lang: str = "ja") -> List[str]:
        """Mock translation for multiple lines."""
        return [f"[JA] {line}" for line in lines]
    
    def is_available(self) -> bool:
        """Mock is always available."""
        return True


def get_translator(use_mock: bool = False) -> LLMTranslator:
    """Get appropriate translator instance."""
    if use_mock or not config.gemini_api_key:
        return MockLLMTranslator()
    return LLMTranslator()
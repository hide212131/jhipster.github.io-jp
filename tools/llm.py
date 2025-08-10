"""LLM interface for translation using Google Gemini."""

import time
import asyncio
from typing import List, Optional, Dict, Any
from config import config


class LLMTranslator:
    """LLM translator using Google Gemini."""
    
    def __init__(self):
        """Initialize LLM translator."""
        print("LLM translator initialized (stub implementation)")
        self.model = None
        self.retry_attempts = config.retry_max_attempts
        self.retry_delay = config.retry_delay
    
    def translate_block(self, text: str, context: str = "") -> Optional[str]:
        """Translate a single block of text."""
        print(f"Would translate: {text[:50]}...")
        # Return mock translation
        return f"[翻訳済み] {text}"
    
    def translate_batch(self, texts: List[str], context: str = "") -> List[Optional[str]]:
        """Translate multiple texts in batch."""
        print(f"Would translate batch of {len(texts)} texts")
        return [f"[翻訳済み] {text}" for text in texts]
    
    def check_semantic_change(self, original: str, modified: str) -> bool:
        """Check if modification represents semantic change requiring retranslation.
        
        This method uses LLM to determine if changes between original and modified
        text represent meaningful semantic changes that require retranslation.
        For the requirements (意味変化疑い時はLLMでYES/NO判定), this provides
        the YES/NO determination for ambiguous cases.
        
        Args:
            original: Original text content
            modified: Modified text content
            
        Returns:
            bool: True if semantic change detected (requires retranslation),
                 False if no semantic change (can preserve existing translation)
        """
        # For demo/test purposes, implement basic heuristics
        # In production, this would call actual LLM API
        
        print(f"LLM semantic change check:")
        print(f"  Original: {original[:50]}...")
        print(f"  Modified: {modified[:50]}...")
        
        # Simple heuristics for semantic change detection
        # These could be replaced with actual LLM calls in production
        
        # If texts are very similar, likely no semantic change
        import difflib
        similarity = difflib.SequenceMatcher(None, original.lower(), modified.lower()).ratio()
        if similarity >= 0.95:
            print(f"  High similarity ({similarity:.3f}) -> No semantic change")
            return False
        
        # Check for key word changes that typically indicate semantic changes
        semantic_indicators = [
            # Numbers/dates changing
            lambda o, m: any(c.isdigit() for c in o) != any(c.isdigit() for c in m),
            # Negation changes (not, no, don't, etc.)
            lambda o, m: ('not ' in o.lower()) != ('not ' in m.lower()),
            # Action words changing
            lambda o, m: len(set(o.lower().split()) & {'can', 'will', 'must', 'should'}) != 
                        len(set(m.lower().split()) & {'can', 'will', 'must', 'should'}),
            # Technical terms changing significantly  
            lambda o, m: len(set(o.lower().split()) & set(m.lower().split())) < len(o.split()) * 0.7
        ]
        
        for indicator in semantic_indicators:
            if indicator(original, modified):
                print(f"  Semantic change indicator detected -> Requires retranslation")
                return True
        
        # Default: if not clearly no change, assume semantic change for safety
        print(f"  Similarity {similarity:.3f} - assuming semantic change for safety")
        return True
    
    def _build_translation_prompt(self, text: str, context: str = "") -> str:
        """Build translation prompt."""
        return f"Translate to Japanese: {text}"
    
    def _build_batch_translation_prompt(self, texts: List[str], context: str = "") -> str:
        """Build batch translation prompt."""
        return f"Translate {len(texts)} texts to Japanese"
    
    def _parse_batch_response(self, response: str, expected_count: int) -> List[Optional[str]]:
        """Parse batch translation response."""
        return [None] * expected_count
    
    def _clean_response(self, response: str) -> str:
        """Clean LLM response."""
        return response.strip()
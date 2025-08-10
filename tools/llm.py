"""LLM interface for translation using Google Gemini."""

import time
import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from asyncio_throttle import Throttler

from config import config
from translation_cache import TranslationCache


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMTranslator:
    """LLM translator using Google Gemini with caching, batching, and retry logic."""
    
    def __init__(self):
        """Initialize LLM translator."""
        self.cache = TranslationCache()
        self.model = None
        self.retry_attempts = config.retry_max_attempts
        self.retry_delay = config.retry_delay
        self.max_concurrent = config.max_concurrent_requests
        
        # Track API calls for acceptance criteria
        self.llm_calls_count = 0
        
        # Initialize Gemini
        self._init_gemini()
        
        # Throttler for rate limiting
        self.throttler = Throttler(rate_limit=8, period=60)  # 8 requests per minute
    
    def _init_gemini(self):
        """Initialize Google Gemini model."""
        if not config.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set. Using mock mode.")
            self.model = None
            return
        
        try:
            genai.configure(api_key=config.gemini_api_key)
            
            # Configure model
            generation_config = {
                "temperature": 0.1,  # Lower temperature for consistent translations
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4096,
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",  # Using flash for better speed/cost ratio
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info("Gemini model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None
    
    async def _call_llm_api(self, prompt: str) -> Optional[str]:
        """Make actual API call to Gemini with rate limiting.
        
        Args:
            prompt: Translation prompt
            
        Returns:
            Translation result or None if failed
        """
        # Always increment call count for tracking
        self.llm_calls_count += 1
        logger.info(f"Making LLM API call #{self.llm_calls_count}")
        
        if not self.model:
            logger.warning("Model not available, using mock translation")
            # Simulate API delay
            await asyncio.sleep(0.1)
            return f"[翻訳済み(Mock)] {prompt[:100]}..."
        
        try:
            # Apply rate limiting
            async with self.throttler:
                
                # Make API call
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                
                if response.text:
                    return response.text.strip()
                else:
                    logger.warning("Empty response from Gemini")
                    return None
                    
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None
    
    def translate_block(self, text: str, context: str = "") -> Optional[str]:
        """Translate a single block of text with caching and retry.
        
        Args:
            text: Text to translate
            context: Additional context for translation
            
        Returns:
            Translated text or None if failed
        """
        # Check cache first
        cached_result = self.cache.get(text, context)
        if cached_result:
            logger.info("Cache hit for text block")
            return cached_result
        
        # Not in cache, translate
        logger.info("Cache miss, translating new text block")
        return asyncio.run(self._translate_block_async(text, context))
    
    async def _translate_block_async(self, text: str, context: str = "") -> Optional[str]:
        """Async translation with retry logic."""
        prompt = self._build_translation_prompt(text, context)
        
        for attempt in range(self.retry_attempts):
            try:
                result = await self._call_llm_api(prompt)
                if result:
                    # Clean and cache the result
                    cleaned_result = self._clean_response(result)
                    self.cache.put(text, cleaned_result, context)
                    return cleaned_result
                
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                
        logger.error(f"All {self.retry_attempts} translation attempts failed")
        return None
    
    def translate_batch(self, texts: List[str], context: str = "") -> List[Optional[str]]:
        """Translate multiple texts in batch with caching and parallel processing.
        
        Args:
            texts: List of texts to translate
            context: Additional context for all translations
            
        Returns:
            List of translations (None for failures)
        """
        if not texts:
            return []
        
        logger.info(f"Starting batch translation of {len(texts)} texts")
        
        # Check cache for all texts
        texts_with_context = [(text, context) for text in texts]
        cached_results = self.cache.batch_get(texts_with_context)
        
        # Identify texts that need translation
        texts_to_translate = []
        indices_to_translate = []
        
        for i, (text, cached_result) in enumerate(zip(texts, cached_results)):
            if cached_result is None:
                texts_to_translate.append(text)
                indices_to_translate.append(i)
        
        cache_hits = len(texts) - len(texts_to_translate)
        logger.info(f"Cache hits: {cache_hits}, Cache misses: {len(texts_to_translate)}")
        
        # If all cached, return immediately
        if not texts_to_translate:
            return cached_results
        
        # Translate remaining texts
        return asyncio.run(self._translate_batch_async(
            texts, cached_results, texts_to_translate, indices_to_translate, context
        ))
    
    async def _translate_batch_async(self, all_texts: List[str], cached_results: List[Optional[str]],
                                   texts_to_translate: List[str], indices_to_translate: List[int],
                                   context: str) -> List[Optional[str]]:
        """Async batch translation with parallelism and fallback."""
        results = cached_results[:]  # Copy cached results
        
        # Try batch processing first
        if len(texts_to_translate) > 1:
            logger.info("Attempting batch translation")
            batch_results = await self._translate_batch_parallel(texts_to_translate, context)
            
            # Apply batch results
            for i, result in enumerate(batch_results):
                results[indices_to_translate[i]] = result
            
            # Check for failures and retry individually
            failed_indices = []
            for i, result in enumerate(batch_results):
                if result is None:
                    failed_indices.append(i)
            
            if failed_indices:
                logger.info(f"Retrying {len(failed_indices)} failed texts individually")
                for i in failed_indices:
                    original_index = indices_to_translate[i]
                    text = texts_to_translate[i]
                    individual_result = await self._translate_block_async(text, context)
                    results[original_index] = individual_result
        else:
            # Single text, translate directly
            text = texts_to_translate[0]
            index = indices_to_translate[0]
            result = await self._translate_block_async(text, context)
            results[index] = result
        
        return results
    
    async def _translate_batch_parallel(self, texts: List[str], context: str) -> List[Optional[str]]:
        """Translate multiple texts in parallel with concurrency control."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def translate_single(text: str) -> Optional[str]:
            async with semaphore:
                return await self._translate_block_async(text, context)
        
        # Create tasks for all texts
        tasks = [translate_single(text) for text in texts]
        
        # Execute with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300  # 5 minute timeout
            )
            
            # Convert exceptions to None
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Parallel translation failed: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except asyncio.TimeoutError:
            logger.error("Batch translation timed out")
            return [None] * len(texts)
    
    def check_semantic_change(self, original: str, modified: str) -> bool:
        """Check if modification represents semantic change requiring retranslation.
        
        Enhanced with LLM-based analysis for ambiguous cases.
        """
        # First, apply fast heuristics
        if self._fast_semantic_check(original, modified):
            # Fast heuristics indicate semantic change
            return True
        
        # For ambiguous cases, use LLM analysis
        if self._should_use_llm_analysis(original, modified):
            logger.info("Using LLM for semantic change analysis")
            return self._llm_semantic_analysis(original, modified)
        
        # Default to no semantic change for very similar texts
        return False
    
    def _fast_semantic_check(self, original: str, modified: str) -> bool:
        """Fast heuristic-based semantic change detection."""
        import difflib
        
        # High similarity indicates no semantic change
        similarity = difflib.SequenceMatcher(None, original.lower(), modified.lower()).ratio()
        if similarity >= 0.95:
            return False
        
        # Very low similarity indicates definite semantic change
        if similarity < 0.4:
            return True
        
        # Tokenize for more detailed analysis
        orig_words = set(original.lower().split())
        mod_words = set(modified.lower().split())
        
        # Check for key indicators of semantic change
        semantic_indicators = [
            # Numbers/dates changing
            lambda: any(c.isdigit() for c in original) != any(c.isdigit() for c in modified),
            # Negation changes
            lambda: any(neg in original.lower() for neg in ['not ', 'no ', "don't", "can't", "won't"]) != 
                   any(neg in modified.lower() for neg in ['not ', 'no ', "don't", "can't", "won't"]),
            # Action words changing
            lambda: len(orig_words & {'can', 'will', 'must', 'should', 'could', 'would', 'may', 'might'}) != 
                   len(mod_words & {'can', 'will', 'must', 'should', 'could', 'would', 'may', 'might'}),
            # Antonyms detection
            lambda: self._contains_antonyms(orig_words, mod_words),
            # Significant word changes (less than 60% overlap)
            lambda: len(orig_words & mod_words) < len(orig_words | mod_words) * 0.6
        ]
        
        for indicator in semantic_indicators:
            if indicator():
                return True
        
        return False
    
    def _contains_antonyms(self, words1: set, words2: set) -> bool:
        """Check for common antonym pairs."""
        antonym_pairs = [
            ('happy', 'sad'), ('good', 'bad'), ('yes', 'no'), ('start', 'stop'),
            ('open', 'close'), ('fast', 'slow'), ('big', 'small'), ('hot', 'cold'),
            ('up', 'down'), ('in', 'out'), ('on', 'off'), ('left', 'right'),
            ('hello', 'goodbye'), ('begin', 'end'), ('first', 'last'),
            ('install', 'uninstall'), ('enable', 'disable'), ('create', 'delete')
        ]
        
        for word1, word2 in antonym_pairs:
            if (word1 in words1 and word2 in words2) or (word2 in words1 and word1 in words2):
                return True
        
        return False
    
    def _should_use_llm_analysis(self, original: str, modified: str) -> bool:
        """Determine if LLM analysis is needed for semantic change detection."""
        # Use LLM for medium-length texts with moderate similarity
        import difflib
        similarity = difflib.SequenceMatcher(None, original.lower(), modified.lower()).ratio()
        
        # Use LLM for texts in the "ambiguous" similarity range
        return 0.5 <= similarity < 0.95 and 20 <= len(original) <= 500
    
    def _llm_semantic_analysis(self, original: str, modified: str) -> bool:
        """Use LLM to analyze semantic changes."""
        prompt = f"""Compare these two texts and determine if the changes represent meaningful semantic differences that would require retranslation:

Original: {original}

Modified: {modified}

Consider:
- Do the changes affect the core meaning?
- Are there factual or numerical changes?
- Do modal verbs (can/will/must/should) change?
- Are there negation changes?

Respond with only "YES" if retranslation is needed, or "NO" if the changes are minor and don't affect meaning."""

        try:
            result = asyncio.run(self._call_llm_api(prompt))
            if result:
                response = result.strip().upper()
                return response.startswith("YES")
        except Exception as e:
            logger.warning(f"LLM semantic analysis failed: {e}")
        
        # Default to requiring retranslation on error
        return True
    
    def _build_translation_prompt(self, text: str, context: str = "") -> str:
        """Build optimized translation prompt for Gemini."""
        base_prompt = """You are a professional technical translator specializing in software documentation. Translate the following English text to natural Japanese, maintaining the same structure and technical accuracy.

Rules:
- Preserve all markdown formatting, HTML tags, and code blocks exactly
- Keep technical terms and proper nouns in English when appropriate
- Maintain the original line breaks and spacing
- Use natural Japanese expressions while staying faithful to the original meaning
- For JHipster-specific terms, use established Japanese translations if available"""

        if context:
            base_prompt += f"\n\nContext (for reference, do not translate this):\n{context}\n"
        
        base_prompt += f"\n\nText to translate:\n{text}\n\nJapanese translation:"
        
        return base_prompt
    
    def _build_batch_translation_prompt(self, texts: List[str], context: str = "") -> str:
        """Build batch translation prompt."""
        base_prompt = """You are a professional technical translator. Translate each of the following English texts to Japanese, preserving formatting and structure. Separate each translation with "---NEXT---".

Rules:
- Maintain exact formatting (markdown, HTML, etc.)
- Keep line breaks and spacing
- Use consistent terminology
- Number each translation to match the input order"""

        if context:
            base_prompt += f"\n\nContext:\n{context}\n"
        
        base_prompt += "\n\nTexts to translate:\n"
        for i, text in enumerate(texts, 1):
            base_prompt += f"\n{i}. {text}\n"
        
        base_prompt += "\nJapanese translations (separated by ---NEXT---):"
        
        return base_prompt
    
    def _parse_batch_response(self, response: str, expected_count: int) -> List[Optional[str]]:
        """Parse batch translation response."""
        if not response:
            return [None] * expected_count
        
        # Split by separator
        parts = response.split("---NEXT---")
        
        results = []
        for i in range(expected_count):
            if i < len(parts):
                cleaned = self._clean_response(parts[i])
                if cleaned:
                    results.append(cleaned)
                else:
                    results.append(None)
            else:
                results.append(None)
        
        return results
    
    def _clean_response(self, response: str) -> str:
        """Clean LLM response."""
        if not response:
            return ""
        
        # Remove common artifacts
        response = response.strip()
        
        # Remove numbering artifacts from batch responses
        import re
        response = re.sub(r'^\d+\.\s*', '', response)
        
        return response
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get translator statistics including cache performance."""
        cache_stats = self.cache.get_statistics()
        
        return {
            "llm_calls_count": self.llm_calls_count,
            "cache_stats": cache_stats,
            "model_available": self.model is not None,
            "max_concurrent": self.max_concurrent,
            "retry_attempts": self.retry_attempts,
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.llm_calls_count = 0
        self.cache.hit_count = 0
        self.cache.miss_count = 0
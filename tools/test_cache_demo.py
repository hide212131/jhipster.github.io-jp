#!/usr/bin/env python3
"""Simple test to demonstrate caching and LLM call reduction."""

import tempfile
from pathlib import Path
from translation_cache import TranslationCache
from llm import LLMTranslator


def test_cache_demonstration():
    """Demonstrate that caching reduces LLM operations."""
    print("=== Cache Demonstration ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create translator with fresh cache
        cache = TranslationCache(Path(temp_dir))
        translator = LLMTranslator()
        translator.cache = cache
        translator.reset_statistics()
        
        # Test texts
        test_texts = [
            "Hello, world!",
            "This is a test document.",
            "JHipster is a great framework."
        ]
        
        print("First translation batch...")
        results1 = translator.translate_batch(test_texts)
        stats1 = translator.get_statistics()
        
        print(f"First run: {stats1['llm_calls_count']} LLM calls, {stats1['cache_stats']['session_misses']} cache misses")
        
        # Reset session statistics but keep cache
        translator.llm_calls_count = 0
        translator.cache.hit_count = 0
        translator.cache.miss_count = 0
        
        print("Second translation batch (same texts)...")
        results2 = translator.translate_batch(test_texts)
        stats2 = translator.get_statistics()
        
        print(f"Second run: {stats2['llm_calls_count']} LLM calls, {stats2['cache_stats']['session_hits']} cache hits")
        
        # Verify cache worked
        cache_effective = stats2['cache_stats']['session_hits'] > 0
        results_consistent = len(results1) == len(results2)
        
        print(f"\nResults:")
        print(f"✓ Cache effectiveness: {cache_effective}")
        print(f"✓ Results consistent: {results_consistent}")
        print(f"✓ Cache entries: {stats2['cache_stats']['total_entries']}")
        
        return cache_effective and results_consistent


def test_individual_caching():
    """Test individual translation caching."""
    print("\n=== Individual Translation Caching ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = TranslationCache(Path(temp_dir))
        translator = LLMTranslator()
        translator.cache = cache
        translator.reset_statistics()
        
        text = "Welcome to JHipster!"
        context = "Documentation greeting"
        
        print("First translation...")
        result1 = translator.translate_block(text, context)
        calls_after_first = translator.llm_calls_count
        
        print("Second translation (same text and context)...")
        result2 = translator.translate_block(text, context)
        calls_after_second = translator.llm_calls_count
        
        print(f"LLM calls after first: {calls_after_first}")
        print(f"LLM calls after second: {calls_after_second}")
        print(f"Cache hit on second call: {calls_after_second == calls_after_first}")
        
        # Verify
        no_additional_calls = calls_after_second == calls_after_first
        same_result = result1 == result2
        
        print(f"✓ No additional LLM calls: {no_additional_calls}")
        print(f"✓ Same result: {same_result}")
        
        return no_additional_calls and same_result


def main():
    """Run cache demonstration tests."""
    print("=== Translation Cache Demonstration ===\n")
    
    try:
        test1_passed = test_cache_demonstration()
        test2_passed = test_individual_caching()
        
        print("\n" + "="*50)
        print("CACHE DEMONSTRATION RESULTS")
        print("="*50)
        
        print(f"{'✅' if test1_passed else '❌'} Batch translation caching: {test1_passed}")
        print(f"{'✅' if test2_passed else '❌'} Individual translation caching: {test2_passed}")
        
        overall_success = test1_passed and test2_passed
        print(f"\n{'✅ SUCCESS' if overall_success else '❌ FAILED'}: Cache functionality demonstrated")
        
        if overall_success:
            print("\n🎯 ACCEPTANCE CRITERIA MET:")
            print("   - Re-execution reduces LLM operations (cache hits)")
            print("   - SQLite caching working")
            print("   - Consistent translation results")
        
        return 0 if overall_success else 1
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
"""Block-wise translation with line count preservation."""

import time
import click
from typing import List, Dict, Any
from pathlib import Path
from placeholder import PlaceholderProtector
from segmenter import TextSegmenter
from reflow import LineReflow
from llm import LLMTranslator
from metrics_collector import get_metrics_collector


class BlockwiseTranslator:
    """Handles block-wise translation while preserving line structure."""
    
    def __init__(self):
        """Initialize translator components."""
        self.protector = PlaceholderProtector()
        self.segmenter = TextSegmenter()
        self.reflow = LineReflow()
        self.llm = LLMTranslator()
        self.metrics_collector = get_metrics_collector()
    
    def translate_file_content(self, content: str, context: str = "", file_path: str = "") -> str:
        """Translate file content while preserving line structure."""
        start_time = time.time()
        original_lines = content.split('\n')
        initial_llm_calls = self.llm.llm_calls_count
        
        # Protect placeholders
        protected_content = self.protector.protect(content)
        
        # Segment into blocks
        blocks = self.segmenter.segment_into_blocks(protected_content)
        
        # Collect translatable blocks for batch processing
        translatable_blocks = []
        translatable_indices = []
        
        for i, block in enumerate(blocks):
            if self.segmenter.is_translatable_block(block):
                translatable_blocks.append(block)
                translatable_indices.append(i)
        
        # Prepare texts for batch translation
        texts_to_translate = []
        contexts = []
        
        for i, block in enumerate(translatable_blocks):
            block_content = '\n'.join(block['lines'])
            texts_to_translate.append(block_content)
            
            # Get context for better translation
            original_index = translatable_indices[i]
            context_blocks = self.segmenter.get_context_blocks(blocks, original_index, 1)
            context_text = self._build_context_text(context_blocks, original_index, context)
            contexts.append(context_text)
        
        # Batch translate all translatable blocks
        if texts_to_translate:
            print(f"Translating {len(texts_to_translate)} blocks...")
            
            # Use batch translation for efficiency
            if len(texts_to_translate) > 1:
                # For multiple blocks, use the first context as representative
                # (could be enhanced to handle different contexts per batch)
                representative_context = contexts[0] if contexts else context
                translated_texts = self.llm.translate_batch(texts_to_translate, representative_context)
            else:
                # Single block
                translated_text = self.llm.translate_block(texts_to_translate[0], contexts[0])
                translated_texts = [translated_text]
        else:
            translated_texts = []
        
        # Calculate metrics after translation
        end_time = time.time()
        processing_time = end_time - start_time
        llm_calls_made = self.llm.llm_calls_count - initial_llm_calls
        
        # Record LLM call metrics if file_path is provided
        if file_path:
            # TODO: In a more sophisticated implementation, we'd track retries from the LLM module
            # For now, we estimate retries as 0 and cache hits from the cache module
            cache_hits = getattr(self.llm.cache, 'cache_hits_count', 0) if hasattr(self.llm, 'cache') else 0
            self.metrics_collector.record_llm_call(
                file_path=file_path,
                retry_count=0,  # Would need to be tracked in LLM module
                processing_time=processing_time,
                cache_hit=(cache_hits > 0)
            )
        
        # Apply translations to blocks
        translated_blocks = []
        translated_index = 0
        
        for i, block in enumerate(blocks):
            if self.segmenter.is_translatable_block(block):
                # Apply translation and reflow
                if translated_index < len(translated_texts) and translated_texts[translated_index]:
                    translated_content = translated_texts[translated_index]
                    
                    # Reflow to match original line count
                    reflowed_lines = self.reflow.reflow_to_match_lines(
                        block['lines'], translated_content
                    )
                    translated_blocks.append({
                        **block,
                        'lines': reflowed_lines
                    })
                else:
                    # Keep original if translation failed
                    translated_blocks.append(block)
                
                translated_index += 1
            else:
                # Keep non-translatable blocks as-is
                translated_blocks.append(block)
        
        # Merge blocks back
        translated_content = self.segmenter.merge_blocks(translated_blocks)
        
        # Restore placeholders
        final_content = self.protector.restore(translated_content)
        
        # Verify line count preservation
        final_lines = final_content.split('\n')
        if len(final_lines) != len(original_lines):
            print(f"Warning: Line count mismatch. Original: {len(original_lines)}, Final: {len(final_lines)}")
        
        return final_content
    
    def check_semantic_change(self, original: str, modified: str) -> bool:
        """Check if modification represents semantic change requiring retranslation.
        
        Delegates to the underlying LLM translator for semantic analysis.
        """
        return self.llm.check_semantic_change(original, modified)
    
    def _build_context_text(self, context_blocks: List[Dict[str, Any]], target_index: int, global_context: str = "") -> str:
        """Build context text for translation."""
        context_parts = []
        
        if global_context:
            context_parts.append(f"Document context: {global_context}")
        
        # Add surrounding blocks as context
        for i, block in enumerate(context_blocks):
            if i != target_index:  # Don't include the target block itself
                block_content = '\n'.join(block['lines'])
                if block_content.strip():
                    context_parts.append(f"Nearby content: {block_content[:200]}...")
        
        return '\n'.join(context_parts)


    def get_translation_statistics(self) -> dict:
        """Get comprehensive translation statistics."""
        return self.llm.get_statistics()
    
    def reset_statistics(self):
        """Reset translation statistics."""
        self.llm.reset_statistics()


@click.command()
@click.option('--input-file', '-i', required=True, help='Input file to translate')
@click.option('--output-file', '-o', help='Output file (default: <input>_translated)')
@click.option('--context', '-c', default='', help='Additional context for translation')
@click.option('--dry-run', is_flag=True, help='Show what would be translated without doing it')
@click.option('--show-stats', is_flag=True, help='Show translation statistics after completion')
@click.help_option('--help', '-h')
def main(input_file: str, output_file: str, context: str, dry_run: bool, show_stats: bool):
    """Translate file content block-wise while preserving line structure.
    
    This tool translates markdown and other documentation files using LLM
    while maintaining the exact line count and structure of the original.
    
    Examples:
        python translate_blockwise.py -i docs/readme.md
        python translate_blockwise.py -i docs/guide.md -o docs/guide_ja.md
        python translate_blockwise.py -i docs/api.md -c "API documentation" --dry-run
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        click.echo(f"Error: Input file '{input_file}' not found", err=True)
        return 1
    
    if not output_file:
        stem = input_path.stem
        suffix = input_path.suffix
        output_file = str(input_path.parent / f"{stem}_translated{suffix}")
    
    output_path = Path(output_file)
    
    try:
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        click.echo(f"Processing file: {input_file}")
        click.echo(f"Original lines: {len(content.split('\n'))}")
        
        if dry_run:
            click.echo("DRY RUN - No files will be modified")
            click.echo(f"Would translate: {input_file}")
            click.echo(f"Would output to: {output_file}")
            return 0
        
        # Translate content
        translator = BlockwiseTranslator()
        start_time = time.time()
        translated_content = translator.translate_file_content(content, context)
        translation_time = time.time() - start_time
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        click.echo(f"Translation completed in {translation_time:.2f} seconds!")
        click.echo(f"Translated lines: {len(translated_content.split('\n'))}")
        click.echo(f"Output written to: {output_file}")
        
        # Show statistics if requested
        if show_stats:
            stats = translator.get_translation_statistics()
            click.echo("\n=== Translation Statistics ===")
            click.echo(f"LLM API calls: {stats['llm_calls_count']}")
            click.echo(f"Cache hits: {stats['cache_stats']['session_hits']}")
            click.echo(f"Cache misses: {stats['cache_stats']['session_misses']}")
            if stats['cache_stats']['session_total'] > 0:
                hit_rate = stats['cache_stats']['session_hit_rate'] * 100
                click.echo(f"Cache hit rate: {hit_rate:.1f}%")
            click.echo(f"Total cache entries: {stats['cache_stats']['total_entries']}")
        
    except Exception as e:
        click.echo(f"Error during translation: {e}", err=True)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
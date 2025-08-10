"""Block-wise translation with line count preservation."""

import click
from typing import List, Dict, Any
from pathlib import Path
from placeholder import PlaceholderProtector
from segmenter import TextSegmenter
from reflow import LineReflow
from llm import LLMTranslator


class BlockwiseTranslator:
    """Handles block-wise translation while preserving line structure."""
    
    def __init__(self):
        """Initialize translator components."""
        self.protector = PlaceholderProtector()
        self.segmenter = TextSegmenter()
        self.reflow = LineReflow()
        self.llm = LLMTranslator()
    
    def translate_file_content(self, content: str, context: str = "") -> str:
        """Translate file content while preserving line structure."""
        original_lines = content.split('\n')
        
        # Protect placeholders
        protected_content = self.protector.protect(content)
        
        # Segment into blocks
        blocks = self.segmenter.segment_into_blocks(protected_content)
        
        # Translate each block
        translated_blocks = []
        for i, block in enumerate(blocks):
            if self.segmenter.is_translatable_block(block):
                # Get context for better translation
                context_blocks = self.segmenter.get_context_blocks(blocks, i, 1)
                context_text = self._build_context_text(context_blocks, i, context)
                
                # Translate block
                block_content = '\n'.join(block['lines'])
                translated_content = self.llm.translate_block(block_content, context_text)
                
                if translated_content:
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


@click.command()
@click.option('--input-file', '-i', required=True, help='Input file to translate')
@click.option('--output-file', '-o', help='Output file (default: <input>_translated)')
@click.option('--context', '-c', default='', help='Additional context for translation')
@click.option('--dry-run', is_flag=True, help='Show what would be translated without doing it')
@click.help_option('--help', '-h')
def main(input_file: str, output_file: str, context: str, dry_run: bool):
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
        output_file = str(input_path.with_suffix(f'_translated{input_path.suffix}'))
    
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
        translated_content = translator.translate_file_content(content, context)
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        click.echo(f"Translation completed!")
        click.echo(f"Translated lines: {len(translated_content.split('\n'))}")
        click.echo(f"Output written to: {output_file}")
        
    except Exception as e:
        click.echo(f"Error during translation: {e}", err=True)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
"""Text segmentation for block-wise translation."""

from typing import List, Dict, Any
import re


class TextSegmenter:
    """Segment text into blocks for translation."""
    
    def __init__(self):
        """Initialize segmenter."""
        self.block_separators = [
            r"^#{1,6}\s+",  # Headings
            r"^\s*[-*+]\s+",  # List items
            r"^\s*\d+\.\s+",  # Numbered lists
            r"^\s*>\s*",  # Blockquotes
            r"^\s*\|.*\|\s*$",  # Table rows
            r"^\s*```",  # Code fences
            r"^\s*<[^>]+>\s*$",  # HTML blocks
        ]
    
    def segment_into_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Segment text into translation blocks."""
        lines = text.split('\n')
        blocks = []
        current_block = []
        current_type = "paragraph"
        
        for i, line in enumerate(lines):
            line_type = self._detect_line_type(line)
            
            # Check if we need to start a new block
            if self._should_start_new_block(line, line_type, current_type, current_block):
                if current_block:
                    blocks.append({
                        "type": current_type,
                        "lines": current_block.copy(),
                        "line_count": len(current_block)
                    })
                    current_block = []
                current_type = line_type
            
            current_block.append(line)
            
            # Empty line always ends current block
            if line.strip() == "":
                if current_block:
                    blocks.append({
                        "type": current_type,
                        "lines": current_block.copy(),
                        "line_count": len(current_block)
                    })
                    current_block = []
                current_type = "paragraph"
        
        # Add final block
        if current_block:
            blocks.append({
                "type": current_type,
                "lines": current_block.copy(),
                "line_count": len(current_block)
            })
        
        return blocks
    
    def _detect_line_type(self, line: str) -> str:
        """Detect the type of a line."""
        stripped = line.strip()
        
        if not stripped:
            return "empty"
        
        # Check for specific patterns
        if re.match(r"^#{1,6}\s+", line):
            return "heading"
        elif re.match(r"^\s*[-*+]\s+", line):
            return "list"
        elif re.match(r"^\s*\d+\.\s+", line):
            return "numbered_list"
        elif re.match(r"^\s*>\s*", line):
            return "blockquote"
        elif re.match(r"^\s*\|.*\|\s*$", line):
            return "table"
        elif re.match(r"^\s*```", line):
            return "code_fence"
        elif re.match(r"^\s*<[^>]+>\s*$", line):
            return "html_block"
        else:
            return "paragraph"
    
    def _should_start_new_block(self, line: str, line_type: str, current_type: str, current_block: List[str]) -> bool:
        """Determine if a new block should be started."""
        # Always start new block after empty line
        if current_type == "empty":
            return True
        
        # Start new block for different types
        if line_type != current_type:
            # Exception: paragraph lines can continue in some contexts
            if current_type == "paragraph" and line_type == "paragraph":
                return False
            return True
        
        # Start new block for headings (each heading is separate)
        if line_type == "heading":
            return len(current_block) > 0
        
        # Start new block for code fences
        if line_type == "code_fence":
            return True
        
        return False
    
    def merge_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Merge blocks back into text."""
        all_lines = []
        for block in blocks:
            all_lines.extend(block["lines"])
        return '\n'.join(all_lines)
    
    def get_context_blocks(self, blocks: List[Dict[str, Any]], target_index: int, context_size: int = 2) -> List[Dict[str, Any]]:
        """Get surrounding blocks for context."""
        start_idx = max(0, target_index - context_size)
        end_idx = min(len(blocks), target_index + context_size + 1)
        return blocks[start_idx:end_idx]
    
    def is_translatable_block(self, block: Dict[str, Any]) -> bool:
        """Check if block should be translated."""
        block_type = block["type"]
        
        # Don't translate code blocks
        if block_type in ["code_fence"]:
            return False
        
        # Don't translate empty blocks
        if block_type == "empty":
            return False
        
        # Check if block contains only placeholders
        content = '\n'.join(block["lines"]).strip()
        if not content or content.startswith("__PLACEHOLDER_"):
            return False
        
        return True
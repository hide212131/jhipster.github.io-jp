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
        in_code_fence = False
        in_frontmatter = False
        code_fence_lang = ""
        
        for i, line in enumerate(lines):
            line_type = self._detect_line_type(line)
            
            # Handle frontmatter transitions
            if line_type == "frontmatter":
                if not in_frontmatter and i == 0:
                    # Starting frontmatter at beginning of file
                    in_frontmatter = True
                    current_type = "frontmatter"
                    current_block.append(line)
                elif in_frontmatter:
                    # Ending frontmatter
                    current_block.append(line)
                    blocks.append({
                        "type": current_type,
                        "lines": current_block.copy(),
                        "line_count": len(current_block)
                    })
                    current_block = []
                    in_frontmatter = False
                    current_type = "paragraph"
                else:
                    # Horizontal rule (--- not at start)
                    if current_block:
                        blocks.append({
                            "type": current_type,
                            "lines": current_block.copy(),
                            "line_count": len(current_block)
                        })
                        current_block = []
                    current_type = "paragraph"
                    current_block.append(line)
                continue
            
            # If we're inside frontmatter, everything goes into the frontmatter block
            if in_frontmatter:
                current_block.append(line)
                continue
            
            # Handle code fence transitions
            if line_type == "code_fence":
                if not in_code_fence:
                    # Starting a code fence
                    if current_block:
                        blocks.append({
                            "type": current_type,
                            "lines": current_block.copy(),
                            "line_count": len(current_block)
                        })
                        current_block = []
                    in_code_fence = True
                    current_type = "code_fence"
                    code_fence_lang = line.strip()[3:].strip()  # Extract language if present
                    current_block.append(line)
                else:
                    # Ending a code fence
                    current_block.append(line)
                    blocks.append({
                        "type": current_type,
                        "lines": current_block.copy(),
                        "line_count": len(current_block),
                        "language": code_fence_lang
                    })
                    current_block = []
                    in_code_fence = False
                    current_type = "paragraph"
                continue
            
            # If we're inside a code fence, everything goes into the code block
            if in_code_fence:
                current_block.append(line)
                continue
            
            # Check if we need to start a new block (outside code fence)
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
            
            # Empty line always ends current block (except in code fence or frontmatter)
            if line.strip() == "" and not in_code_fence and not in_frontmatter:
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
            block_info = {
                "type": current_type,
                "lines": current_block.copy(),
                "line_count": len(current_block)
            }
            if current_type == "code_fence" and code_fence_lang:
                block_info["language"] = code_fence_lang
            blocks.append(block_info)
        
        return blocks
    
    def _detect_line_type(self, line: str) -> str:
        """Detect the type of a line."""
        stripped = line.strip()
        
        if not stripped:
            return "empty"
        
        # Check for frontmatter
        if line.strip() == "---":
            return "frontmatter"
        
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
    
    def build_context_text(self, blocks: List[Dict[str, Any]], target_index: int, context_size: int = 2) -> str:
        """Build concatenated text with context for translation."""
        context_blocks = self.get_context_blocks(blocks, target_index, context_size)
        
        # Mark the target block for identification
        text_parts = []
        for i, block in enumerate(context_blocks):
            actual_index = max(0, target_index - context_size) + i
            block_text = '\n'.join(block['lines'])
            
            if actual_index == target_index:
                # Mark the target block for translation
                text_parts.append(f"__TARGET_START__\n{block_text}\n__TARGET_END__")
            else:
                # Include context blocks as-is (for reference only)
                text_parts.append(f"__CONTEXT__\n{block_text}\n__END_CONTEXT__")
        
        return '\n\n'.join(text_parts)
    
    def extract_target_from_context(self, context_text: str) -> str:
        """Extract the target text from a context-enriched translation."""
        import re
        
        # Find text between TARGET markers
        match = re.search(r'__TARGET_START__\s*(.*?)\s*__TARGET_END__', context_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: return the whole text if no markers found
        return context_text.strip()
    
    def is_translatable_block(self, block: Dict[str, Any]) -> bool:
        """Check if block should be translated."""
        block_type = block["type"]
        
        # Don't translate code blocks, frontmatter, or empty blocks
        if block_type in ["code_fence", "frontmatter", "empty"]:
            return False
        
        # Check if block contains only placeholders
        content = '\n'.join(block["lines"]).strip()
        if not content or content.startswith("__PLACEHOLDER_"):
            return False
        
        return True
"""Line reflow utilities for maintaining line count alignment."""

from typing import List
import textwrap


class LineReflow:
    """Reflow translated text to match original line structure."""
    
    def __init__(self, max_line_length: int = 120):
        """Initialize reflow with maximum line length."""
        self.max_line_length = max_line_length
    
    def reflow_to_match_lines(self, original_lines: List[str], translated_text: str) -> List[str]:
        """Reflow translated text to match original line count."""
        target_line_count = len(original_lines)
        translated_lines = translated_text.strip().split('\n')
        
        # If already matching, return as-is
        if len(translated_lines) == target_line_count:
            return translated_lines
        
        # Try different reflow strategies
        reflowed = self._reflow_with_word_wrap(translated_text, target_line_count)
        
        # If still not matching, use proportional distribution
        if len(reflowed) != target_line_count:
            reflowed = self._reflow_proportional(translated_text, target_line_count)
        
        # Last resort: pad or truncate
        if len(reflowed) != target_line_count:
            reflowed = self._adjust_line_count(reflowed, target_line_count)
        
        return reflowed
    
    def _reflow_with_word_wrap(self, text: str, target_lines: int) -> List[str]:
        """Reflow text using word wrapping to target line count."""
        # Calculate approximate width per line
        total_chars = len(text.replace('\n', ' '))
        if target_lines <= 0:
            return []
        
        width = max(20, min(self.max_line_length, total_chars // target_lines))
        
        # Wrap text
        wrapper = textwrap.TextWrapper(
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
            expand_tabs=False,
            replace_whitespace=True,
            drop_whitespace=True
        )
        
        wrapped_lines = wrapper.wrap(text.replace('\n', ' '))
        return wrapped_lines
    
    def _reflow_proportional(self, text: str, target_lines: int) -> List[str]:
        """Distribute text proportionally across target lines."""
        words = text.replace('\n', ' ').split()
        if not words:
            return [''] * target_lines
        
        if target_lines <= 0:
            return []
        
        words_per_line = len(words) / target_lines
        lines = []
        current_line_words = []
        words_count = 0
        
        for i, word in enumerate(words):
            current_line_words.append(word)
            words_count += 1
            
            # Check if we should end this line
            expected_words = int((len(lines) + 1) * words_per_line)
            if words_count >= expected_words or i == len(words) - 1:
                lines.append(' '.join(current_line_words))
                current_line_words = []
                
                # Stop if we've reached target lines
                if len(lines) >= target_lines:
                    break
        
        return lines
    
    def _adjust_line_count(self, lines: List[str], target_count: int) -> List[str]:
        """Adjust line count by padding or truncating."""
        current_count = len(lines)
        
        if current_count == target_count:
            return lines
        elif current_count < target_count:
            # Pad with empty lines
            padded_lines = lines + [''] * (target_count - current_count)
            return padded_lines
        else:
            # Truncate or merge lines
            if target_count == 1:
                return [' '.join(lines)]
            
            # Merge some lines to reduce count
            merged_lines = []
            lines_per_target = current_count / target_count
            
            for i in range(target_count):
                start_idx = int(i * lines_per_target)
                end_idx = int((i + 1) * lines_per_target)
                
                if i == target_count - 1:  # Last group gets remaining lines
                    end_idx = current_count
                
                group_lines = lines[start_idx:end_idx]
                merged_line = ' '.join(line.strip() for line in group_lines if line.strip())
                merged_lines.append(merged_line)
            
            return merged_lines
    
    def preserve_empty_lines(self, original_lines: List[str], reflowed_lines: List[str]) -> List[str]:
        """Preserve empty lines from original in reflowed text."""
        if len(original_lines) != len(reflowed_lines):
            return reflowed_lines
        
        result = []
        for i, (orig, reflow) in enumerate(zip(original_lines, reflowed_lines)):
            if orig.strip() == '':
                result.append('')
            else:
                result.append(reflow)
        
        return result
    
    def maintain_structure_markers(self, original_lines: List[str], reflowed_lines: List[str]) -> List[str]:
        """Maintain structural markers like list bullets, headings."""
        if len(original_lines) != len(reflowed_lines):
            return reflowed_lines
        
        result = []
        for orig, reflow in zip(original_lines, reflowed_lines):
            # Detect structure markers
            orig_stripped = orig.strip()
            
            # Heading markers
            if orig_stripped.startswith('#'):
                heading_level = len(orig_stripped) - len(orig_stripped.lstrip('#'))
                marker = '#' * heading_level + ' '
                if not reflow.startswith(marker):
                    reflow = marker + reflow.lstrip('# ')
            
            # List markers
            elif orig_stripped.startswith(('- ', '* ', '+ ')):
                marker = orig_stripped[:2]
                if not reflow.strip().startswith(marker):
                    reflow = marker + reflow.lstrip('- * + ')
            
            # Numbered list markers
            elif orig_stripped and orig_stripped[0].isdigit() and '. ' in orig_stripped:
                marker_end = orig_stripped.find('. ') + 2
                marker = orig_stripped[:marker_end]
                if not reflow.strip().startswith(marker.strip()):
                    reflow = marker + reflow.lstrip('0123456789. ')
            
            result.append(reflow)
        
        return result
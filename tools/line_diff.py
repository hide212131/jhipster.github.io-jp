"""Line-level diff operations for change detection."""

import difflib
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class DiffOperation:
    """Represents a diff operation."""
    operation: str  # 'equal', 'insert', 'delete', 'replace'
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    old_lines: List[str]
    new_lines: List[str]
    similarity_ratio: float = 0.0


class LineDiff:
    """Line-level diff operations."""
    
    def __init__(self, similarity_threshold: float = 0.98):
        """Initialize with similarity threshold for minor changes."""
        self.similarity_threshold = similarity_threshold
    
    def get_diff_operations(self, old_lines: List[str], new_lines: List[str]) -> List[DiffOperation]:
        """Get list of diff operations between old and new lines."""
        sequence_matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        operations = []
        
        for tag, old_start, old_end, new_start, new_end in sequence_matcher.get_opcodes():
            old_content = old_lines[old_start:old_end]
            new_content = new_lines[new_start:new_end]
            
            # Calculate similarity for replace operations
            similarity = 0.0
            if tag == 'replace' and old_content and new_content:
                similarity = self._calculate_similarity(old_content, new_content)
            
            operation = DiffOperation(
                operation=tag,
                old_start=old_start,
                old_end=old_end,
                new_start=new_start,
                new_end=new_end,
                old_lines=old_content,
                new_lines=new_content,
                similarity_ratio=similarity
            )
            
            operations.append(operation)
        
        return operations
    
    def _calculate_similarity(self, old_lines: List[str], new_lines: List[str]) -> float:
        """Calculate similarity between two line groups."""
        old_text = '\n'.join(old_lines)
        new_text = '\n'.join(new_lines)
        
        matcher = difflib.SequenceMatcher(None, old_text, new_text)
        return matcher.ratio()
    
    def is_minor_change(self, operation: DiffOperation) -> bool:
        """Check if a replace operation is a minor change."""
        if operation.operation != 'replace':
            return False
        
        # Check similarity ratio
        if operation.similarity_ratio >= self.similarity_threshold:
            return True
        
        # Check if only whitespace/punctuation changes
        old_text = '\n'.join(operation.old_lines).strip()
        new_text = '\n'.join(operation.new_lines).strip()
        
        # Normalize whitespace and compare
        old_normalized = ' '.join(old_text.split())
        new_normalized = ' '.join(new_text.split())
        
        if old_normalized == new_normalized:
            return True
        
        # Check if only punctuation changes
        old_alpha = ''.join(c for c in old_normalized if c.isalnum())
        new_alpha = ''.join(c for c in new_normalized if c.isalnum())
        
        if old_alpha == new_alpha:
            return True
        
        return False
    
    def classify_change_type(self, operation: DiffOperation) -> str:
        """Classify the type of change."""
        if operation.operation == 'equal':
            return 'unchanged'
        elif operation.operation == 'insert':
            return 'added'
        elif operation.operation == 'delete':
            return 'removed'
        elif operation.operation == 'replace':
            if self.is_minor_change(operation):
                return 'minor_edit'
            else:
                return 'modified'
        else:
            return 'unknown'
    
    def get_translation_strategy(self, operation: DiffOperation) -> str:
        """Get recommended translation strategy for operation."""
        change_type = self.classify_change_type(operation)
        
        if change_type == 'unchanged':
            return 'keep_existing'
        elif change_type == 'added':
            return 'translate_new'
        elif change_type == 'removed':
            return 'delete_existing'
        elif change_type == 'minor_edit':
            return 'keep_existing'
        elif change_type == 'modified':
            return 'retranslate'
        else:
            return 'retranslate'
    
    def merge_adjacent_operations(self, operations: List[DiffOperation]) -> List[DiffOperation]:
        """Merge adjacent operations of the same type."""
        if not operations:
            return operations
        
        merged = []
        current = operations[0]
        
        for next_op in operations[1:]:
            # Check if operations can be merged
            if (current.operation == next_op.operation and
                current.old_end == next_op.old_start and
                current.new_end == next_op.new_start):
                
                # Merge operations
                current = DiffOperation(
                    operation=current.operation,
                    old_start=current.old_start,
                    old_end=next_op.old_end,
                    new_start=current.new_start,
                    new_end=next_op.new_end,
                    old_lines=current.old_lines + next_op.old_lines,
                    new_lines=current.new_lines + next_op.new_lines,
                    similarity_ratio=min(current.similarity_ratio, next_op.similarity_ratio)
                )
            else:
                merged.append(current)
                current = next_op
        
        merged.append(current)
        return merged
    
    def get_diff_summary(self, operations: List[DiffOperation]) -> Dict[str, Any]:
        """Get summary of diff operations."""
        summary = {
            'total_operations': len(operations),
            'unchanged_lines': 0,
            'added_lines': 0,
            'removed_lines': 0,
            'modified_lines': 0,
            'minor_edits': 0,
            'major_changes': 0
        }
        
        for op in operations:
            change_type = self.classify_change_type(op)
            
            if change_type == 'unchanged':
                summary['unchanged_lines'] += len(op.old_lines)
            elif change_type == 'added':
                summary['added_lines'] += len(op.new_lines)
            elif change_type == 'removed':
                summary['removed_lines'] += len(op.old_lines)
            elif change_type == 'minor_edit':
                summary['minor_edits'] += 1
                summary['modified_lines'] += len(op.new_lines)
            elif change_type == 'modified':
                summary['major_changes'] += 1
                summary['modified_lines'] += len(op.new_lines)
        
        return summary
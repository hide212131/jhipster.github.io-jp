"""Line-level diff utilities for translation management."""

import difflib
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class LineDiff:
    """Represents a line-level difference."""

    operation: str  # 'equal', 'insert', 'delete', 'replace'
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    old_lines: List[str]
    new_lines: List[str]
    similarity: float = 0.0


class LineDiffAnalyzer:
    """Analyze line-level differences between files."""

    def __init__(self, similarity_threshold: float = 0.98):
        self.similarity_threshold = similarity_threshold

    def analyze_differences(self, old_content: str, new_content: str) -> List[LineDiff]:
        """Analyze differences between old and new content."""
        old_lines = old_content.splitlines(keepends=False)
        new_lines = new_content.splitlines(keepends=False)

        differ = difflib.SequenceMatcher(None, old_lines, new_lines)
        diffs = []

        for tag, old_start, old_end, new_start, new_end in differ.get_opcodes():
            old_chunk = old_lines[old_start:old_end]
            new_chunk = new_lines[new_start:new_end]

            # Calculate similarity for replace operations
            similarity = 0.0
            if tag == "replace":
                similarity = self._calculate_similarity(old_chunk, new_chunk)

            diff = LineDiff(
                operation=tag,
                old_start=old_start,
                old_end=old_end,
                new_start=new_start,
                new_end=new_end,
                old_lines=old_chunk,
                new_lines=new_chunk,
                similarity=similarity,
            )

            diffs.append(diff)

        return diffs

    def _calculate_similarity(
        self, old_lines: List[str], new_lines: List[str]
    ) -> float:
        """Calculate similarity between two sets of lines."""
        if not old_lines or not new_lines:
            return 0.0

        # Join lines and compare as text
        old_text = " ".join(old_lines)
        new_text = " ".join(new_lines)

        return difflib.SequenceMatcher(None, old_text, new_text).ratio()

    def classify_change_significance(self, diff: LineDiff) -> str:
        """Classify the significance of a change."""
        if diff.operation == "equal":
            return "no_change"
        elif diff.operation in ["insert", "delete"]:
            return "structural_change"
        elif diff.operation == "replace":
            if diff.similarity >= self.similarity_threshold:
                return "minor_change"
            else:
                return "major_change"
        else:
            return "unknown"

    def is_minor_change(self, diff: LineDiff) -> bool:
        """Check if a change is minor (typo, formatting, etc.)."""
        if diff.operation != "replace":
            return False

        # High similarity suggests minor change
        if diff.similarity >= self.similarity_threshold:
            return True

        # Check for common minor change patterns
        if len(diff.old_lines) == len(diff.new_lines) == 1:
            old_line = diff.old_lines[0]
            new_line = diff.new_lines[0]

            # Check for punctuation/spacing changes
            old_cleaned = self._clean_for_comparison(old_line)
            new_cleaned = self._clean_for_comparison(new_line)

            if old_cleaned == new_cleaned:
                return True

        return False

    def _clean_for_comparison(self, text: str) -> str:
        """Clean text for minor change comparison."""
        import re

        # Remove extra whitespace and punctuation
        cleaned = re.sub(r"[^\w\s]", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip().lower()

    def get_diff_statistics(self, diffs: List[LineDiff]) -> Dict[str, Any]:
        """Get statistics about the differences."""
        stats = {
            "total_diffs": len(diffs),
            "equal_blocks": 0,
            "insert_blocks": 0,
            "delete_blocks": 0,
            "replace_blocks": 0,
            "minor_changes": 0,
            "major_changes": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "lines_changed": 0,
        }

        for diff in diffs:
            if diff.operation == "equal":
                stats["equal_blocks"] += 1
            elif diff.operation == "insert":
                stats["insert_blocks"] += 1
                stats["lines_added"] += len(diff.new_lines)
            elif diff.operation == "delete":
                stats["delete_blocks"] += 1
                stats["lines_removed"] += len(diff.old_lines)
            elif diff.operation == "replace":
                stats["replace_blocks"] += 1
                stats["lines_changed"] += max(len(diff.old_lines), len(diff.new_lines))

                if self.is_minor_change(diff):
                    stats["minor_changes"] += 1
                else:
                    stats["major_changes"] += 1

        return stats

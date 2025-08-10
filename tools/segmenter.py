"""Text segmentation utilities for block-wise translation."""

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TextBlock:
    """Represents a block of text for translation."""

    content: str
    start_line: int
    end_line: int
    block_type: str  # 'paragraph', 'heading', 'list', 'code', 'table', etc.
    translatable: bool = True


class TextSegmenter:
    """Segment text into blocks for translation while preserving structure."""

    def __init__(self):
        # Patterns for different block types
        self.heading_pattern = re.compile(r"^#+\s+")
        self.code_fence_pattern = re.compile(r"^```")
        self.list_pattern = re.compile(r"^[\s]*[-*+]\s+|^[\s]*\d+\.\s+")
        self.table_pattern = re.compile(r"^\|.*\|$")
        self.html_block_pattern = re.compile(r"^<\w+.*>$|^</\w+>$")

    def segment_text(self, text: str) -> List[TextBlock]:
        """Segment text into translation blocks."""
        lines = text.splitlines()
        blocks = []
        current_block = []
        current_type = "paragraph"
        current_translatable = True
        block_start = 0
        in_code_fence = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check for code fence
            if self.code_fence_pattern.match(line_stripped):
                # End current block
                if current_block:
                    blocks.append(
                        self._create_block(
                            current_block,
                            block_start,
                            i - 1,
                            current_type,
                            current_translatable,
                        )
                    )
                    current_block = []

                in_code_fence = not in_code_fence
                current_type = "code_fence"
                current_translatable = False
                current_block = [line]
                block_start = i
                continue

            # If in code fence, just accumulate
            if in_code_fence:
                current_block.append(line)
                continue

            # Empty line - potential block boundary
            if not line_stripped:
                current_block.append(line)
                # If next line starts new block type, end current block
                if i + 1 < len(lines) and self._is_block_boundary(lines[i + 1]):
                    if current_block:
                        blocks.append(
                            self._create_block(
                                current_block,
                                block_start,
                                i,
                                current_type,
                                current_translatable,
                            )
                        )
                        current_block = []
                        block_start = i + 1
                continue

            # Determine block type and handle transitions
            new_type, new_translatable = self._get_block_type(line)

            # If block type changes, end current block
            if new_type != current_type and current_block:
                blocks.append(
                    self._create_block(
                        current_block,
                        block_start,
                        i - 1,
                        current_type,
                        current_translatable,
                    )
                )
                current_block = []
                block_start = i

            current_type = new_type
            current_translatable = new_translatable
            current_block.append(line)

        # Add final block
        if current_block:
            blocks.append(
                self._create_block(
                    current_block,
                    block_start,
                    len(lines) - 1,
                    current_type,
                    current_translatable,
                )
            )

        return blocks

    def _is_block_boundary(self, line: str) -> bool:
        """Check if line starts a new block type."""
        line_stripped = line.strip()
        return (
            self.heading_pattern.match(line_stripped)
            or self.code_fence_pattern.match(line_stripped)
            or self.list_pattern.match(line_stripped)
            or self.table_pattern.match(line_stripped)
            or self.html_block_pattern.match(line_stripped)
        )

    def _get_block_type(self, line: str) -> Tuple[str, bool]:
        """Determine block type and translatability."""
        line_stripped = line.strip()

        if self.heading_pattern.match(line_stripped):
            return "heading", True
        elif self.code_fence_pattern.match(line_stripped):
            return "code_fence", False
        elif self.list_pattern.match(line_stripped):
            return "list", True
        elif self.table_pattern.match(line_stripped):
            return "table", True
        elif self.html_block_pattern.match(line_stripped):
            return "html", False
        else:
            return "paragraph", True

    def _create_block(
        self,
        lines: List[str],
        start: int,
        end: int,
        block_type: str,
        translatable: bool,
    ) -> TextBlock:
        """Create a TextBlock from lines."""
        content = "\n".join(lines)
        return TextBlock(
            content=content,
            start_line=start,
            end_line=end,
            block_type=block_type,
            translatable=translatable,
        )

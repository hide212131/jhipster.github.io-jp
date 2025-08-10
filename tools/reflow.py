"""Text reflow utilities to maintain line count after translation."""

from typing import List


class TextReflower:
    """Reflow translated text to match original line count."""

    def __init__(self):
        self.max_line_length = 100  # Configurable maximum line length

    def reflow_to_match_lines(
        self, translated_text: str, target_line_count: int
    ) -> str:
        """Reflow translated text to match target line count."""
        lines = translated_text.strip().split("\n")

        # If already correct line count, return as-is
        if len(lines) == target_line_count:
            return translated_text

        # If we have fewer lines, we need to break long lines
        if len(lines) < target_line_count:
            return self._break_lines_to_count(lines, target_line_count)

        # If we have more lines, we need to join short lines
        if len(lines) > target_line_count:
            return self._join_lines_to_count(lines, target_line_count)

        return translated_text

    def _break_lines_to_count(self, lines: List[str], target_count: int) -> str:
        """Break lines to reach target count."""
        result_lines = []

        for line in lines:
            # If we've reached target count, add remaining as-is
            if len(result_lines) >= target_count:
                result_lines.append(line)
                continue

            # Calculate how many lines this should become
            remaining_input = len(lines) - lines.index(line)
            remaining_target = target_count - len(result_lines)

            if remaining_input <= remaining_target:
                # We have enough target lines remaining
                result_lines.append(line)
            else:
                # Need to break this line
                broken_lines = self._break_single_line(
                    line, remaining_target // remaining_input
                )
                result_lines.extend(broken_lines)

        return "\n".join(result_lines)

    def _join_lines_to_count(self, lines: List[str], target_count: int) -> str:
        """Join lines to reach target count."""
        if target_count >= len(lines):
            return "\n".join(lines)

        result_lines = []
        lines_to_merge = len(lines) - target_count + 1

        i = 0
        while i < len(lines) and len(result_lines) < target_count:
            if len(result_lines) == target_count - 1:
                # Last target line - join all remaining
                remaining = " ".join(lines[i:])
                result_lines.append(remaining)
                break
            else:
                # Join a few lines
                merge_count = min(lines_to_merge, len(lines) - i)
                if merge_count > 1:
                    merged = " ".join(lines[i : i + merge_count])
                    result_lines.append(merged)
                    i += merge_count
                    lines_to_merge -= 1
                else:
                    result_lines.append(lines[i])
                    i += 1

        return "\n".join(result_lines)

    def _break_single_line(self, line: str, target_lines: int) -> List[str]:
        """Break a single line into multiple lines."""
        if target_lines <= 1:
            return [line]

        words = line.split()
        if len(words) <= target_lines:
            # Each word becomes a line
            return words

        # Distribute words across target lines
        words_per_line = len(words) // target_lines
        remainder = len(words) % target_lines

        result = []
        word_idx = 0

        for i in range(target_lines):
            # Some lines get extra word if there's remainder
            line_word_count = words_per_line + (1 if i < remainder else 0)
            line_words = words[word_idx : word_idx + line_word_count]
            result.append(" ".join(line_words))
            word_idx += line_word_count

        return result

    def preserve_structure_markers(self, text: str) -> str:
        """Preserve markdown structure markers when reflowing."""
        lines = text.split("\n")
        preserved_lines = []

        for line in lines:
            # Don't reflow lines that start with markdown markers
            stripped = line.strip()
            if (
                stripped.startswith("#")
                or stripped.startswith("*")
                or stripped.startswith("-")
                or stripped.startswith("+")
                or stripped.startswith("|")
                or stripped.startswith(">")
            ):
                preserved_lines.append(line)
            else:
                preserved_lines.append(line)

        return "\n".join(preserved_lines)

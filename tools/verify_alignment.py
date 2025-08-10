"""Verify alignment and structure of translated files."""

import click
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
import re
from config import config


class AlignmentVerifier:
    """Verify alignment between original and translated files."""
    
    def __init__(self):
        """Initialize alignment verifier."""
        pass
    
    def verify_file(self, original_file: str, translated_file: str) -> Dict[str, Any]:
        """Verify alignment of a single file."""
        result = {
            "file": translated_file,
            "line_count_match": False,
            "structure_match": False,
            "code_fence_match": False,
            "table_match": False,
            "trailing_spaces_match": False,
            "issues": [],
            "statistics": {
                "original_lines": 0,
                "translated_lines": 0,
                "code_fences": 0,
                "tables": 0,
                "trailing_spaces": 0
            }
        }
        
        try:
            # Read files
            with open(original_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(translated_file, 'r', encoding='utf-8') as f:
                translated_content = f.read()
            
            # Split into lines
            original_lines = original_content.split('\n')
            translated_lines = translated_content.split('\n')
            
            result["statistics"]["original_lines"] = len(original_lines)
            result["statistics"]["translated_lines"] = len(translated_lines)
            
            # Verify line count
            result["line_count_match"] = len(original_lines) == len(translated_lines)
            if not result["line_count_match"]:
                result["issues"].append(
                    f"Line count mismatch: original {len(original_lines)}, translated {len(translated_lines)}"
                )
            
            # Verify structure elements
            result["structure_match"] = self._verify_structure(original_lines, translated_lines, result)
            result["code_fence_match"] = self._verify_code_fences(original_lines, translated_lines, result)
            result["table_match"] = self._verify_tables(original_lines, translated_lines, result)
            result["trailing_spaces_match"] = self._verify_trailing_spaces(original_lines, translated_lines, result)
            
        except Exception as e:
            result["issues"].append(f"Error reading files: {e}")
        
        return result
    
    def _verify_structure(self, original_lines: List[str], translated_lines: List[str], result: Dict[str, Any]) -> bool:
        """Verify structural elements match."""
        issues = []
        
        # Process all lines, even if counts differ
        max_lines = max(len(original_lines), len(translated_lines))
        
        for i in range(max_lines):
            line_num = i + 1
            orig = original_lines[i] if i < len(original_lines) else ""
            trans = translated_lines[i] if i < len(translated_lines) else ""
            
            # Check headings
            orig_heading = re.match(r'^(#{1,6})\s+', orig)
            trans_heading = re.match(r'^(#{1,6})\s+', trans)
            
            if orig_heading and not trans_heading:
                if i >= len(translated_lines):
                    issues.append(f"Line {line_num}: Missing heading marker (translated file too short)")
                else:
                    issues.append(f"Line {line_num}: Missing heading marker in translation")
            elif not orig_heading and trans_heading:
                if i >= len(original_lines):
                    issues.append(f"Line {line_num}: Unexpected heading marker (original file too short)")
                else:
                    issues.append(f"Line {line_num}: Unexpected heading marker in translation")
            elif orig_heading and trans_heading:
                if len(orig_heading.group(1)) != len(trans_heading.group(1)):
                    issues.append(f"Line {line_num}: Heading level mismatch (original: {len(orig_heading.group(1))}, translated: {len(trans_heading.group(1))})")
            
            # Check list items
            orig_list = re.match(r'^(\s*)([-*+]|\d+\.)\s+', orig)
            trans_list = re.match(r'^(\s*)([-*+]|\d+\.)\s+', trans)
            
            if orig_list and not trans_list:
                if i >= len(translated_lines):
                    issues.append(f"Line {line_num}: Missing list marker (translated file too short)")
                else:
                    issues.append(f"Line {line_num}: Missing list marker in translation")
            elif not orig_list and trans_list:
                if i >= len(original_lines):
                    issues.append(f"Line {line_num}: Unexpected list marker (original file too short)")
                else:
                    issues.append(f"Line {line_num}: Unexpected list marker in translation")
            elif orig_list and trans_list:
                # Check indentation
                if len(orig_list.group(1)) != len(trans_list.group(1)):
                    issues.append(f"Line {line_num}: List indentation mismatch (original: {len(orig_list.group(1))}, translated: {len(trans_list.group(1))})")
            
            # Check blockquotes
            orig_quote = orig.strip().startswith('>')
            trans_quote = trans.strip().startswith('>')
            
            if orig_quote != trans_quote:
                if i >= len(translated_lines):
                    issues.append(f"Line {line_num}: Blockquote mismatch (translated file too short)")
                elif i >= len(original_lines):
                    issues.append(f"Line {line_num}: Blockquote mismatch (original file too short)")
                else:
                    issues.append(f"Line {line_num}: Blockquote mismatch")
        
        result["issues"].extend(issues)
        return len(issues) == 0
    
    def _verify_code_fences(self, original_lines: List[str], translated_lines: List[str], result: Dict[str, Any]) -> bool:
        """Verify code fence integrity."""
        issues = []
        orig_fences = []
        trans_fences = []
        
        # Collect code fence positions from both files, even if line counts differ
        for i, line in enumerate(original_lines):
            if re.match(r'^\s*```', line):
                orig_fences.append((i, line.strip()))
        
        for i, line in enumerate(translated_lines):
            if re.match(r'^\s*```', line):
                trans_fences.append((i, line.strip()))
        
        result["statistics"]["code_fences"] = len(orig_fences)
        
        # Compare fence positions and content
        if len(orig_fences) != len(trans_fences):
            issues.append(f"Code fence count mismatch: original {len(orig_fences)}, translated {len(trans_fences)}")
        
        # Check fence alignment even with different line counts
        min_fences = min(len(orig_fences), len(trans_fences))
        for i in range(min_fences):
            orig_pos, orig_fence = orig_fences[i]
            trans_pos, trans_fence = trans_fences[i]
            
            if orig_pos != trans_pos:
                issues.append(f"Code fence position mismatch at line {orig_pos + 1} (original) vs line {trans_pos + 1} (translated)")
            if orig_fence != trans_fence:
                issues.append(f"Code fence content mismatch at line {orig_pos + 1}: '{orig_fence}' vs '{trans_fence}'")
        
        # Report extra fences
        if len(orig_fences) > min_fences:
            for i in range(min_fences, len(orig_fences)):
                pos, fence = orig_fences[i]
                issues.append(f"Missing code fence in translated file: line {pos + 1} '{fence}'")
        
        if len(trans_fences) > min_fences:
            for i in range(min_fences, len(trans_fences)):
                pos, fence = trans_fences[i]
                issues.append(f"Extra code fence in translated file: line {pos + 1} '{fence}'")
        
        result["issues"].extend(issues)
        return len(issues) == 0
    
    def _verify_tables(self, original_lines: List[str], translated_lines: List[str], result: Dict[str, Any]) -> bool:
        """Verify table structure."""
        issues = []
        table_lines = 0
        
        # Process all lines, even if counts differ
        max_lines = max(len(original_lines), len(translated_lines))
        
        for i in range(max_lines):
            line_num = i + 1
            orig = original_lines[i] if i < len(original_lines) else ""
            trans = translated_lines[i] if i < len(translated_lines) else ""
            
            # Check if line contains table separators
            orig_is_table = '|' in orig
            trans_is_table = '|' in trans
            
            if orig_is_table:
                table_lines += 1
                
                if not trans_is_table:
                    if i >= len(translated_lines):
                        issues.append(f"Line {line_num}: Missing table structure (translated file too short)")
                    else:
                        issues.append(f"Line {line_num}: Missing table structure in translation")
                else:
                    # Count pipe characters
                    orig_pipes = orig.count('|')
                    trans_pipes = trans.count('|')
                    
                    if orig_pipes != trans_pipes:
                        issues.append(f"Line {line_num}: Table column count mismatch ({orig_pipes} vs {trans_pipes})")
                    
                    # Check alignment markers
                    if re.match(r'^\s*\|[\s:|-]+\|\s*$', orig):
                        if not re.match(r'^\s*\|[\s:|-]+\|\s*$', trans):
                            issues.append(f"Line {line_num}: Table alignment row mismatch")
            elif trans_is_table:
                if i >= len(original_lines):
                    issues.append(f"Line {line_num}: Unexpected table structure (original file too short)")
                else:
                    issues.append(f"Line {line_num}: Unexpected table structure in translation")
        
        result["statistics"]["tables"] = table_lines
        result["issues"].extend(issues)
        return len(issues) == 0
    
    def _verify_trailing_spaces(self, original_lines: List[str], translated_lines: List[str], result: Dict[str, Any]) -> bool:
        """Verify trailing spaces (markdown line breaks)."""
        issues = []
        trailing_space_lines = 0
        
        # Process all lines, even if counts differ
        max_lines = max(len(original_lines), len(translated_lines))
        
        for i in range(max_lines):
            line_num = i + 1
            orig = original_lines[i] if i < len(original_lines) else ""
            trans = translated_lines[i] if i < len(translated_lines) else ""
            
            orig_trailing = orig.endswith('  ')
            trans_trailing = trans.endswith('  ')
            
            if orig_trailing:
                trailing_space_lines += 1
                
                if not trans_trailing:
                    if i >= len(translated_lines):
                        issues.append(f"Line {line_num}: Missing trailing spaces (translated file too short)")
                    else:
                        issues.append(f"Line {line_num}: Missing trailing spaces in translation")
            elif trans_trailing:
                if i >= len(original_lines):
                    issues.append(f"Line {line_num}: Unexpected trailing spaces (original file too short)")
                else:
                    issues.append(f"Line {line_num}: Unexpected trailing spaces in translation")
        
        result["statistics"]["trailing_spaces"] = trailing_space_lines
        result["issues"].extend(issues)
        return len(issues) == 0
    
    def verify_directory(self, original_dir: str, translated_dir: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Verify all files in directory."""
        if not file_patterns:
            file_patterns = ["*.md", "*.markdown", "*.mdx"]
        
        original_path = Path(original_dir)
        translated_path = Path(translated_dir)
        
        results = {
            "summary": {
                "total_files": 0,
                "passed_files": 0,
                "failed_files": 0,
                "total_issues": 0
            },
            "files": []
        }
        
        # Find all matching files
        for pattern in file_patterns:
            for original_file in original_path.rglob(pattern):
                relative_path = original_file.relative_to(original_path)
                translated_file = translated_path / relative_path
                
                if translated_file.exists():
                    file_result = self.verify_file(str(original_file), str(translated_file))
                    results["files"].append(file_result)
                    
                    results["summary"]["total_files"] += 1
                    if not file_result["issues"]:
                        results["summary"]["passed_files"] += 1
                    else:
                        results["summary"]["failed_files"] += 1
                        results["summary"]["total_issues"] += len(file_result["issues"])
        
        return results


@click.command()
@click.option('--original', '-o', required=True, help='Original file or directory')
@click.option('--translated', '-t', required=True, help='Translated file or directory')
@click.option('--output', help='Output file for verification results (default: .out/verification.json)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'summary']), default='summary', help='Output format')
@click.option('--fail-on-issues', is_flag=True, help='Exit with non-zero code if issues found')
@click.help_option('--help', '-h')
def main(original: str, translated: str, output: str, output_format: str, fail_on_issues: bool):
    """Verify alignment and structure of translated files.
    
    This tool verifies that translated files maintain the same structure,
    line count, and formatting as the original files.
    
    Examples:
        python verify_alignment.py -o docs/readme.md -t docs/readme_ja.md
        python verify_alignment.py -o docs/ -t translated_docs/ --format json
        python verify_alignment.py -o original.md -t translated.md --fail-on-issues
    """
    
    try:
        verifier = AlignmentVerifier()
        
        if not output:
            output = str(config.output_dir / "verification.json")
        
        # Check if inputs are files or directories
        original_path = Path(original)
        translated_path = Path(translated)
        
        if original_path.is_file() and translated_path.is_file():
            # Single file verification
            click.echo(f"Verifying file: {original} -> {translated}")
            results = verifier.verify_file(original, translated)
            
            # Wrap single file result in directory format
            results = {
                "summary": {
                    "total_files": 1,
                    "passed_files": 1 if not results["issues"] else 0,
                    "failed_files": 1 if results["issues"] else 0,
                    "total_issues": len(results["issues"])
                },
                "files": [results]
            }
            
        elif original_path.is_dir() and translated_path.is_dir():
            # Directory verification
            click.echo(f"Verifying directory: {original} -> {translated}")
            results = verifier.verify_directory(original, translated)
            
        else:
            click.echo("Error: Both paths must be files or both must be directories", err=True)
            return 1
        
        # Output results
        if output_format == 'json':
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            click.echo(f"Verification results written to: {output}")
        
        # Print summary
        summary = results["summary"]
        click.echo(f"\n=== Verification Summary ===")
        click.echo(f"Total files: {summary['total_files']}")
        click.echo(f"Passed: {summary['passed_files']}")
        click.echo(f"Failed: {summary['failed_files']}")
        click.echo(f"Total issues: {summary['total_issues']}")
        
        # Show issues if any
        if summary["total_issues"] > 0:
            click.echo(f"\n=== Issues Found ===")
            for file_result in results["files"]:
                if file_result["issues"]:
                    click.echo(f"\n{file_result['file']}:")
                    for issue in file_result["issues"]:
                        click.echo(f"  - {issue}")
        
        # Return appropriate exit code
        if fail_on_issues and summary["total_issues"] > 0:
            import sys
            sys.exit(1)
        
        return 0
        
    except Exception as e:
        click.echo(f"Error during verification: {e}", err=True)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
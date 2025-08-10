#!/usr/bin/env python3
"""
Verification and alignment utilities for JHipster translation tools.
Verifies translation quality and alignment with source content.
"""

from typing import List, Dict, NamedTuple, Optional
import re
from tools.placeholder import PlaceholderProcessor


class VerificationResult(NamedTuple):
    """Result of translation verification."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    score: float  # 0.0 to 1.0


class TranslationVerifier:
    """Verifies translation quality and alignment."""
    
    def __init__(self):
        """Initialize translation verifier."""
        self.placeholder_processor = PlaceholderProcessor()
    
    def verify_translation(self, original: str, translated: str) -> VerificationResult:
        """Verify a single translation."""
        warnings = []
        errors = []
        
        # Check basic structure preservation
        structure_score = self._verify_structure(original, translated, warnings, errors)
        
        # Check placeholder preservation
        placeholder_score = self._verify_placeholders(original, translated, warnings, errors)
        
        # Check format preservation
        format_score = self._verify_formatting(original, translated, warnings, errors)
        
        # Check content completeness
        completeness_score = self._verify_completeness(original, translated, warnings, errors)
        
        # Calculate overall score
        overall_score = (structure_score + placeholder_score + format_score + completeness_score) / 4
        
        # Determine if translation is valid (no errors and score above threshold)
        is_valid = len(errors) == 0 and overall_score >= 0.7
        
        return VerificationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            score=overall_score
        )
    
    def verify_batch_translations(self, translations: List[tuple]) -> Dict[str, VerificationResult]:
        """Verify multiple translations."""
        results = {}
        
        for i, (original, translated) in enumerate(translations):
            result = self.verify_translation(original, translated)
            results[f"translation_{i}"] = result
        
        return results
    
    def _verify_structure(self, original: str, translated: str, warnings: List[str], errors: List[str]) -> float:
        """Verify structural preservation (headers, lists, etc.)."""
        score = 1.0
        
        # Check markdown headers
        orig_headers = re.findall(r'^#+\s', original, re.MULTILINE)
        trans_headers = re.findall(r'^#+\s', translated, re.MULTILINE)
        
        if len(orig_headers) != len(trans_headers):
            warnings.append(f"Header count mismatch: {len(orig_headers)} vs {len(trans_headers)}")
            score -= 0.2
        
        # Check list items
        orig_lists = re.findall(r'^\s*[-*+]\s', original, re.MULTILINE)
        trans_lists = re.findall(r'^\s*[-*+]\s', translated, re.MULTILINE)
        
        if len(orig_lists) != len(trans_lists):
            warnings.append(f"List item count mismatch: {len(orig_lists)} vs {len(trans_lists)}")
            score -= 0.2
        
        return max(0.0, score)
    
    def _verify_placeholders(self, original: str, translated: str, warnings: List[str], errors: List[str]) -> float:
        """Verify placeholder preservation."""
        score = 1.0
        
        # Extract placeholders from both texts
        placeholder_patterns = [
            r'```[\s\S]*?```',  # Code blocks
            r'`[^`]+`',  # Inline code
            r'\{[^}]+\}',  # Variables
            r'<[^>]+>',  # HTML tags
        ]
        
        for pattern in placeholder_patterns:
            orig_matches = re.findall(pattern, original)
            trans_matches = re.findall(pattern, translated)
            
            if len(orig_matches) != len(trans_matches):
                errors.append(f"Placeholder pattern '{pattern}' count mismatch")
                score -= 0.3
        
        return max(0.0, score)
    
    def _verify_formatting(self, original: str, translated: str, warnings: List[str], errors: List[str]) -> float:
        """Verify formatting preservation."""
        score = 1.0
        
        # Check bold text
        orig_bold = len(re.findall(r'\*\*[^*]+\*\*', original))
        trans_bold = len(re.findall(r'\*\*[^*]+\*\*', translated))
        
        if orig_bold != trans_bold:
            warnings.append(f"Bold formatting mismatch: {orig_bold} vs {trans_bold}")
            score -= 0.1
        
        # Check italic text
        orig_italic = len(re.findall(r'\*[^*]+\*', original))
        trans_italic = len(re.findall(r'\*[^*]+\*', translated))
        
        if orig_italic != trans_italic:
            warnings.append(f"Italic formatting mismatch: {orig_italic} vs {trans_italic}")
            score -= 0.1
        
        # Check links
        orig_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original))
        trans_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', translated))
        
        if orig_links != trans_links:
            warnings.append(f"Link count mismatch: {orig_links} vs {trans_links}")
            score -= 0.2
        
        return max(0.0, score)
    
    def _verify_completeness(self, original: str, translated: str, warnings: List[str], errors: List[str]) -> float:
        """Verify translation completeness."""
        score = 1.0
        
        # Check if translation is empty
        if not translated.strip():
            errors.append("Translation is empty")
            return 0.0
        
        # Check relative length (rough heuristic)
        orig_len = len(original.strip())
        trans_len = len(translated.strip())
        
        if orig_len > 0:
            length_ratio = trans_len / orig_len
            
            # Flag if translation is suspiciously short or long
            if length_ratio < 0.3:
                warnings.append(f"Translation seems too short (ratio: {length_ratio:.2f})")
                score -= 0.3
            elif length_ratio > 3.0:
                warnings.append(f"Translation seems too long (ratio: {length_ratio:.2f})")
                score -= 0.2
        
        return max(0.0, score)
    
    def generate_verification_report(self, results: Dict[str, VerificationResult]) -> str:
        """Generate human-readable verification report."""
        lines = ["# Translation Verification Report", ""]
        
        total_translations = len(results)
        valid_translations = sum(1 for r in results.values() if r.is_valid)
        average_score = sum(r.score for r in results.values()) / total_translations if total_translations > 0 else 0
        
        lines.extend([
            f"**Total Translations:** {total_translations}",
            f"**Valid Translations:** {valid_translations} ({valid_translations/total_translations*100:.1f}%)",
            f"**Average Score:** {average_score:.2f}",
            ""
        ])
        
        # Summary by validation status
        if valid_translations < total_translations:
            lines.append("## ⚠️ Issues Found")
            for name, result in results.items():
                if not result.is_valid:
                    lines.append(f"### {name} (Score: {result.score:.2f})")
                    for error in result.errors:
                        lines.append(f"- ❌ {error}")
                    for warning in result.warnings:
                        lines.append(f"- ⚠️ {warning}")
                    lines.append("")
        
        return "\n".join(lines)
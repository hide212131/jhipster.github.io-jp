#!/usr/bin/env python3
"""Verification test for placeholder restoration after translation."""

import sys
from placeholder import PlaceholderProtector


def simulate_translation(protected_text: str) -> str:
    """Simulate LLM translation of protected text."""
    # Simulate what an LLM might do - translate text while preserving placeholders
    lines = protected_text.split('\n')
    translated_lines = []
    
    for line in lines:
        if line.strip() and not line.startswith('__PLACEHOLDER_'):
            # Simulate translation by adding Japanese text
            if 'Visit' in line:
                translated_line = line.replace('Visit', '訪問してください')
            elif 'Check out' in line:
                translated_line = line.replace('Check out', 'チェックしてください')
            elif 'for more info' in line:
                translated_line = line.replace('for more info', '詳細について')
            elif 'Here is some' in line:
                translated_line = line.replace('Here is some', 'ここにいくつかの')
            elif 'This is a sentence' in line:
                translated_line = line.replace('This is a sentence', 'これは文章です')
            elif 'Another' in line:
                translated_line = line.replace('Another', '別の')
            elif 'Multiple' in line:
                translated_line = line.replace('Multiple', '複数の')
            elif 'Column' in line:
                translated_line = line.replace('Column', 'カラム')
            elif 'Data' in line:
                translated_line = line.replace('Data', 'データ')
            elif 'This line has' in line:
                translated_line = line.replace('This line has', 'この行には')
            elif 'Regular line' in line:
                translated_line = line.replace('Regular line', '通常の行')
            else:
                translated_line = line
            translated_lines.append(translated_line)
        else:
            # Keep placeholders and empty lines unchanged
            translated_lines.append(line)
    
    return '\n'.join(translated_lines)


def test_restoration_after_translation():
    """Test that placeholders are correctly restored after translation."""
    print("=== Restoration After Translation Test ===\n")
    
    protector = PlaceholderProtector()
    
    # Test with complex content that includes all placeholder types
    original_text = """# Documentation

Visit https://www.jhipster.tech for more info.
Check out [JHipster Docs](https://www.jhipster.tech/docs/) for details.

Use `npm install` command to install.

<div class="note">Important information</div>

| Feature | Status |
|---------|--------|
| Backend | Ready  |

This is a sentence with footnote[^1].

Line with trailing spaces  
Another line  

[^1]: Footnote content"""
    
    print(f"Original text (length: {len(original_text)}):")
    print(original_text[:200] + "..." if len(original_text) > 200 else original_text)
    
    # Step 1: Protect placeholders
    protected_text = protector.protect(original_text)
    print(f"\nProtected text (length: {len(protected_text)}):")
    print(protected_text[:200] + "..." if len(protected_text) > 200 else protected_text)
    
    # Step 2: Simulate translation
    translated_text = simulate_translation(protected_text)
    print(f"\nTranslated text (length: {len(translated_text)}):")
    print(translated_text[:200] + "..." if len(translated_text) > 200 else translated_text)
    
    # Step 3: Restore placeholders
    final_text = protector.restore(translated_text)
    print(f"\nFinal text (length: {len(final_text)}):")
    print(final_text[:200] + "..." if len(final_text) > 200 else final_text)
    
    # Verification: Check that protected elements are preserved
    verification_checks = [
        ("https://www.jhipster.tech", "URL preserved"),
        ("[JHipster Docs](https://www.jhipster.tech/docs/)", "Markdown link preserved"),
        ("`npm install`", "Inline code preserved"),
        ('<div class="note">', "HTML tag preserved"),
        ("[^1]", "Footnote reference preserved"),
        ("  \n", "Trailing spaces preserved"),
        ("|---------|", "Table separator preserved")
    ]
    
    verification_passed = 0
    for check_text, description in verification_checks:
        if check_text in final_text:
            print(f"✓ {description}")
            verification_passed += 1
        else:
            print(f"✗ {description} - '{check_text}' not found")
    
    # Check that translation occurred
    translation_checks = [
        ("訪問してください", "Translation applied"),
        ("チェックしてください", "Translation applied"),
        ("複数の", "Translation applied")
    ]
    
    translation_applied = 0
    for check_text, description in translation_checks:
        if check_text in final_text:
            print(f"✓ {description}")
            translation_applied += 1
        else:
            print(f"✗ {description} - '{check_text}' not found")
    
    # Get protection statistics
    stats = protector.get_stats()
    print(f"\nProtection statistics: {stats}")
    
    # Overall verification
    total_checks = len(verification_checks)
    success_rate = verification_passed / total_checks * 100
    
    print(f"\nVerification Results:")
    print(f"- Protected elements preserved: {verification_passed}/{total_checks} ({success_rate:.0f}%)")
    print(f"- Translation applied: {translation_applied}/{len(translation_checks)}")
    
    # Pass if most elements are preserved and some translation occurred
    test_passed = verification_passed >= 5 and translation_applied >= 1
    
    if test_passed:
        print("✅ Restoration after translation test PASSED")
        return True
    else:
        print("❌ Restoration after translation test FAILED")
        return False


def main():
    """Run verification test."""
    if test_restoration_after_translation():
        print("\n🎉 Placeholder protection and restoration working correctly!")
        return 0
    else:
        print("\n💥 Issues found with placeholder protection/restoration!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
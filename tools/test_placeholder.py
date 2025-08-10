#!/usr/bin/env python3
"""Unit tests for placeholder protection and restoration."""

import sys
from placeholder import PlaceholderProtector


def test_case_1_inline_code_protection():
    """Test Case 1: Inline code protection and restoration."""
    print("=== Test Case 1: Inline Code Protection ===")
    
    protector = PlaceholderProtector()
    
    test_text = """Here is some `inline code` in the text.
Multiple `code snippets` can be `protected` properly.
Even complex code like `npm install --save-dev @types/node` should work."""
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original: {test_text[:50]}...")
    print(f"Protected: {protected[:100]}...")
    
    # Verify placeholders are created
    assert "__PLACEHOLDER_INLINE_CODE_" in protected
    assert "`inline code`" not in protected
    assert "`code snippets`" not in protected
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored: {restored[:50]}...")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Test Case 1 passed")
    return True


def test_case_2_url_and_markdown_links():
    """Test Case 2: URL and Markdown link protection."""
    print("\n=== Test Case 2: URLs and Markdown Links ===")
    
    protector = PlaceholderProtector()
    
    test_text = """Visit https://www.jhipster.tech for more info.
Check out [JHipster Documentation](https://www.jhipster.tech/documentation-archive/) for details.
Multiple URLs: https://github.com/jhipster/generator-jhipster and https://spring.io are useful."""
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original: {test_text[:60]}...")
    print(f"Protected: {protected[:100]}...")
    
    # Verify placeholders are created
    assert "__PLACEHOLDER_" in protected
    assert "https://www.jhipster.tech" not in protected
    assert "[JHipster Documentation](https://www.jhipster.tech/documentation-archive/)" not in protected
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored: {restored[:60]}...")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Test Case 2 passed")
    return True


def test_case_3_html_attributes():
    """Test Case 3: HTML tag and attribute protection."""
    print("\n=== Test Case 3: HTML Attributes ===")
    
    protector = PlaceholderProtector()
    
    test_text = """Here is some HTML: <div class="container">
<a href="https://example.com" target="_blank">Link</a>
<img src="/path/to/image.jpg" alt="Description" />
<span id="unique-id" data-value="123">Text</span>"""
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original: {test_text[:50]}...")
    print(f"Protected: {protected[:100]}...")
    
    # Verify placeholders are created
    assert "__PLACEHOLDER_HTML_TAG_" in protected
    assert '<div class="container">' not in protected
    assert 'target="_blank"' not in protected
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored: {restored[:50]}...")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Test Case 3 passed")
    return True


def test_case_4_footnotes():
    """Test Case 4: Footnote reference protection."""
    print("\n=== Test Case 4: Footnote References ===")
    
    protector = PlaceholderProtector()
    
    test_text = """This is a sentence with a footnote[^1].
Another footnote reference[^note-2] is here.
Multiple footnotes[^3] can appear[^footnote-name] in text."""
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original: {test_text}")
    print(f"Protected: {protected[:100]}...")
    
    # Verify placeholders are created
    assert "__PLACEHOLDER_FOOTNOTE_" in protected
    assert "[^1]" not in protected
    assert "[^note-2]" not in protected
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored: {restored}")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Test Case 4 passed")
    return True


def test_case_5_table_separators():
    """Test Case 5: Table separator and alignment protection."""
    print("\n=== Test Case 5: Table Separators ===")
    
    protector = PlaceholderProtector()
    
    test_text = """| Column 1 | Column 2 | Column 3 |
|----------|:---------|----------:|
| Data 1   | Data 2   | Data 3    |
| More     | Content  | Here      |"""
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original table:\n{test_text}")
    print(f"Protected: {protected[:100]}...")
    
    # Verify placeholders are created
    assert "__PLACEHOLDER_TABLE_SEP_" in protected
    assert "|----------|:---------|----------|" not in protected
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored table:\n{restored}")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Test Case 5 passed")
    return True


def test_case_6_trailing_spaces():
    """Test Case 6: Trailing double spaces (markdown line breaks) protection."""
    print("\n=== Test Case 6: Trailing Spaces ===")
    
    protector = PlaceholderProtector()
    
    test_text = """This line has trailing spaces for line break  
This is the next line  
Another line with break  
Regular line without break
Final line  """
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original (showing trailing spaces): '{test_text}'")
    print(f"Protected: {protected[:100]}...")
    
    # Verify placeholders are created
    assert "__PLACEHOLDER_TRAILING_SPACES_" in protected
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored (showing trailing spaces): '{restored}'")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Test Case 6 passed")
    return True


def test_comprehensive_integration():
    """Integration test with multiple placeholder types."""
    print("\n=== Integration Test: Multiple Placeholder Types ===")
    
    protector = PlaceholderProtector()
    
    test_text = """# JHipster Documentation  

Visit the [official site](https://www.jhipster.tech) for more info.

## Installation

Run the following command:
```bash
npm install -g generator-jhipster
```

Use `jhipster --help` for options.

## Features

| Feature | Description | Status |
|---------|:------------|--------|
| Spring Boot | Backend framework | ✓ |
| Angular | Frontend framework | ✓ |

Check the footnote[^1] for details.

<div class="note">
Important: See https://github.com/jhipster/generator-jhipster for source.
</div>

[^1]: More information available online  """
    
    # Protect placeholders
    protected = protector.protect(test_text)
    print(f"Original length: {len(test_text)}")
    print(f"Protected length: {len(protected)}")
    
    # Verify various placeholder types exist
    assert "__PLACEHOLDER_" in protected
    
    # Get protection statistics
    stats = protector.get_stats()
    print(f"Protection stats: {stats}")
    
    # Restore placeholders
    restored = protector.restore(protected)
    print(f"Restored length: {len(restored)}")
    
    # Verify restoration is correct
    assert restored == test_text
    print("✓ Integration test passed")
    return True


def main():
    """Run all placeholder protection tests."""
    print("=== Placeholder Protection Unit Tests ===\n")
    
    test_functions = [
        test_case_1_inline_code_protection,
        test_case_2_url_and_markdown_links, 
        test_case_3_html_attributes,
        test_case_4_footnotes,
        test_case_5_table_separators,
        test_case_6_trailing_spaces,
        test_comprehensive_integration
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_func.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test_func.__name__} failed with error: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Total tests: {len(test_functions)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    # Acceptance criteria: All 6 core tests must pass
    core_tests_passed = passed >= 6
    print(f"\nAcceptance Criteria: {'✅ MET' if core_tests_passed else '❌ NOT MET'}")
    print("- Requirement: 6 unit tests pass")
    print(f"- Result: {passed} tests passed")
    
    if core_tests_passed:
        print("✅ All placeholder protection tests passed!")
        return 0
    else:
        print("❌ Some placeholder protection tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
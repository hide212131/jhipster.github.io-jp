# Line-wise Translation Tools

This directory contains tools for performing line-wise translation of markdown files with comprehensive placeholder protection and content preservation.

## Features

- **1 input line → 1 output line guarantee**: Preserves exact line count
- **Placeholder protection**: Protects special content during translation
- **Code fence handling**: Skips translation inside code blocks
- **Table support**: Preserves markdown table structure
- **YAML frontmatter**: Preserves Jekyll/Hugo frontmatter
- **Micro-batch format**: L000x=... format for better translation context
- **Fallback strategies**: Graceful handling of translation failures

## Files

- `placeholder.py`: Core placeholder protection and restoration logic
- `translate_linewise.py`: Main line-wise translation engine
- `cli.py`: Command-line interface
- `test_translation.py`: Comprehensive test suite

## Supported Content Protection

### Inline Elements
- Inline code: `` `console.log()` ``
- URLs: `https://www.example.com`
- Markdown links: `[text](url)`
- Jekyll variables: `{{ site.url }}`
- Jekyll tags: `{% include header.html %}`
- HTML tags: `<i class="icon"></i>`
- GitHub references: `#123`
- Version numbers: `v7.9.3`
- File paths: `config.yml`

### Block Elements
- Code fences: ``````` blocks
- Tables: `| col1 | col2 |`
- YAML frontmatter: `---` blocks

## Usage

### Command Line

```bash
# Basic translation
python3 -m tools.cli input.md

# Specify output file
python3 -m tools.cli input.md output.md

# Validate file structure
python3 -m tools.cli --validate input.md

# Show statistics
python3 -m tools.cli --stats input.md

# Run tests
python3 -m tools.cli --test
```

### Python API

```python
from tools.translate_linewise import LinewiseTranslator

translator = LinewiseTranslator()

# Translate lines
input_lines = ["# Header", "Some text with `code`"]
output_lines = translator.translate_file_with_microbatch(input_lines)

# Or translate file directly
from tools.translate_linewise import translate_markdown_file
translate_markdown_file("input.md", "output.md")
```

### Placeholder Protection Only

```python
from tools.placeholder import protect_line, restore_line

text = "Use `console.log()` and visit {{ site.url }}"
protected, manager = protect_line(text)
# protected: "Use __PLACEHOLDER_0001__ and visit __PLACEHOLDER_0002__"

# After translation...
restored = restore_line(translated_text, manager)
# restored: "Use `console.log()` and visit {{ site.url }}"
```

## Testing

Run the test suite:

```bash
python3 tools/test_translation.py
```

Test categories:
- Placeholder protection/restoration
- Line count preservation
- State machine behavior (code fences, tables, YAML)
- Real markdown file handling
- Integration tests

## Implementation Details

### State Machine

The translator uses a state machine to track content context:

- `NORMAL`: Regular translatable content
- `CODE_FENCE`: Inside code blocks (skip translation)
- `TABLE`: Inside markdown tables (skip translation)
- `YAML_FRONTMATTER`: Inside YAML blocks (skip translation)

### Placeholder System

Protected content is replaced with unique tokens during translation:

1. **Protection**: Special content → `__PLACEHOLDER_0001__`
2. **Translation**: Placeholders preserved in translated text
3. **Restoration**: Placeholders → original special content

### Micro-batch Format

For better translation context, content can be batched:

```
L0001=# Header text
L0002=Paragraph content
L0003=Another paragraph
```

This format provides context to translation services while maintaining line-by-line processing.

## Examples

### Input Markdown
```markdown
---
title: Example
---

# Sample Document

Visit [JHipster]({{ site.url }}) for documentation.

```bash
npm install
```

| Feature | Status |
|---------|--------|
| Translation | ✅ |
```

### Output (Mock Translation)
```markdown
---
title: Example
---

[TRANSLATED] # Sample Document

[TRANSLATED] Visit [JHipster]({{ site.url }}) for documentation.

```bash
npm install
```

| Feature | Status |
|---------|--------|
| Translation | ✅ |
```

Note how:
- YAML frontmatter is preserved
- Jekyll variables in links are protected
- Code blocks are not translated
- Tables are preserved
- Line count remains identical

## Integration

This tool is designed to be integrated into translation workflows:

1. **Pre-processing**: Protect special content
2. **Translation**: Send to translation service
3. **Post-processing**: Restore protected content
4. **Validation**: Verify line count and content integrity

## Error Handling

- **Translation failures**: Fall back to original content
- **Restoration failures**: Validate and report issues
- **Line count mismatches**: Assert and abort if detected
- **State tracking**: Reset between files to prevent contamination
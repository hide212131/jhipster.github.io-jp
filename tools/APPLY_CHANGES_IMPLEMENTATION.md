# apply_changes.py Implementation Summary

## Issue Requirements Implemented

✅ **既訳温存/新規挿入/削除/再翻訳の適用** (Apply existing translation preservation/new insertions/deletions/retranslations)

✅ **軽微変更（SequenceMatcher.ratio ≥ 0.98）は既訳温存** (Minor changes with similarity ≥ 0.98 preserve existing translations)  

✅ **意味変化疑い時はLLMでYES/NO判定** (LLM YES/NO determination when semantic change is suspected)

✅ **受入基準: 4種の変更を正しく処理（フィクスチャによるテスト）** (Acceptance criteria: correctly process 4 types of changes with fixture tests)

## 4 Change Types Implementation

### 1. EQUAL Operations (既訳温存)
- **Strategy**: `keep_existing`
- **Action**: Preserve existing Japanese translation
- **Logic**: Content unchanged, no translation needed

### 2. INSERT Operations (新規挿入)  
- **Strategy**: `translate_new`
- **Action**: Translate new content and apply
- **Logic**: New content added, requires translation

### 3. DELETE Operations (削除)
- **Strategy**: `delete_existing`  
- **Action**: Handle deletion in translation
- **Logic**: Content removed, update translation accordingly

### 4. REPLACE Operations (軽微変更/再翻訳)
- **Minor Edit** (similarity ≥ 0.98):
  - **Strategy**: `keep_existing`
  - **Action**: Preserve existing translation
  - **Logic**: Change too small to affect meaning
  
- **Major Change** (similarity < 0.98):
  - **Strategy**: `retranslate`
  - **Action**: Use LLM to determine if semantic change
  - **Logic**: 
    - If LLM says semantic change → retranslate
    - If LLM says no semantic change → preserve existing

## Key Features

### Similarity Threshold Handling
- Uses `SequenceMatcher.ratio ≥ 0.98` threshold
- Minor changes (≥ 0.98) preserve existing translations
- Major changes (< 0.98) trigger semantic analysis

### LLM Semantic Change Detection  
- For borderline cases (0.8 ≤ similarity < 0.98)
- LLM analyzes if changes are semantically significant
- YES → retranslate, NO → preserve existing
- Handles edge cases like negation, numbers, technical terms

### Existing Translation Preservation
- Retrieves current Japanese translation from HEAD
- Preserves when appropriate based on operation strategy
- Writes preserved content back to files

### Mixed Operations Handling
- Files can have multiple operation types
- Smart strategy selection based on operation mix
- Translates entire file if any operations require translation

## Test Coverage

### Comprehensive Test Suite (21 tests total)
- **7 apply_changes tests**: All 4 change types + LLM scenarios + integration
- **14 discover_changes tests**: Existing functionality (no regression)

### Test Cases
1. `test_apply_changes_equal_operation`: EQUAL → keep_existing
2. `test_apply_changes_insert_operation`: INSERT → translate_new  
3. `test_apply_changes_delete_operation`: DELETE → delete_existing
4. `test_apply_changes_replace_minor_edit`: REPLACE minor → keep_existing
5. `test_apply_changes_replace_major_change_with_llm`: REPLACE major + LLM → retranslate
6. `test_apply_changes_replace_llm_no_semantic_change`: LLM says no change → keep_existing
7. `test_mixed_operations_file`: Mixed operations → smart handling

### Demo Script
- `test_apply_changes_demo.py`: Comprehensive demonstration
- Shows all 4 change types in action
- Validates acceptance criteria
- Clear console output showing LLM usage

## Files Modified/Added

### Enhanced Files
- `apply_changes.py`: Complete rewrite of `_apply_file_changes` method
- `llm.py`: Added semantic change detection with heuristics
- `translate_blockwise.py`: Added LLM delegation method

### Test Files Added
- `test_apply_changes.py`: Comprehensive test suite with fixtures
- `test_apply_changes_demo.py`: Interactive demonstration script

## CLI Compatibility

The enhanced `apply_changes.py` maintains full CLI compatibility:

```bash
# Apply all changes
python apply_changes.py -c changes.json

# Apply specific files
python apply_changes.py -c changes.json -f docs/readme.md

# Dry run preview  
python apply_changes.py -c changes.json --dry-run

# Commit changes
python apply_changes.py -c changes.json --commit
```

## Integration with Pipeline

Works seamlessly with existing pipeline:
1. `discover_changes.py` → detects 4 operation types with strategies
2. `apply_changes.py` → applies operations with preservation/translation logic
3. Maintains compatibility with `translate_blockwise.py` and `llm.py`

## Success Metrics

- ✅ All 21 tests pass
- ✅ No regression in existing functionality  
- ✅ Demo validates all acceptance criteria
- ✅ CLI compatibility maintained
- ✅ Proper LLM semantic change detection
- ✅ Similarity threshold handling (≥ 0.98)
- ✅ 4 change types correctly processed
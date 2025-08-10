#!/usr/bin/env python3
"""Demonstration script for enhanced pr_body.py functionality.

This script showcases all the enhanced features implemented to meet the requirements.
"""

import json
import tempfile
import subprocess
import sys
from pathlib import Path

def create_demo_data():
    """Create comprehensive demo data showcasing all features."""
    
    print("🔧 Creating demonstration data...")
    
    # Comprehensive changes data
    changes_data = {
        "upstream_ref": "upstream/main",
        "upstream_sha": "abc123def456789",
        "timestamp": "2025-01-23T10:30:00Z",
        "base_commit": "def456ghi789abc",
        "files": {
            "translate": [
                {
                    "path": "docs/getting-started/installation.md",
                    "status": "modified",
                    "change_type": "replace",
                    "strategy": "retranslate",
                    "upstream_sha": "abc123def456789",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/abc123def456789",
                    "lines_added": 15,
                    "lines_removed": 8,
                    "lines_modified": 25,
                    "total_lines_before": 120,
                    "total_lines_after": 127
                },
                {
                    "path": "docs/creating-an-app/creating-an-entity.md",
                    "status": "added",
                    "change_type": "insert", 
                    "strategy": "translate_new",
                    "upstream_sha": "def456ghi789abc",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/def456ghi789abc",
                    "lines_added": 75,
                    "lines_removed": 0,
                    "lines_modified": 0,
                    "total_lines_before": 0,
                    "total_lines_after": 75
                },
                {
                    "path": "docs/deprecated/old-tutorial.md",
                    "status": "deleted",
                    "change_type": "delete",
                    "strategy": "delete",
                    "upstream_sha": "ghi789abc123def",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/ghi789abc123def",
                    "lines_added": 0,
                    "lines_removed": 45,
                    "lines_modified": 0,
                    "total_lines_before": 45,
                    "total_lines_after": 0
                },
                {
                    "path": "docs/tutorials/microservices.md",
                    "status": "modified",
                    "change_type": "equal",
                    "strategy": "keep_existing",
                    "upstream_sha": "jkl012mno345pqr",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/jkl012mno345pqr",
                    "lines_added": 0,
                    "lines_removed": 0,
                    "lines_modified": 0,
                    "total_lines_before": 85,
                    "total_lines_after": 85
                }
            ],
            "copy_only": [
                {
                    "path": "static/images/jhipster-logo.png",
                    "status": "added",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "pqr678stu901vwx",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/pqr678stu901vwx"
                },
                {
                    "path": "package.json",
                    "status": "modified",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "stu901vwx234yz",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/stu901vwx234yz"
                },
                {
                    "path": "static/css/bootstrap.min.css",
                    "status": "deleted",
                    "change_type": "copy",
                    "strategy": "copy_only",
                    "upstream_sha": "vwx234yz567abc",
                    "upstream_commit_url": "https://github.com/jhipster/jhipster.github.io/commit/vwx234yz567abc"
                }
            ],
            "ignore": [
                {
                    "path": "node_modules/dependencies/",
                    "status": "modified",
                    "reason": "excluded_path"
                }
            ]
        },
        "statistics": {
            "total_files": 8,
            "translate_files": 4,
            "copy_only_files": 3,
            "ignored_files": 1
        }
    }
    
    # Apply results data
    apply_results_data = {
        "timestamp": "2025-01-23T10:35:00Z",
        "processing_time": 245.8,
        "pipeline_version": "1.0.0",
        "upstream_ref": "upstream/main",
        "translation_branch": "translate/sync-20250123-1030",
        "statistics": {
            "files": {
                "total_processed": 7,
                "translated": 2,
                "copied": 3,
                "kept_existing": 1,
                "deleted": 1,
                "errors": 0
            }
        },
        "errors": [],
        "verification": {
            "line_count_matches": True,
            "structure_preserved": True,
            "code_blocks_intact": True,
            "placeholders_restored": True,
            "all_files_valid": True
        }
    }
    
    # Report.json data showcasing aggregation
    report_data = {
        "report_version": "1.0.0",
        "generation_time": "2025-01-23T10:40:00Z",
        "pipeline_run_id": "sync-20250123-1030",
        "summary": {
            "files": {
                "inserted": 1,
                "replaced": 1,
                "kept": 1,
                "deleted": 1,
                "nondoc_copied": 3
            },
            "operations": {
                "llm_calls": 38,
                "retries": 7,
                "cache_hits": 15,
                "total_processing_time": 245.8
            },
            "lines": {
                "total_original": 250,
                "total_final": 287,
                "net_change": 37
            }
        }
    }
    
    return changes_data, apply_results_data, report_data

def demonstrate_enhanced_features():
    """Demonstrate all enhanced features."""
    
    print("🚀 PR Body Generator Enhancement Demonstration")
    print("=" * 60)
    
    # Create demo data
    changes_data, apply_results_data, report_data = create_demo_data()
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(changes_data, f, indent=2)
        changes_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(apply_results_data, f, indent=2)
        apply_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report_data, f, indent=2)
        report_file = f.name
    
    output_file = "/tmp/demo_pr_body.md"
    
    try:
        print("\n📋 Generating enhanced PR body with all features...")
        
        # Run the enhanced pr_body.py
        result = subprocess.run([
            sys.executable, "pr_body.py",
            "-c", changes_file,
            "-r", apply_file,
            "--report-file", report_file,
            "-o", output_file
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"❌ Error running pr_body.py: {result.stderr}")
            return False
        
        print("✅ PR body generated successfully!")
        
        # Read and display the generated PR body
        with open(output_file, 'r', encoding='utf-8') as f:
            pr_body = f.read()
        
        print("\n" + "=" * 60)
        print("📄 GENERATED PR BODY DEMONSTRATION")
        print("=" * 60)
        print(pr_body)
        print("=" * 60)
        
        # Validate key features
        print("\n🔍 FEATURE VALIDATION:")
        
        features = {
            "📈 Report.json aggregation": "Aggregated Statistics (from report.json)" in pr_body,
            "🏷️ File classification": "| File | Status | Strategy |" in pr_body,
            "📊 Line diff display": "+15/-8 (" in pr_body,  # Check line diff format
            "🔗 SHA and commit links": "github.com/jhipster/jhipster.github.io/commit/" in pr_body,
            "📋 Multiple file types": "Translation Files" in pr_body and "Copy-Only Files" in pr_body,
            "♻️ Strategy display": "retranslate" in pr_body and "translate_new" in pr_body,
            "🗑️ Deleted files section": "Deleted Files" in pr_body,
            "⚡ Operations summary": "LLM calls**: 38" in pr_body
        }
        
        all_passed = True
        for feature, passed in features.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {feature}")
            if not passed:
                all_passed = False
        
        print(f"\n🎯 Overall Feature Validation: {'✅ ALL FEATURES WORKING' if all_passed else '❌ SOME FEATURES MISSING'}")
        
        # Count table rows to verify multi-file handling
        lines = pr_body.split('\n')
        translation_rows = len([line for line in lines if line.startswith("| `docs/") and "|" in line])
        copy_rows = len([line for line in lines if line.startswith("| `static/") or line.startswith("| `package.")])
        
        print(f"\n📊 Table Statistics:")
        print(f"  • Translation file rows: {translation_rows}")
        print(f"  • Copy-only file rows: {copy_rows}")
        print(f"  • Total commit links: {pr_body.count('github.com/jhipster/jhipster.github.io/commit/')}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        return False
    
    finally:
        # Clean up
        import os
        try:
            os.unlink(changes_file)
            os.unlink(apply_file)
            os.unlink(report_file)
        except:
            pass

if __name__ == '__main__':
    success = demonstrate_enhanced_features()
    
    if success:
        print("\n🎉 DEMONSTRATION COMPLETE - All enhanced features working correctly!")
        print("\n📝 IMPLEMENTATION SUMMARY:")
        print("  ✅ 追加/変更/削除/非対象コピーの分類 (File classification)")
        print("  ✅ 更新ファイルの戦略・行数差・SHA・コミットリンク付与 (Strategy, line diff, SHA, commit links)")
        print("  ✅ report.json集計による合計値要約 (Report.json aggregation)")
        print("  ✅ 受入基準: マルチファイル更新時に表が正しく埋まる (Multi-file table validation)")
    else:
        print("\n❌ DEMONSTRATION FAILED - Some features not working correctly!")
    
    exit(0 if success else 1)
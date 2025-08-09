#!/usr/bin/env python3
"""
テストフィクスチャとテストスイート：全オペコード (equal/insert/delete/replace) のテスト
"""

import os
import tempfile
import json
from pathlib import Path
import sys

# tools ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from discover_changes import DiffDiscoverer
from apply_changes import ChangeApplier


class TestFixtures:
    """テストフィクスチャの生成と管理"""
    
    @staticmethod
    def create_equal_test():
        """equal操作のテストケース"""
        source = [
            "# JHipster Documentation",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        target = [
            "# JHipster Documentation", 
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        return source, target, "equal_test"
    
    @staticmethod
    def create_insert_test():
        """insert操作のテストケース"""
        source = [
            "# JHipster Documentation",
            "",
            "## New Section",
            "This is a new section.",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        target = [
            "# JHipster Documentation",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        return source, target, "insert_test"
    
    @staticmethod
    def create_delete_test():
        """delete操作のテストケース"""
        source = [
            "# JHipster Documentation",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        target = [
            "# JHipster Documentation",
            "",
            "## Old Section",
            "This section will be deleted.",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        return source, target, "delete_test"
    
    @staticmethod
    def create_replace_test():
        """replace操作のテストケース"""
        source = [
            "# JHipster Documentation",
            "",
            "This is the updated documentation.",
            "Version 2.0"
        ]
        target = [
            "# JHipster Documentation",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        return source, target, "replace_test"
    
    @staticmethod
    def create_minor_change_test():
        """軽微変更のテストケース"""
        source = [
            "# JHipster Documentation",
            "",
            "This is the main documentation .",
            "Version 1.0"
        ]
        target = [
            "# JHipster Documentation",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        return source, target, "minor_change_test"
    
    @staticmethod
    def create_mixed_operations_test():
        """複数操作が混在するテストケース"""
        source = [
            "# JHipster Documentation",
            "",
            "## Updated Section",
            "This section has been updated.",
            "",
            "## New Feature",
            "This is a completely new feature.",
            "",
            "This is the main documentation.",
            "Version 2.0"
        ]
        target = [
            "# JHipster Documentation",
            "",
            "## Old Section", 
            "This section is old.",
            "",
            "This is the main documentation.",
            "Version 1.0"
        ]
        return source, target, "mixed_operations_test"


class TestRunner:
    """テスト実行クラス"""
    
    def __init__(self):
        self.temp_dir = None
        self.discoverer = DiffDiscoverer()
        self.applier = ChangeApplier(create_backup=True)
    
    def setup(self):
        """テスト環境のセットアップ"""
        self.temp_dir = tempfile.mkdtemp(prefix="jp_diff_test_")
        print(f"Test directory: {self.temp_dir}")
    
    def cleanup(self):
        """テスト環境のクリーンアップ"""
        if self.temp_dir:
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def write_test_files(self, source_lines, target_lines, test_name):
        """テストファイルを作成"""
        source_file = Path(self.temp_dir) / f"{test_name}_source.txt"
        target_file = Path(self.temp_dir) / f"{test_name}_target.txt"
        operations_file = Path(self.temp_dir) / f"{test_name}_operations.json"
        
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(source_lines) + '\n')
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(target_lines) + '\n')
        
        return str(source_file), str(target_file), str(operations_file)
    
    def run_single_test(self, test_func, expected_opcodes):
        """単一テストを実行"""
        print(f"\n=== Running {test_func.__name__} ===")
        
        source_lines, target_lines, test_name = test_func()
        source_file, target_file, operations_file = self.write_test_files(
            source_lines, target_lines, test_name
        )
        
        # 差分検出
        operations = self.discoverer.discover_changes(source_lines, target_lines)
        
        # 操作をJSONファイルに保存
        from discover_changes import serialize_operations
        operations_json = serialize_operations(operations)
        with open(operations_file, 'w', encoding='utf-8') as f:
            f.write(operations_json)
        
        # 結果の検証
        found_opcodes = [op.opcode for op in operations]
        print(f"Expected opcodes: {expected_opcodes}")
        print(f"Found opcodes: {found_opcodes}")
        
        # オペコードの検証
        success = True
        for expected_op in expected_opcodes:
            if expected_op not in found_opcodes:
                print(f"ERROR: Expected opcode '{expected_op}' not found")
                success = False
        
        # 詳細情報の出力
        for i, op in enumerate(operations):
            print(f"  Operation {i+1}: {op.opcode} "
                  f"source[{op.source_start}:{op.source_end}] -> "
                  f"target[{op.target_start}:{op.target_end}]")
            if op.is_minor_change:
                print(f"    -> Minor change detected")
            if op.has_semantic_change is not None:
                print(f"    -> Semantic change: {op.has_semantic_change}")
        
        # 差分適用テスト (replace以外のテストで実行)
        if test_name != "minor_change_test":
            print(f"\n--- Testing apply_changes for {test_name} ---")
            try:
                # ターゲットファイルのコピーを作成
                apply_target = str(Path(self.temp_dir) / f"{test_name}_apply_target.txt")
                import shutil
                shutil.copy2(target_file, apply_target)
                
                # 変更を適用
                self.applier.apply_from_files(apply_target, operations_file)
                
                # 結果をソースファイルと比較
                with open(apply_target, 'r', encoding='utf-8') as f:
                    result_lines = [line.rstrip('\n\r') for line in f.readlines()]
                
                if result_lines == source_lines:
                    print("  Apply test: PASS - Result matches source")
                else:
                    print("  Apply test: FAIL - Result does not match source")
                    print(f"  Expected: {source_lines}")
                    print(f"  Got: {result_lines}")
                    success = False
                    
            except Exception as e:
                print(f"  Apply test: ERROR - {e}")
                success = False
        
        print(f"Test result: {'PASS' if success else 'FAIL'}")
        return success
    
    def run_all_tests(self):
        """全テストを実行"""
        test_cases = [
            (TestFixtures.create_equal_test, ['equal']),
            (TestFixtures.create_insert_test, ['equal', 'delete']),  # source has more content
            (TestFixtures.create_delete_test, ['equal', 'insert']),  # target has more content
            (TestFixtures.create_replace_test, ['equal', 'replace']),
            (TestFixtures.create_minor_change_test, ['equal', 'replace']),
            (TestFixtures.create_mixed_operations_test, ['equal', 'replace'])  # complex case
        ]
        
        self.setup()
        
        try:
            total_tests = len(test_cases)
            passed_tests = 0
            
            for test_func, expected_opcodes in test_cases:
                if self.run_single_test(test_func, expected_opcodes):
                    passed_tests += 1
            
            print(f"\n=== Test Summary ===")
            print(f"Total tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
            
            return passed_tests == total_tests
            
        finally:
            self.cleanup()


def main():
    """メイン関数"""
    print("JHipster Diff System Test Suite")
    print("=" * 40)
    
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\nAll tests passed! ✅")
        return 0
    else:
        print("\nSome tests failed! ❌")
        return 1


if __name__ == '__main__':
    exit(main())
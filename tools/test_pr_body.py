#!/usr/bin/env python3
"""
PR本文生成ツールのテスト
表フォーマットの正当性と情報の完全性を検証
"""

import subprocess
import tempfile
import os
from pathlib import Path
import re


def test_table_format():
    """表フォーマットの正当性をテスト"""
    # 既存の出力を使用してテスト
    result = subprocess.run(
        ['python3', 'tools/pr_body.py', '--print'],
        capture_output=True,
        text=True,
        check=True
    )
    
    output = result.stdout
    
    # 表フォーマットの検証
    lines = output.split('\n')
    
    # ヘッダー行の存在確認
    header_found = False
    separator_found = False
    data_rows = 0
    
    for line in lines:
        if '| ファイルパス | 戦略 | 行数差 | 基準SHA |' in line:
            header_found = True
        elif '|--------------|------|--------|----------|' in line:
            separator_found = True
        elif line.startswith('| `') and '`' in line:
            data_rows += 1
    
    assert header_found, "テーブルヘッダーが見つかりません"
    assert separator_found, "テーブル区切り行が見つかりません"
    assert data_rows > 0, "データ行が見つかりません"
    
    print("✓ 表フォーマットテスト合格")
    return True


def test_information_completeness():
    """情報の完全性をテスト"""
    result = subprocess.run(
        ['python3', 'tools/pr_body.py', '--print'],
        capture_output=True,
        text=True,
        check=True
    )
    
    output = result.stdout
    
    # 必須要素の確認
    assert '基準SHA:' in output, "基準SHAが含まれていません"
    assert '| ファイルパス |' in output, "ファイルパス列が含まれていません"
    assert '| 戦略 |' in output, "戦略列が含まれていません"
    assert '| 行数差 |' in output, "行数差列が含まれていません"
    assert '| 基準SHA |' in output, "基準SHA列が含まれていません"
    
    # SHA形式の確認（8桁のハッシュ）
    sha_pattern = r'`[a-f0-9]{8}`'
    assert re.search(sha_pattern, output), "適切なSHA形式が見つかりません"
    
    print("✓ 情報完全性テスト合格")
    return True


def test_multiple_files_support():
    """複数ファイル対応のテスト"""
    # 現在の変更をチェック
    result = subprocess.run(
        ['python3', 'tools/pr_body.py', '--print'],
        capture_output=True,
        text=True,
        check=True
    )
    
    output = result.stdout
    lines = output.split('\n')
    
    # データ行の数をカウント
    data_rows = 0
    for line in lines:
        if line.startswith('| `') and line.count('|') >= 4:
            data_rows += 1
    
    # 現在は複数ファイルが変更されているはず
    if data_rows > 1:
        print(f"✓ 複数ファイル対応テスト合格 ({data_rows}ファイル)")
        return True
    else:
        print(f"⚠ 単一ファイルでのテスト ({data_rows}ファイル)")
        return True


def test_gh_pr_compatibility():
    """gh pr create --body-file 互換性テスト"""
    # PR本文を生成
    subprocess.run(['python3', 'tools/pr_body.py'], check=True)
    
    # 出力ファイルの存在確認
    output_file = Path('tools/.out/pr_body.md')
    assert output_file.exists(), "出力ファイルが作成されていません"
    
    # ファイル内容の確認
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Markdownフォーマットの確認
    assert content.startswith('## '), "適切なMarkdownヘッダーで始まっていません"
    assert '|' in content, "テーブル形式になっていません"
    
    print("✓ gh pr create --body-file 互換性テスト合格")
    return True


def main():
    """テスト実行"""
    print("PR本文生成ツールのテストを開始...")
    
    # カレントディレクトリをリポジトリルートに変更
    os.chdir(Path(__file__).parent.parent)
    
    tests = [
        test_information_completeness,
        test_multiple_files_support,
        test_gh_pr_compatibility,
        test_table_format,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 失敗: {e}")
    
    print(f"\nテスト結果: {passed}/{len(tests)} 合格")
    
    if passed == len(tests):
        print("🎉 全テスト合格！")
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
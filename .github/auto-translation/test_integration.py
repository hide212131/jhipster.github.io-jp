#!/usr/bin/env python3
"""
統合テストスクリプト：差分検出・適用器の動作確認
"""

import sys
import tempfile
from pathlib import Path

# プロジェクトルートにモジュールを追加
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from line_diff import analyze_file_diff, OperationType
from apply_changes import ChangeApplicator, SemanticChangeDetector


def test_comprehensive_diff_application():
    """包括的な差分適用テスト"""
    print("🧪 差分検出・適用器の統合テスト開始")
    
    # テストデータ準備
    old_content = """# JHipster Installation Guide

This guide will help you install JHipster.

## Prerequisites

You need Java 17 or later.
You need Node.js 18 or later.

## Installation Steps

1. Install JHipster CLI
2. Create a new project
3. Run the application

## Troubleshooting

If you encounter issues, check the logs.
"""

    new_content = """# JHipster Installation Guide

This comprehensive guide will help you install JHipster quickly.

## Prerequisites

You need Java 21 or later.
You need Node.js 20 or later.
You need Git installed.

## Installation Steps

1. Install JHipster CLI globally
2. Create a new project directory
3. Generate application
4. Run the application

## Configuration

Configure your database settings.

## Troubleshooting

If you encounter issues, check the application logs.
"""

    existing_translation = """# JHipster インストールガイド

このガイドでは JHipster のインストール方法を説明します。

## 前提条件

Java 17 以降が必要です。
Node.js 18 以降が必要です。

## インストール手順

1. JHipster CLI をインストール
2. 新しいプロジェクトを作成
3. アプリケーションを実行

## トラブルシューティング

問題が発生した場合は、ログを確認してください。
"""

    print("📊 行レベル差分分析...")
    
    # 1. 行レベル差分分析
    analyzer = analyze_file_diff(old_content, new_content)
    summary = analyzer.get_change_summary()
    
    print(f"   操作総数: {summary['total_operations']}")
    print(f"   equal: {summary['equal_count']}")
    print(f"   insert: {summary['insert_count']}")
    print(f"   delete: {summary['delete_count']}")
    print(f"   replace: {summary['replace_count']}")
    print(f"   軽微変更: {summary['minor_changes']}")
    print(f"   重要変更: {summary['major_changes']}")
    
    # 2. 操作詳細の確認
    print("\n🔍 検出された操作:")
    for i, op in enumerate(analyzer.operations):
        if op.operation != OperationType.EQUAL:
            print(f"   操作 {i+1}: {op.operation.value}")
            print(f"      旧: 行 {op.old_start}-{op.old_end}")
            print(f"      新: 行 {op.new_start}-{op.new_end}")
            if op.operation == OperationType.REPLACE:
                print(f"      類似度: {op.similarity_ratio:.3f}")
                print(f"      軽微変更: {op.is_minor_change()}")
    
    # 3. 変更適用のテスト
    print("\n⚙️ 変更適用テスト...")
    
    applicator = ChangeApplicator()
    
    # 操作データを準備
    operations = [
        {
            "operation": op.operation.value,
            "old_start": op.old_start,
            "old_end": op.old_end,
            "new_start": op.new_start,
            "new_end": op.new_end,
            "old_lines": op.old_lines,
            "new_lines": op.new_lines,
            "similarity_ratio": op.similarity_ratio,
            "is_minor_change": op.is_minor_change()
        }
        for op in analyzer.operations
    ]
    
    # ファイル変更を適用
    result = applicator.apply_file_changes("test.md", operations, existing_translation)
    
    print(f"   適用結果: {'成功' if result.applied else '失敗'}")
    print(f"   ポリシー: {result.policy.value}")
    print(f"   理由: {result.reason}")
    
    if result.error:
        print(f"   エラー: {result.error}")
    
    # 4. 意味変更検出のテスト
    print("\n🤖 意味変更検出テスト...")
    
    detector = SemanticChangeDetector()
    
    test_cases = [
        ("Hello, world.", "Hello, world!", "句読点のみ変更"),
        ("Java 17 or later", "Java 21 or later", "バージョン変更"),
        ("This guide", "This comprehensive guide", "修飾語追加"),
        ("check the logs", "check the application logs", "詳細化")
    ]
    
    for old_text, new_text, description in test_cases:
        has_semantic_change = detector.has_semantic_change(old_text, new_text)
        print(f"   {description}: {'意味変更あり' if has_semantic_change else '軽微変更'}")
    
    print("\n✅ 統合テスト完了")
    
    # 結果確認
    assert result.applied, "変更適用が失敗しました"
    assert summary['total_operations'] > 0, "操作が検出されませんでした"
    assert analyzer.has_significant_changes(), "重要な変更が検出されませんでした"
    
    print("🎉 すべてのテストが成功しました！")


if __name__ == "__main__":
    test_comprehensive_diff_application()
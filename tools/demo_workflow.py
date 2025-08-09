#!/usr/bin/env python3
"""
差分検出・適用システムのデモンストレーション
完全なワークフローの例
"""

import tempfile
import os
from pathlib import Path
import sys

# tools ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from discover_changes import DiffDiscoverer, serialize_operations
from apply_changes import ChangeApplier


def create_demo_files():
    """デモ用のファイルを作成"""
    # 英語原文 (upstream)
    english_content = """# JHipster Getting Started Guide

## Introduction
Welcome to JHipster! This guide will help you get started.

## Prerequisites
Before you begin, make sure you have:
- Java 11 or higher
- Node.js 14 or higher
- Git

## Installation Steps
1. Install JHipster CLI
2. Create a new application
3. Configure your database
4. Run the application

## Next Steps
Explore the generated code and customize your application.
"""

    # 日本語訳 (既存)
    japanese_content = """# JHipster スタートガイド

## はじめに
JHipsterへようこそ！このガイドでは開始方法を説明します。

## 前提条件
始める前に、以下を確認してください：
- Java 8以上
- Node.js 12以上
- Git

## インストール手順
1. JHipster CLIをインストール
2. 新しいアプリケーションを作成
3. データベースを設定
4. アプリケーションを実行

## 次のステップ
生成されたコードを探索し、アプリケーションをカスタマイズしてください。
"""

    return english_content.strip().split('\n'), japanese_content.strip().split('\n')


def demo_workflow():
    """完全なワークフローのデモ"""
    print("=" * 60)
    print("JHipster差分検出・適用システム デモンストレーション")
    print("=" * 60)
    
    # テンポラリディレクトリを作成
    with tempfile.TemporaryDirectory(prefix="jhipster_diff_demo_") as temp_dir:
        temp_path = Path(temp_dir)
        
        # デモファイルを作成
        english_lines, japanese_lines = create_demo_files()
        
        english_file = temp_path / "english.md"
        japanese_file = temp_path / "japanese.md"
        diff_file = temp_path / "diff.json"
        
        # ファイルに書き込み
        with open(english_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(english_lines) + '\n')
        
        with open(japanese_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(japanese_lines) + '\n')
        
        print(f"\n📁 作業ディレクトリ: {temp_dir}")
        print(f"   英語原文: {english_file.name}")
        print(f"   日本語訳: {japanese_file.name}")
        
        # Step 1: 差分検出
        print("\n🔍 Step 1: 差分検出")
        discoverer = DiffDiscoverer()
        operations = discoverer.discover_from_files(str(english_file), str(japanese_file))
        
        # 結果をJSONファイルに保存
        operations_json = serialize_operations(operations)
        with open(diff_file, 'w', encoding='utf-8') as f:
            f.write(operations_json)
        
        # 統計を表示
        total_ops = len(operations)
        by_opcode = {}
        minor_count = 0
        semantic_count = 0
        
        for op in operations:
            by_opcode[op.opcode] = by_opcode.get(op.opcode, 0) + 1
            if op.is_minor_change:
                minor_count += 1
            if op.has_semantic_change:
                semantic_count += 1
        
        print(f"   検出された操作数: {total_ops}")
        print(f"   操作別内訳: {by_opcode}")
        print(f"   軽微変更: {minor_count}")
        print(f"   意味変化: {semantic_count}")
        
        # 主要な差分を表示
        print("\n📋 主要な差分:")
        for i, op in enumerate(operations[:5]):  # 最初の5つを表示
            if op.opcode != 'equal':
                print(f"   {i+1}. {op.opcode}: '{op.target_text[:30]}...' -> '{op.source_text[:30]}...'")
                if op.is_minor_change:
                    print(f"      (軽微変更)")
                if op.has_semantic_change:
                    print(f"      (意味変化あり)")
        
        # Step 2: 差分適用
        print(f"\n✅ Step 2: 差分適用")
        applier = ChangeApplier(create_backup=True)
        
        # 適用前のファイルサイズ
        original_size = japanese_file.stat().st_size
        
        # 差分を適用
        success = applier.apply_from_files(str(japanese_file), str(diff_file))
        
        if success:
            # 適用後のファイルサイズ
            new_size = japanese_file.stat().st_size
            print(f"   差分適用完了！")
            print(f"   ファイルサイズ: {original_size} → {new_size} bytes")
            
            # バックアップファイルの存在確認
            backup_file = Path(str(japanese_file) + '.backup')
            if backup_file.exists():
                print(f"   バックアップ作成: {backup_file.name}")
        
        # Step 3: 結果検証
        print(f"\n🔎 Step 3: 結果検証")
        
        # 適用後のファイルを読み込み
        with open(japanese_file, 'r', encoding='utf-8') as f:
            result_lines = [line.rstrip('\n\r') for line in f.readlines()]
        
        # 英語原文と比較
        if result_lines == english_lines:
            print("   ✅ 完全一致: 日本語ファイルが英語原文と同じ内容になりました")
        else:
            print("   ⚠️  差分が残っています")
            # 簡単な差分表示
            for i, (eng, jpn) in enumerate(zip(english_lines, result_lines)):
                if eng != jpn:
                    print(f"   行{i+1}: '{jpn}' != '{eng}'")
                    break
        
        print(f"\n📊 処理サマリー:")
        print(f"   - 処理した操作数: {total_ops}")
        print(f"   - 意味変化のある変更: {semantic_count}")
        print(f"   - 軽微変更: {minor_count}")
        print(f"   - 差分ファイル: {diff_file.name}")
        print(f"   - バックアップファイル: {japanese_file.name}.backup")
        
        print(f"\n💡 実際の運用では:")
        print(f"   1. --skip-minor オプションで軽微変更をスキップ")
        print(f"   2. --skip-no-semantic オプションで意味変化のない変更をスキップ")
        print(f"   3. GEMINI_API_KEY 環境変数でAI意味判定を有効化")
        
        # ファイル内容の一部を表示
        print(f"\n📄 適用後のファイル内容 (最初の5行):")
        with open(japanese_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 5:
                    break
                print(f"   {i+1}: {line.rstrip()}")
        
        print("\n" + "=" * 60)
        print("デモンストレーション完了!")
        print("=" * 60)


if __name__ == '__main__':
    demo_workflow()
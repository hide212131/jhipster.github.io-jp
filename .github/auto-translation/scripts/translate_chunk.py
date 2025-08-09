#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
Gemini翻訳スクリプト
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import google.generativeai as genai
import sys
from pathlib import Path

# ツールモジュールのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import create_gemini_client, get_gemini_config, get_translation_config


def find_project_root() -> Path:
    """プロジェクトルートディレクトリを見つける"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'package.json').exists():
            return current
        current = current.parent
    return Path.cwd()


class GeminiTranslator:
    def __init__(self, api_key: str = None, model_name: str = "gemini-1.5-flash", use_new_llm: bool = True):
        # 新しいLLM層を使用するかどうか
        self.use_new_llm = use_new_llm
        
        if self.use_new_llm:
            # 新しいLLM層を使用
            if api_key:
                os.environ.setdefault('GEMINI_API_KEY', api_key)
            try:
                self.gemini_config = get_gemini_config()
                self.translation_config = get_translation_config()
                self.llm_client = create_gemini_client(self.gemini_config)
                self.api_key = self.gemini_config.api_key
                self.model_name = model_name or self.gemini_config.default_model
                self.max_tokens = self.translation_config.max_tokens_per_chunk
                print(f"✅ Using new LLM layer with rate control and model switching")
            except Exception as e:
                print(f"⚠️ Failed to initialize new LLM layer: {e}")
                print("Falling back to legacy implementation")
                self.use_new_llm = False
        
        if not self.use_new_llm:
            # 従来の実装（後方互換性）
            self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is required")
            self.model_name = model_name
            self.max_tokens = 4096
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
            print(f"✅ Using legacy Gemini implementation")
        
        self.style_guide_content = ""
        self.project_root = find_project_root()
        
        # スタイルガイドを読み込み
        self.load_style_guide()
    
    def load_style_guide(self):
        """基本スタイルガイドを読み込み"""
        # プロジェクトルートから相対パスで探索
        style_guide_path = self.project_root / ".github/auto-translation/docs/style-guide.md"
        
        if style_guide_path.exists():
            try:
                with open(style_guide_path, 'r', encoding='utf-8') as f:
                    self.style_guide_content = f.read()
                print(f"✅ Loaded base style guide: {style_guide_path}")
            except Exception as e:
                print(f"⚠️ Error loading base style guide: {e}")
        else:
            print(f"⚠️ Base style guide not found: {style_guide_path}")
    
    def get_custom_style_guide_for_path(self, file_path: str) -> str:
        """ファイルパスに応じたカスタムスタイルガイドを取得"""
        custom_style_guide = ""
        
        # docs/releases フォルダの場合、リリース用スタイルガイドを適用
        if file_path.startswith("docs/releases/"):
            release_style_guide_path = self.project_root / ".github/auto-translation/docs/style-guide-release.md"
            if release_style_guide_path.exists():
                try:
                    with open(release_style_guide_path, 'r', encoding='utf-8') as f:
                        custom_style_guide = f.read()
                    print(f"✅ Applied custom style guide for releases: {file_path}")
                except Exception as e:
                    print(f"⚠️ Error loading release style guide: {e}")
        
        # 他のフォルダ固有のスタイルガイドもここに追加可能
        
        return custom_style_guide
    
    def count_tokens_estimate(self, text: str) -> int:
        """テキストのトークン数を概算"""
        # 簡易的な計算：日本語は1文字=1.5トークン、英語は1単語=1トークン
        japanese_chars = len(re.findall(r'[ひらがなカタカナ漢字]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        other_chars = len(text) - japanese_chars - english_words
        
        return int(japanese_chars * 1.5 + english_words + other_chars * 0.3)
    
    def split_content_by_paragraphs(self, content: str) -> List[str]:
        """内容を段落単位で分割"""
        # 空行で分割
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 現在のチャンクに段落を追加した場合のトークン数を計算
            test_chunk = f"{current_chunk}\n\n{paragraph}".strip()
            if self.count_tokens_estimate(test_chunk) > self.max_tokens and current_chunk:
                # 現在のチャンクを保存し、新しいチャンクを開始
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk = test_chunk
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def create_translation_prompt(self, content: str, file_path: str = "") -> str:
        """翻訳用プロンプトを作成"""
        # カスタムスタイルガイドを取得
        custom_style_guide = self.get_custom_style_guide_for_path(file_path)
        
        # 基本スタイルガイドとカスタムスタイルガイドを統合
        style_guide_section = ""
        if self.style_guide_content or custom_style_guide:
            combined_style_guide = ""
            
            if self.style_guide_content:
                combined_style_guide += f"## 基本スタイルガイド\n\n{self.style_guide_content}\n\n"
            
            if custom_style_guide:
                combined_style_guide += f"## カスタムスタイルガイド（{file_path}）\n\n{custom_style_guide}\n\n"
                combined_style_guide += "**重要**: カスタムスタイルガイドの指示が基本スタイルガイドと異なる場合は、カスタムスタイルガイドを優先してください。\n\n"
            
            style_guide_section = f"""
以下のスタイルガイドに従って翻訳してください：

{combined_style_guide}---

"""
        
        prompt = f"""{style_guide_section}以下の英語のJHipsterドキュメントを日本語に翻訳してください。

重要な注意事項：
1. マークダウン形式を保持してください
2. コードブロック、URL、ファイルパス、コマンドは翻訳しないでください
3. 技術用語は適切な日本語に翻訳するか、必要に応じて英語のまま残してください
4. 文体は常体（である調）を使用してください
5. **CRITICAL**: 元の文書の行数と改行位置を厳密に保持してください（行の追加・削除は禁止）
6. **CRITICAL**: すでにある日本語は変更せずそのまま維持
7. HTMLタグやマークダウン記法は変更しないでください
8. 空行、段落区切りを完全に維持してください

翻訳対象テキスト：

{content}

翻訳結果（日本語のみ）："""
        
        return prompt
    
    def create_conflict_translation_prompt(self, content: str, stage: str, file_path: str = "") -> str:
        """2段階コンフリクト翻訳用プロンプト"""
        # カスタムスタイルガイドを取得
        custom_style_guide = self.get_custom_style_guide_for_path(file_path)
        
        # 基本スタイルガイドとカスタムスタイルガイドを統合
        style_guide_section = ""
        if self.style_guide_content or custom_style_guide:
            combined_style_guide = ""
            
            if self.style_guide_content:
                combined_style_guide += f"## 基本スタイルガイド\n\n{self.style_guide_content}\n\n"
            
            if custom_style_guide:
                combined_style_guide += f"## カスタムスタイルガイド（{file_path}）\n\n{custom_style_guide}\n\n"
                combined_style_guide += "**重要**: カスタムスタイルガイドの指示が基本スタイルガイドと異なる場合は、カスタムスタイルガイドを優先してください。\n\n"
            
            style_guide_section = f"""
以下のスタイルガイドに従って翻訳してください：

{combined_style_guide}---

"""
        
        if stage == "translate":
            # 第1段階：新規英文を既存日本語スタイルで翻訳
            return f"""{style_guide_section}以下のテキストはGitマージコンフリクトを含むJHipsterドキュメントです。第1段階として、新規英語内容を既存日本語のスタイルに合わせて翻訳してください。

重要：コンフリクトマーカー（<<<<<<<、=======、>>>>>>>）は削除せず、そのまま保持してください。

翻訳指示：
1. <<<<<<< HEAD と ======= の間：既存の日本語版 → 参考として利用（翻訳スタイル、用語選択の基準）
2. ======= と >>>>>>> の間：上流の新規英語版 → 既存日本語のスタイルに合わせて翻訳
3. 既存日本語の文体、用語選択、表現方法を参考にして新規英語を翻訳
4. コンフリクトマーカーは削除しない
5. **CRITICAL**: 行数と改行位置を厳密に保持（行の追加・削除は禁止）
6. **CRITICAL**: コンフリクトマーカーで囲まれた箇所のみ翻訳。他は変更せずそのまま維持
7. マークダウン形式、URL、コマンドは翻訳しない
8. 文体は既存部分と同じ常体（である調）を使用

入力テキスト：

{content}

第1段階結果（新規英文を既存スタイルで翻訳済み、マーカー保持）："""
        else:  # stage == "merge"
            # 第2段階：HEAD側を削除し、翻訳された新規内容を採用
            return f"""{style_guide_section}以下のテキストはコンフリクトマーカーを含む文書です。第2段階として、HEAD側を完全に削除し、新規翻訳内容のみを採用してください。

マージ指示：
1. <<<<<<< HEAD と ======= の間：既存バージョン → 完全に削除
2. ======= と >>>>>>> の間：翻訳済み新規バージョン → これを採用
3. HEAD側の内容は削除し、新規翻訳内容で完全に置き換える
4. コンフリクトマーカーを完全に削除
5. 最終的には翻訳済み新規内容のみが残る
6. **CRITICAL**: 翻訳後の行数と改行位置を厳密に保持
7. **CRITICAL**: 新規翻訳内容以外の箇所は変更せずそのまま維持
8. マークダウン構造は保持

入力テキスト：

{content}

第2段階結果（HEAD削除、新規翻訳内容のみ採用）："""

    def translate_chunk_two_stage(self, content: str, file_path: str = "", retry_count: int = 3) -> Optional[str]:
        """2段階でコンフリクト翻訳"""
        print("   Using 2-stage conflict resolution...")
        
        if self.use_new_llm:
            # 新しいLLM層を使用
            try:
                # 第1段階：英文翻訳（マーカー保持）
                stage1_prompt = self.create_conflict_translation_prompt(content, "translate", file_path)
                stage1_result = self.llm_client.generate_content(stage1_prompt, content)
                
                if not stage1_result:
                    print("   Stage 1 failed")
                    return None
                print("   Stage 1 completed")
                
                # 第2段階：マージ（マーカー削除）
                stage2_prompt = self.create_conflict_translation_prompt(stage1_result, "merge", file_path)
                final_result = self.llm_client.generate_content(stage2_prompt, stage1_result)
                
                if final_result:
                    print("   Stage 2 completed")
                    return final_result
                else:
                    print("   Stage 2 failed, returning stage 1 result")
                    return stage1_result
            except Exception as e:
                print(f"❌ Error in two-stage translation with new LLM layer: {e}")
                return None
        else:
            # 従来の実装
            # 第1段階：英文翻訳（マーカー保持）
            stage1_prompt = self.create_conflict_translation_prompt(content, "translate", file_path)
            stage1_result = None
            
            for attempt in range(retry_count):
                try:
                    response = self.model.generate_content(stage1_prompt)
                    if response.text:
                        stage1_result = response.text.strip()
                        print(f"   Stage 1 completed (attempt {attempt + 1})")
                        break
                except Exception as e:
                    print(f"   Stage 1 attempt {attempt + 1} failed: {e}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)
            
            if not stage1_result:
                print("   Stage 1 failed completely")
                return None
            
            # 第2段階：マージ（マーカー削除）
            stage2_prompt = self.create_conflict_translation_prompt(stage1_result, "merge", file_path)
            
            for attempt in range(retry_count):
                try:
                    response = self.model.generate_content(stage2_prompt)
                    if response.text:
                        final_result = response.text.strip()
                        print(f"   Stage 2 completed (attempt {attempt + 1})")
                        return final_result
                except Exception as e:
                    print(f"   Stage 2 attempt {attempt + 1} failed: {e}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)
            
            print("   Stage 2 failed, returning stage 1 result")
            return stage1_result

    def translate_chunk(self, content: str, file_path: str = "", retry_count: int = 3) -> Optional[str]:
        """単一チャンクを翻訳"""
        # コンフリクトマーカーがあるかチェック
        has_conflicts = any(marker in content for marker in ['<<<<<<<', '=======', '>>>>>>>'])
        
        if has_conflicts:
            return self.translate_chunk_two_stage(content, file_path, retry_count)
        
        # 通常翻訳
        prompt = self.create_translation_prompt(content, file_path)
        
        if self.use_new_llm:
            # 新しいLLM層を使用
            try:
                translated = self.llm_client.generate_content(prompt, content)
                if translated:
                    # 行数チェック
                    original_lines = len(content.split('\n'))
                    translated_lines = len(translated.split('\n'))
                    
                    # 行数の差が設定値を超える場合は警告
                    tolerance = getattr(self.translation_config, 'line_count_tolerance', 0.2)
                    if abs(original_lines - translated_lines) / max(original_lines, 1) > tolerance:
                        print(f"⚠️ Line count mismatch: {original_lines} -> {translated_lines}")
                    
                    return translated
                else:
                    print("⚠️ Translation failed with new LLM layer")
                    return None
            except Exception as e:
                print(f"❌ Error with new LLM layer: {e}")
                return None
        else:
            # 従来の実装
            for attempt in range(retry_count):
                try:
                    response = self.model.generate_content(prompt)
                    
                    if response.text:
                        translated = response.text.strip()
                        
                        # 行数チェック
                        original_lines = len(content.split('\n'))
                        translated_lines = len(translated.split('\n'))
                        
                        # 行数の差が20%を超える場合は警告
                        if abs(original_lines - translated_lines) / max(original_lines, 1) > 0.2:
                            print(f"⚠️ Line count mismatch: {original_lines} -> {translated_lines}")
                        
                        return translated
                    else:
                        print(f"⚠️ Empty response from Gemini (attempt {attempt + 1})")
                        
                except Exception as e:
                    print(f"⚠️ Translation error (attempt {attempt + 1}): {e}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)  # 指数バックオフ
            
            return None
    
    def translate_file(self, file_path: str, output_path: Optional[str] = None) -> bool:
        """ファイル全体を翻訳"""
        try:
            # プロジェクトルートからの相対パスでファイルを読み込み
            full_file_path = self.project_root / file_path
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📝 Translating: {file_path}")
            
            # コンテンツを分割
            chunks = self.split_content_by_paragraphs(content)
            print(f"   Split into {len(chunks)} chunks")
            
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                print(f"   Translating chunk {i + 1}/{len(chunks)}...")
                translated_chunk = self.translate_chunk(chunk, file_path)
                
                if translated_chunk is None:
                    print(f"❌ Failed to translate chunk {i + 1}")
                    return False
                
                translated_chunks.append(translated_chunk)
                
                # API制限を避けるための待機
                if i < len(chunks) - 1:
                    time.sleep(1)
            
            # 翻訳結果を結合
            translated_content = '\n\n'.join(translated_chunks)
            
            # 出力ファイルパスを決定
            if output_path is None:
                full_output_path = full_file_path
            else:
                full_output_path = self.project_root / output_path
            
            # 翻訳結果を保存
            full_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            print(f"✅ Translation completed: {full_output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error translating file {file_path}: {e}")
            return False
    
    def translate_files_from_classification(self, classification_file: str, mode: str = "all") -> bool:
        """分類結果から翻訳対象ファイルを翻訳"""
        try:
            # プロジェクトルートからの相対パスで分類ファイルを読み込み
            full_classification_path = self.project_root / classification_file
            with open(full_classification_path, 'r', encoding='utf-8') as f:
                classification = json.load(f)
            
            files_to_translate = []
            
            if mode == "all":
                # a, b-1, b-2のすべてを翻訳
                files_to_translate.extend(classification["summary"]["a"])
                files_to_translate.extend(classification["summary"]["b-1"])
                files_to_translate.extend(classification["summary"]["b-2"])
            elif mode == "selective":
                # aとb-1のみを翻訳（衝突があるファイルは除外）
                files_to_translate.extend(classification["summary"]["a"])
                files_to_translate.extend(classification["summary"]["b-1"])
            elif mode == "new-only":
                # 新規ファイルのみを翻訳
                files_to_translate.extend(classification["summary"]["a"])
            
            if not files_to_translate:
                print("📋 No files to translate")
                return True
            
            print(f"📋 Found {len(files_to_translate)} files to translate")
            
            success_count = 0
            for file_path in files_to_translate:
                if self.translate_file(file_path):
                    success_count += 1
                else:
                    print(f"❌ Failed to translate: {file_path}")
            
            print(f"✅ Translation completed: {success_count}/{len(files_to_translate)} files")
            return success_count == len(files_to_translate)
            
        except Exception as e:
            print(f"❌ Error in batch translation: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Translate files using Gemini API")
    parser.add_argument(
        "--file",
        help="Single file to translate"
    )
    parser.add_argument(
        "--classification",
        help="Classification JSON file for batch translation"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "selective", "new-only"],
        default="selective",
        help="Translation mode for batch processing"
    )
    parser.add_argument(
        "--output",
        help="Output file path (for single file translation)"
    )
    
    args = parser.parse_args()
    
    # API キーをチェック
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "fake_api_key_for_development":
        print("❌ GEMINI_API_KEY environment variable is required")
        sys.exit(1)
    
    translator = GeminiTranslator(api_key)
    
    if args.file:
        # 単一ファイル翻訳
        success = translator.translate_file(args.file, args.output)
        sys.exit(0 if success else 1)
    elif args.classification:
        # バッチ翻訳
        success = translator.translate_files_from_classification(args.classification, args.mode)
        sys.exit(0 if success else 1)
    else:
        print("❌ Either --file or --classification must be specified")
        sys.exit(1)


if __name__ == "__main__":
    main()
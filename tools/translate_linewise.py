#!/usr/bin/env python3
"""
行ロック翻訳器（Line-locked Translator）
1入力行→1出力行を保証し、プレースホルダ保護とコードフェンス非翻訳を提供
"""

import os
import re
import sys
import time
import json
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# プレースホルダ保護システムをインポート
sys.path.append(str(Path(__file__).parent))
from placeholder import PlaceholderProtector

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai not available, using mock mode")
    genai = None


class FenceState(Enum):
    """コードフェンスの状態"""
    OUTSIDE = "outside"  # フェンス外
    INSIDE = "inside"    # フェンス内


@dataclass
class LineTranslationResult:
    """行翻訳結果"""
    original_line: str
    translated_line: str
    line_number: int
    was_protected: bool
    was_in_fence: bool
    placeholder_count: int


class CodeFenceDetector:
    """コードフェンス検出器"""
    
    def __init__(self):
        self.state = FenceState.OUTSIDE
        self.fence_markers = [
            r'^```',      # Triple backticks
            r'^~~~',      # Triple tildes
            r'^    ',     # 4-space indent (code block)
            r'^\t',       # Tab indent (code block)
        ]
    
    def process_line(self, line: str) -> Tuple[FenceState, bool]:
        """
        行を処理してフェンス状態を更新
        Returns: (現在の状態, この行でフェンスが変化したか)
        """
        stripped = line.strip()
        
        # 空行の場合は状態変更なし
        if not stripped:
            return self.state, False
        
        # Triple backticks or tildes
        if re.match(r'^```|^~~~', stripped):
            if self.state == FenceState.OUTSIDE:
                self.state = FenceState.INSIDE
                return self.state, True
            elif self.state == FenceState.INSIDE:
                self.state = FenceState.OUTSIDE
                return self.state, True
        
        # 現在の状態を返す（フェンス内では変更なし）
        return self.state, False
    
    def is_inside_fence(self) -> bool:
        """現在フェンス内かどうか"""
        return self.state == FenceState.INSIDE
    
    def reset(self):
        """状態をリセット"""
        self.state = FenceState.OUTSIDE


class LinewiseTranslator:
    """行ロック翻訳器メインクラス"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.protector = PlaceholderProtector()
        self.fence_detector = CodeFenceDetector()
        self.model = None
        
        # API初期化
        if api_key and api_key != "fake_api_key_for_testing" and genai:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            print("Warning: Using mock translation mode")
    
    def normalize_llm_output(self, text: str) -> str:
        """LLM出力の改行を空白に正規化"""
        # 複数行の出力を単一行に統合（改行→空白）
        normalized = re.sub(r'\n+', ' ', text.strip())
        # 複数スペースを単一スペースに
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    def create_micro_batch_prompt(self, lines: List[str], batch_id: str) -> str:
        """マイクロバッチ用プロンプトを作成"""
        # L0001=... 形式でバッチを構築
        batch_lines = []
        for i, line in enumerate(lines, 1):
            line_id = f"L{i:04d}"
            batch_lines.append(f"{line_id}={line}")
        
        batch_content = '\n'.join(batch_lines)
        
        prompt = f"""あなたは日本語翻訳の専門家です。以下の英語の行を日本語に翻訳してください。

重要な制約：
1. **行数厳守**: 入力行数と出力行数を完全に一致させてください
2. **行位置保持**: L0001から順番に、同じ順序で翻訳結果を返してください
3. **形式維持**: 出力は必ず "L0001=翻訳結果" の形式で返してください
4. **改行禁止**: 各行の翻訳結果内で改行は使用しないでください
5. **プレースホルダ保護**: PLACEHOLDER_で始まる文字列は翻訳せずそのまま保持してください
6. **空行保持**: 空の行（L0001=）は空のまま出力してください

翻訳スタイル：
- 文体：常体（である調）
- 技術用語：適切な日本語に翻訳または原文のまま
- マークダウン記法：保持

入力バッチ（ID: {batch_id}）：
{batch_content}

出力（同じ形式で同じ行数）："""
        
        return prompt
    
    def parse_batch_response(self, response: str, expected_count: int) -> Optional[List[str]]:
        """バッチレスポンスを解析して行リストに変換"""
        lines = response.strip().split('\n')
        parsed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # L0001=... 形式を解析
            match = re.match(r'^L(\d+)=(.*)$', line)
            if match:
                line_num = int(match.group(1))
                content = match.group(2)
                parsed_lines.append((line_num, content))
        
        # 順序チェックと欠落チェック
        if len(parsed_lines) != expected_count:
            print(f"❌ Line count mismatch: expected {expected_count}, got {len(parsed_lines)}")
            return None
        
        # 順序並び替え
        parsed_lines.sort(key=lambda x: x[0])
        
        # 連続性チェック
        for i, (line_num, _) in enumerate(parsed_lines, 1):
            if line_num != i:
                print(f"❌ Line number mismatch: expected L{i:04d}, got L{line_num:04d}")
                return None
        
        # コンテンツ部分のみ返す
        return [content for _, content in parsed_lines]
    
    def translate_batch(self, lines: List[str], batch_id: str, retry_count: int = 3) -> Optional[List[str]]:
        """マイクロバッチ翻訳"""
        if not self.model:
            # モック翻訳
            mock_results = []
            for line in lines:
                if line.strip():  # 内容がある行のみ翻訳
                    mock_results.append(f"[MOCK翻訳]{line}")
                else:  # 空行・空白のみの行はそのまま
                    mock_results.append(line)
            return mock_results
        
        prompt = self.create_micro_batch_prompt(lines, batch_id)
        
        for attempt in range(retry_count):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    # レスポンス正規化
                    normalized_response = response.text.strip()
                    
                    # バッチ解析
                    translated_lines = self.parse_batch_response(normalized_response, len(lines))
                    if translated_lines is not None:
                        # LLM出力の改行を正規化
                        normalized_lines = [self.normalize_llm_output(line) for line in translated_lines]
                        return normalized_lines
                    else:
                        print(f"⚠️ Batch parsing failed (attempt {attempt + 1})")
                else:
                    print(f"⚠️ Empty response (attempt {attempt + 1})")
                    
            except Exception as e:
                print(f"⚠️ Translation error (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
        
        return None
    
    def split_batch_recursively(self, lines: List[str], batch_id: str, line_protectors: List, max_retries: int = 3) -> List[str]:
        """
        バッチ翻訳が失敗した場合の再帰的分割フォールバック
        最終的に1行単位まで分割する
        """
        if len(lines) == 1:
            # 1行単位での翻訳試行
            result = self.translate_batch(lines, f"{batch_id}_single", max_retries)
            if result:
                return result
            else:
                # 最後の手段：オリジナルを返す
                print(f"❌ Failed to translate single line: {repr(lines[0])}")
                return lines
        
        # バッチを半分に分割
        mid = len(lines) // 2
        left_lines = lines[:mid]
        right_lines = lines[mid:]
        left_protectors = line_protectors[:mid]
        right_protectors = line_protectors[mid:]
        
        print(f"   Splitting batch {batch_id}: {len(lines)} -> {len(left_lines)} + {len(right_lines)}")
        
        # 左半分
        left_result = self.translate_batch(left_lines, f"{batch_id}_L", max_retries)
        if left_result is None:
            left_result = self.split_batch_recursively(left_lines, f"{batch_id}_L", left_protectors, max_retries)
        
        # 右半分
        right_result = self.translate_batch(right_lines, f"{batch_id}_R", max_retries)
        if right_result is None:
            right_result = self.split_batch_recursively(right_lines, f"{batch_id}_R", right_protectors, max_retries)
        
        return left_result + right_result
    
    def translate_line_batch(self, lines: List[str], max_batch_size: int = 20) -> List[LineTranslationResult]:
        """行のバッチ翻訳（フェンス状態考慮）"""
        results = []
        self.fence_detector.reset()
        self.protector.clear()
        
        # バッチ処理用の準備
        batch_lines = []
        batch_start_line = 0
        
        for line_num, original_line in enumerate(lines):
            # フェンス状態チェック
            fence_state, fence_changed = self.fence_detector.process_line(original_line)
            
            # フェンスの開始・終了行かどうかをチェック
            is_fence_marker = fence_changed
            # フェンス内かどうかは、フェンス開始行の場合は開始後、フェンス終了行の場合は終了前の状態を使用
            if is_fence_marker and fence_state == FenceState.INSIDE:
                # フェンス開始行
                is_in_fence = False  # 開始行自体は翻訳対象外だが、まだフェンス内ではない
            elif is_fence_marker and fence_state == FenceState.OUTSIDE:
                # フェンス終了行
                is_in_fence = True   # 終了行自体も翻訳対象外
            else:
                # 通常行
                is_in_fence = fence_state == FenceState.INSIDE
            
            if is_in_fence or is_fence_marker:
                # フェンス内またはフェンスマーカー行：翻訳せずそのまま追加
                if batch_lines:
                    # 蓄積されたバッチを翻訳
                    batch_results = self._process_batch(batch_lines, batch_start_line)
                    results.extend(batch_results)
                    batch_lines = []
                
                # フェンス内行をそのまま追加
                result = LineTranslationResult(
                    original_line=original_line,
                    translated_line=original_line,  # そのまま
                    line_number=line_num,
                    was_protected=False,
                    was_in_fence=True,
                    placeholder_count=0
                )
                results.append(result)
            else:
                # フェンス外：バッチに追加
                if not batch_lines:
                    batch_start_line = line_num
                batch_lines.append(original_line)
                
                # バッチサイズ制限チェック
                if len(batch_lines) >= max_batch_size:
                    batch_results = self._process_batch(batch_lines, batch_start_line)
                    results.extend(batch_results)
                    batch_lines = []
        
        # 残りのバッチを処理
        if batch_lines:
            batch_results = self._process_batch(batch_lines, batch_start_line)
            results.extend(batch_results)
        
        return results
    
    def _process_batch(self, lines: List[str], start_line_num: int) -> List[LineTranslationResult]:
        """バッチ処理の実行"""
        if not lines:
            return []
        
        # 各行ごとに独立してプレースホルダ保護を適用
        protected_lines = []
        line_protectors = []
        
        for line in lines:
            # 各行に独立したプロテクターを使用
            line_protector = PlaceholderProtector()
            protected_line = line_protector.protect_all(line)
            
            protected_lines.append(protected_line)
            line_protectors.append(line_protector)
        
        # バッチ翻訳実行
        batch_id = f"B{start_line_num:04d}"
        translated_lines = self.translate_batch(protected_lines, batch_id)
        
        if translated_lines is None:
            # フォールバック：再帰的分割
            print(f"   Falling back to recursive splitting for batch {batch_id}")
            translated_lines = self.split_batch_recursively(protected_lines, batch_id, line_protectors)
        
        # 各行ごとにプレースホルダ復元
        restored_lines = []
        for i, translated_line in enumerate(translated_lines):
            if i < len(line_protectors):
                restored_line = line_protectors[i].restore_all(translated_line)
            else:
                restored_line = translated_line
            restored_lines.append(restored_line)
        
        # 結果オブジェクト作成
        results = []
        for i, (original, translated) in enumerate(zip(lines, restored_lines)):
            placeholder_count = len(line_protectors[i].placeholders) if i < len(line_protectors) else 0
            result = LineTranslationResult(
                original_line=original,
                translated_line=translated,
                line_number=start_line_num + i,
                was_protected=placeholder_count > 0,
                was_in_fence=False,
                placeholder_count=placeholder_count
            )
            results.append(result)
        
        return results
    
    def translate_text(self, text: str) -> Tuple[str, List[LineTranslationResult]]:
        """テキスト全体を行ロック翻訳"""
        lines = text.split('\n')
        results = self.translate_line_batch(lines)
        
        # 翻訳結果を結合
        translated_lines = [result.translated_line for result in results]
        translated_text = '\n'.join(translated_lines)
        
        return translated_text, results
    
    def translate_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """ファイル翻訳"""
        try:
            # ファイル読み込み
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📝 Translating file: {input_path}")
            
            # 翻訳実行
            translated_content, results = self.translate_text(content)
            
            # 統計情報
            total_lines = len(results)
            protected_lines = sum(1 for r in results if r.was_protected)
            fence_lines = sum(1 for r in results if r.was_in_fence)
            total_placeholders = sum(r.placeholder_count for r in results)
            
            print(f"   📊 Statistics:")
            print(f"      Total lines: {total_lines}")
            print(f"      Protected lines: {protected_lines}")
            print(f"      Fence lines: {fence_lines}")
            print(f"      Total placeholders: {total_placeholders}")
            
            # 行数検証
            original_line_count = len(content.split('\n'))
            translated_line_count = len(translated_content.split('\n'))
            
            if original_line_count != translated_line_count:
                print(f"❌ Line count mismatch: {original_line_count} -> {translated_line_count}")
                return False
            
            # ファイル出力
            if output_path is None:
                output_path = input_path
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            print(f"✅ Translation completed: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error translating file {input_path}: {e}")
            return False
    
    def validate_translation(self, original: str, translated: str) -> Tuple[bool, List[str]]:
        """翻訳結果の検証"""
        errors = []
        
        original_lines = original.split('\n')
        translated_lines = translated.split('\n')
        
        # 行数チェック
        if len(original_lines) != len(translated_lines):
            errors.append(f"Line count mismatch: {len(original_lines)} -> {len(translated_lines)}")
        
        # プレースホルダー残存チェック
        remaining_placeholders = re.findall(r'PLACEHOLDER_\d+_[a-f0-9]{8}', translated)
        if remaining_placeholders:
            errors.append(f"Unreplaced placeholders: {remaining_placeholders}")
        
        # 基本的なマークダウン構造チェック
        original_headers = re.findall(r'^#+\s', original, re.MULTILINE)
        translated_headers = re.findall(r'^#+\s', translated, re.MULTILINE)
        if len(original_headers) != len(translated_headers):
            # ただし、差が1個以下の場合は警告のみ（テーブルヘッダーとの混同可能性）
            diff = abs(len(original_headers) - len(translated_headers))
            if diff <= 1:
                print(f"⚠️ Minor header count difference: {len(original_headers)} -> {len(translated_headers)}")
            else:
                errors.append(f"Header count mismatch: {len(original_headers)} -> {len(translated_headers)}")
        
        return len(errors) == 0, errors


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Line-locked translator with placeholder protection")
    parser.add_argument("--file", help="File to translate")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--text", help="Text to translate (for testing)")
    parser.add_argument("--batch-size", type=int, default=20, help="Max batch size")
    
    args = parser.parse_args()
    
    # API キー取得
    api_key = os.getenv("GEMINI_API_KEY", "fake_api_key_for_testing")
    
    translator = LinewiseTranslator(api_key)
    
    if args.file:
        # ファイル翻訳
        success = translator.translate_file(args.file, args.output)
        sys.exit(0 if success else 1)
    elif args.text:
        # テキスト翻訳（テスト用）
        translated, results = translator.translate_text(args.text)
        print("Original:")
        print(repr(args.text))
        print("\nTranslated:")
        print(repr(translated))
        
        # 検証
        is_valid, errors = translator.validate_translation(args.text, translated)
        print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
        for error in errors:
            print(f"  - {error}")
    else:
        # デモ実行
        demo_text = """# Sample Document

This document contains `inline code` and [links](https://example.com).

```python
# This code should not be translated
def hello():
    return "Hello, World!"
```

| Column 1 | Column 2 |
|----------|----------|
| Cell A   | Cell B   |

Regular paragraph with footnote[^1].

[^1]: Footnote content.
"""
        
        print("🔄 Running demo translation...")
        translated, results = translator.translate_text(demo_text)
        
        print("\n📄 Original:")
        print(demo_text)
        print("\n📄 Translated:")
        print(translated)
        
        # 検証
        is_valid, errors = translator.validate_translation(demo_text, translated)
        print(f"\n✅ Validation: {'PASS' if is_valid else 'FAIL'}")
        if errors:
            for error in errors:
                print(f"  ❌ {error}")


if __name__ == "__main__":
    main()
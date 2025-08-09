# 行ロック翻訳器 (Line-locked Translator)

JHipsterドキュメント翻訳のための高精度翻訳システム

## 概要

行ロック翻訳器は、Markdownドキュメントの翻訳において**1入力行→1出力行**を厳密に保証する翻訳システムです。JHipsterドキュメントの自動翻訳において、文書構造の完全性を保ちながら高品質な翻訳を提供します。

## 主要機能

### 1. 行数完全保証 (Line-locked Translation)
- 入力文書と出力文書の行数が常に一致
- 行の位置関係を完全保持
- 段落構造、空行位置の保持

### 2. プレースホルダ保護システム
以下の要素を翻訳から保護し、翻訳後に完全復元：

- **インラインコード**: `code`
- **URL**: `https://example.com`
- **Markdownリンク**: `[text](url)`
- **HTML属性値**: `class="example"`
- **脚注ID**: `[^1]`, `[^1]:`
- **表の区切り文字**: `|`, `|:---|`, `|:---:|`, `|---:|`
- **行末2スペース**: 改行マーカー `  `

### 3. コードフェンス非翻訳
状態機械による正確なコードブロック検出：
```python
# このコードは翻訳されません
def hello():
    return "Hello, World!"
```

### 4. マイクロバッチI/O
- `L0001=内容` 形式での構造化翻訳
- バッチサイズの動的調整
- 検証失敗時の再帰的分割フォールバック（最終的に1行単位）

## ファイル構成

```
tools/
├── placeholder.py          # プレースホルダ保護システム
├── translate_linewise.py   # 行ロック翻訳器本体
├── integration.py          # 既存システム統合
├── tests/
│   ├── test_placeholder.py
│   └── test_translate_linewise.py
└── README.md              # このファイル
```

## 使用方法

### 基本的な使用

```python
from translate_linewise import LinewiseTranslator

# 翻訳器を初期化
translator = LinewiseTranslator(api_key="your_gemini_api_key")

# テキスト翻訳
translated_text, results = translator.translate_text(content)

# ファイル翻訳
success = translator.translate_file("input.md", "output.md")
```

### コマンドライン使用

```bash
# ファイル翻訳
python translate_linewise.py --file input.md --output output.md

# テキスト翻訳（テスト用）
python translate_linewise.py --text "# Sample text"

# デモ実行
python translate_linewise.py
```

### 既存システムとの統合

```python
from integration import translate_file_with_line_lock

# 行ロック翻訳でファイルを処理
success = translate_file_with_line_lock("docs/example.md")
```

## API リファレンス

### LinewiseTranslator

#### コンストラクタ
```python
LinewiseTranslator(api_key=None, model_name="gemini-1.5-flash")
```

#### 主要メソッド

- `translate_text(text: str) -> Tuple[str, List[LineTranslationResult]]`
  - テキスト全体を行ロック翻訳
  - 戻り値: (翻訳済みテキスト, 行別結果リスト)

- `translate_file(input_path: str, output_path: str = None) -> bool`
  - ファイルを行ロック翻訳
  - 戻り値: 翻訳成功フラグ

- `validate_translation(original: str, translated: str) -> Tuple[bool, List[str]]`
  - 翻訳結果の検証
  - 戻り値: (検証合格フラグ, エラーリスト)

### PlaceholderProtector

#### 主要メソッド

- `protect_all(content: str) -> str`: 全保護要素を適用
- `restore_all(content: str) -> str`: 全プレースホルダーを復元
- `validate_restoration(original, protected, restored) -> Tuple[bool, List[str]]`: 復元検証

## テスト

```bash
# 全テスト実行
python -m pytest tests/ -v

# 特定のテスト実行
python -m pytest tests/test_placeholder.py -v
python -m pytest tests/test_translate_linewise.py -v

# 統合テスト
python integration.py
```

## 受入基準 (Definition of Done)

✅ **任意の .md 入力に対し、出力行数が常に一致する**
- 全テストで行数一致を検証
- 空行、空白行の位置保持
- 段落構造の完全保持

✅ **保護トークンが破損しない（復元完全）**
- プレースホルダーの一意性保証
- 復元機能の完全性検証
- ネストした保護要素の対応

✅ **コードフェンス内スキップの確認**
- 三重バッククォート、チルダ対応
- フェンス状態の正確な追跡
- フェンス内容の完全保持

✅ **表行でパイプ個数/アライメント維持**
- 表区切り文字の保護
- アライメント指定の保持
- 表構造の完全性維持

✅ **脚注やリンクの URL/ID 保持**
- Markdownリンク形式の保護
- 脚注参照・定義の保持
- URL形式の完全復元

✅ **LLM 出力の改行混入時の正規化（改行→空白）**
- 改行の自動正規化
- 行内スペースの適正化
- 出力形式の統一

## 設定

### 環境変数

- `GEMINI_API_KEY`: Gemini API キー（必須、テスト時は `fake_api_key_for_testing`）

### パラメータ調整

- バッチサイズ: デフォルト20行（`max_batch_size`で調整可能）
- リトライ回数: デフォルト3回（API呼び出し失敗時）
- モデル名: デフォルト `gemini-1.5-flash`

## 既存システムとの関係

- **独立性**: 既存の自動翻訳システムに依存せず動作
- **互換性**: `.github/auto-translation` との統合可能
- **拡張性**: 既存のワークフローに組み込み可能

## パフォーマンス

- **精度**: プレースホルダ保護により構造破損ゼロ
- **効率**: マイクロバッチ処理による高速化
- **信頼性**: 検証失敗時の自動フォールバック

## ライセンス

MIT License - JHipster プロジェクトに準拠

## 変更履歴

### v1.0.0 (2024-08-09)
- 初回リリース
- 行ロック翻訳機能の実装
- プレースホルダ保護システムの実装
- コードフェンス検出機能の実装
- マイクロバッチI/O対応
- 包括的テストスイートの作成
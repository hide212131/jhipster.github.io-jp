# LLM呼び出し層（Gemini / レート制御 / リトライ / モデル切替）

Gemini API を利用した翻訳実行層の実装。レート制御や失敗時再試行、モデル切替に対応。

## 機能

- **Gemini API統合**: `google-generativeai`ライブラリを使用
- **セマフォによる並列化制御**: 同時実行数を制限して安定性を確保
- **指数バックオフ/リトライ**: 失敗時の自動再試行機能
- **モデル自動切替**: `gemini-1.5-flash` → `gemini-1.5-pro` の自動フォールバック
- **ドライランモード**: APIキーなしでの動作確認が可能

## インストール

```bash
pip install -r requirements.txt
```

## 環境設定

Gemini APIを使用する場合は、環境変数を設定してください：

```bash
export GEMINI_API_KEY="your_api_key_here"
```

## 基本的な使用方法

### Pythonコードでの使用

```python
import asyncio
from tools.llm import translate_text, generate_text, LLMConfig, GeminiModel

async def main():
    # 基本的な翻訳
    result = await translate_text("Hello, world!", "ja")
    print(f"翻訳結果: {result.content}")
    
    # カスタム設定での使用
    config = LLMConfig(
        preferred_model=GeminiModel.PRO,
        max_concurrent=3,
        max_retries=5
    )
    
    result = await generate_text("日本の首都は？", config)
    print(f"生成結果: {result.content}")

asyncio.run(main())
```

### コマンドラインでの使用

```bash
# 基本的な翻訳（ドライランモード）
python3 tools/llm.py --text "Hello, world!" --target-lang "ja" --dry-run

# Proモデルを使用
python3 tools/llm.py --text "Test message" --model "pro" --dry-run

# 実際のAPI使用（要: GEMINI_API_KEY）
python3 tools/llm.py --text "Hello, world!" --target-lang "ja"
```

## 設定オプション

### LLMConfig パラメータ

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `api_key` | `None` | Gemini API キー（環境変数 `GEMINI_API_KEY` から自動取得） |
| `max_concurrent` | `5` | 最大同時実行数（セマフォ制御） |
| `max_retries` | `3` | 最大リトライ回数 |
| `base_delay` | `1.0` | リトライ時の基準遅延時間（秒） |
| `max_delay` | `60.0` | 最大遅延時間（秒） |
| `timeout` | `30.0` | API呼び出しタイムアウト（秒） |
| `dry_run` | `False` | ドライランモード |
| `preferred_model` | `GeminiModel.FLASH` | 優先使用モデル |
| `fallback_model` | `GeminiModel.PRO` | フォールバックモデル |

### 利用可能なモデル

- `GeminiModel.FLASH`: `gemini-1.5-flash` (高速・コスト効率)
- `GeminiModel.PRO`: `gemini-1.5-pro` (高性能・高精度)

## エラーハンドリング

### エラータイプ

- **RateLimitError**: レート制限エラー（自動リトライ）
- **ModelError**: モデルエラー（自動モデル切替）
- **LLMError**: その他のLLM関連エラー

### リトライロジック

1. **レート制限エラー**: 指数バックオフでリトライ
2. **モデルエラー**: フォールバックモデルに切替
3. **その他エラー**: 指数バックオフでリトライ

## レスポンス形式

```python
@dataclass
class LLMResponse:
    content: str          # 生成されたテキスト
    model_used: str       # 使用されたモデル名
    success: bool         # 成功フラグ
    retry_count: int      # リトライ回数
    execution_time: float # 実行時間（秒）
```

## 使用例

詳細な使用例は `examples.py` を参照してください：

```bash
python3 examples.py
```

## テスト

テストスクリプトで動作確認ができます：

```bash
python3 test_llm.py
```

テスト内容：
- ドライランモード動作確認
- 並列リクエスト処理（セマフォ制御）
- モデル切替機能
- 便利関数の動作
- エラーハンドリング

## 注意事項

1. **APIキー管理**: 本番環境では環境変数でAPIキーを管理してください
2. **レート制限**: Gemini APIのレート制限に注意して `max_concurrent` を調整してください
3. **コスト管理**: 使用モデルによってコストが異なります
4. **ドライランモード**: 開発・テスト時は `dry_run=True` を使用して費用を抑制してください

## 実装詳細

### 並列制御

`asyncio.Semaphore` を使用して同時実行数を制限：

```python
async with self._semaphore:
    # API呼び出し処理
```

### 指数バックオフ

リトライ時の遅延計算：

```python
delay = min(base_delay * (2 ** retry_count), max_delay)
jitter = delay * 0.2 * (random.random() - 0.5)  # ±20%のジッター
```

### モデル切替

優先モデルでエラーが発生した場合、自動的にフォールバックモデルに切替：

```python
if model_to_use == self.config.preferred_model:
    model_to_use = self.config.fallback_model
```
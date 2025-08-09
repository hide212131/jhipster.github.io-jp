# LLM呼び出し層 (tools/llm.py) 使用ガイド

## 概要

このモジュールは、JHipster日本語ドキュメント自動翻訳システム用のGemini API呼び出し共通層です。レート制御、リトライ機構、モデル自動切替機能を提供します。

## 主な機能

### 1. レート制御
- 1分間あたりのリクエスト数制限（デフォルト: 60）
- 制限到達時の自動待機
- 並列リクエスト数制限（デフォルト: 3）

### 2. リトライ機構
- 指数バックオフによる自動リトライ（最大3回）
- ジッター付きで負荷分散
- 設定可能な待機時間

### 3. モデル自動切替
- 短文: `gemini-1.5-flash` (8000文字未満かつ200行未満)
- 長文: `gemini-1.5-pro` (8000文字以上または200行以上)

## 基本的な使用方法

### 1. 環境変数の設定

```bash
# 必須
export GEMINI_API_KEY="your_gemini_api_key"

# オプション（詳細設定）
export GEMINI_MAX_CONCURRENT=3          # 並列リクエスト数上限
export GEMINI_REQUESTS_PER_MINUTE=60    # 1分あたりのリクエスト数上限
export GEMINI_MAX_RETRIES=3             # 最大リトライ回数
export GEMINI_BASE_DELAY=1.0            # 基本待機時間（秒）
export GEMINI_PRO_THRESHOLD_CHARS=8000  # proモデル使用の文字数閾値
export GEMINI_PRO_THRESHOLD_LINES=200   # proモデル使用の行数閾値
```

### 2. コードでの使用

```python
from tools import get_gemini_config, create_gemini_client

# 設定を取得
config = get_gemini_config()

# クライアントを作成
client = create_gemini_client(config)

# 翻訳実行
result = client.generate_content(
    prompt="以下の英語を日本語に翻訳してください:",
    content="Hello, world!"  # モデル選択に使用
)

print(result)  # 翻訳結果
```

### 3. GeminiTranslatorでの使用

既存の`GeminiTranslator`は自動的に新しいLLM層を使用します：

```python
from scripts.translate_chunk import GeminiTranslator

# 新しいLLM層を使用（デフォルト）
translator = GeminiTranslator(use_new_llm=True)

# 翻訳実行
result = translator.translate_chunk("This is a test.")
```

## モック機能（テスト用）

本番環境のAPIキーを使わずにテストを行うことができます：

```python
from tools import get_gemini_config, create_gemini_client

config = get_gemini_config()
# APIキーが "fake" または "test_" で始まる場合、自動的にモックを使用
client = create_gemini_client(config, mock=True)

result = client.generate_content("テストプロンプト", "テストコンテンツ")
print(result)  # モック翻訳結果

# 統計情報の取得
if hasattr(client, 'get_stats'):
    stats = client.get_stats()
    print(f"API呼び出し回数: {stats['total_calls']}")
    print(f"モデル使用状況: {stats['model_usage']}")
```

## 設定オプション

### GeminiConfig

| パラメータ | デフォルト値 | 説明 |
|-----------|-------------|------|
| `api_key` | 環境変数 `GEMINI_API_KEY` | Gemini API キー |
| `pro_model` | `gemini-1.5-pro` | 高精度モデル名 |
| `flash_model` | `gemini-1.5-flash` | 高速モデル名 |
| `pro_threshold_chars` | `8000` | proモデル使用の文字数閾値 |
| `pro_threshold_lines` | `200` | proモデル使用の行数閾値 |
| `max_concurrent_requests` | `3` | 並列リクエスト数上限 |
| `requests_per_minute` | `60` | 1分あたりのリクエスト数上限 |
| `max_retries` | `3` | 最大リトライ回数 |
| `base_delay` | `1.0` | 基本待機時間（秒） |
| `max_delay` | `60.0` | 最大待機時間（秒） |
| `jitter_max` | `0.5` | ジッター最大値（秒） |
| `request_timeout` | `120.0` | リクエストタイムアウト（秒） |

## エラーハンドリング

```python
from tools import create_gemini_client, get_gemini_config

try:
    config = get_gemini_config()
    client = create_gemini_client(config)
    result = client.generate_content("プロンプト", "コンテンツ")
    
    if result is None:
        print("翻訳が失敗しました（全リトライ試行後）")
    else:
        print(f"翻訳成功: {result}")
        
except ValueError as e:
    print(f"設定エラー: {e}")
except Exception as e:
    print(f"予期しないエラー: {e}")
```

## パフォーマンス監視

```python
import time
from tools import create_gemini_client, get_gemini_config

config = get_gemini_config()
client = create_gemini_client(config, mock=True)

# 複数リクエストのテスト
start_time = time.time()
for i in range(10):
    result = client.generate_content(f"プロンプト{i}", f"コンテンツ{i}")
    print(f"リクエスト{i+1}: {result[:50]}...")

elapsed = time.time() - start_time
print(f"総時間: {elapsed:.2f}秒")

# 統計情報
if hasattr(client, 'get_stats'):
    stats = client.get_stats()
    print(f"統計: {stats}")
```

## 注意事項

1. **API キー管理**: 本番環境では必ず適切なSecrets管理を使用してください
2. **レート制限**: Gemini APIの制限に従って設定値を調整してください
3. **モデル選択**: 用途に応じて閾値を調整してください
4. **リトライ制限**: 過度なリトライはAPIクォータを消費するため注意してください
5. **並列制限**: 同時接続数を増やしすぎるとレート制限に引っかかる可能性があります

## 互換性

- 既存の`GeminiTranslator`との完全な後方互換性
- 新しい機能はオプトイン方式
- 従来の実装へのフォールバック機能

この設計により、最小限の変更で高度なLLM呼び出し機能を利用できます。
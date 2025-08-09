# 差分検出・適用器 実装完了レポート

## 概要

Issue #29 の要件に従い、upstream の旧/新と既訳を突き合わせ、equal/insert/delete/replace を判断して適用する差分適用器を実装しました。

## 実装ファイル

### 新規実装ファイル

1. **`scripts/line_diff.py`** - 行レベル差分検出・操作モジュール
   - `OperationType` 枚挙型（equal/insert/delete/replace）
   - `LineOperation` データクラス（操作詳細と軽微変更判定）
   - `LineDiffAnalyzer` クラス（差分分析エンジン）

2. **`scripts/discover_changes.py`** - 変更検出スクリプト
   - `TranslationMetaManager` クラス（upstream_sha 管理）
   - `UpstreamChangeDiscoverer` クラス（upstream 変更検出）
   - translation-meta の upstream_sha を基準に行オペコード列挙

3. **`scripts/apply_changes.py`** - 変更適用スクリプト
   - `SemanticChangeDetector` クラス（LLM ベース意味判定）
   - `ChangeApplicator` クラス（ポリシー適用エンジン）
   - ポリシーに従い既訳温存/新規翻訳/削除/再翻訳を適用

### テストファイル

4. **`tests/test_line_diff.py`** - 行差分モジュールテスト（20テストケース）
5. **`tests/test_discover_changes.py`** - 変更検出テスト（16テストケース）
6. **`tests/test_apply_changes.py`** - 変更適用テスト（28テストケース）

### 補助ファイル

7. **`test_integration.py`** - 統合動作確認スクリプト
8. **`demo_usage.py`** - 使用方法デモスクリプト

## 主要機能

### 1. 行レベル差分検出
- difflib.SequenceMatcher を使用した高精度な行レベル差分分析
- equal/insert/delete/replace の4種類の操作を識別
- 類似度計算による軽微変更の自動判定

### 2. 軽微変更判定
- **閾値**: 類似度 ≥ 0.90 & トークン数差20%以内
- **検出対象**: 句読点・空白のみの変更
- **トークン化**: 英語・日本語対応の境界検出

### 3. LLM 意味判定
- Gemini API による YES/NO の意味変更判定
- API エラー時のフォールバック判定機能
- レート制御対応のプロンプト設計

### 4. 変更適用ポリシー
- **keep_existing**: 既訳維持（軽微変更・意味変更なし）
- **new_translation**: 新規翻訳（insert 操作）
- **delete**: 削除（delete 操作）
- **retranslate**: 再翻訳（意味的変更のある replace）

### 5. 行対応維持
- 置換レンジ内での 1:1 行対応の厳密な維持
- 削除処理での行数整合性の保持
- 逆順適用によるインデックス整合性確保

## 受入基準の達成

✅ **合成フィクスチャテスト**: 64個のテストケースで equal/insert/delete/replace の全パターンを検証

✅ **置換レンジ内 1:1 行対応**: `LineOperation` クラスで行範囲を厳密管理

✅ **軽微変更スキップ**: 類似度・トークン数・句読点判定の3段階チェック

✅ **再翻訳分岐網羅**: LLM判定とフォールバック判定の両方を実装

✅ **削除時行数整合**: 逆順処理とインデックス追跡で整合性保持

## 使用方法

### 基本コマンド
```bash
# 変更検出
python scripts/discover_changes.py --output changes.json

# 変更適用（ドライラン）
python scripts/apply_changes.py --changes-file changes.json --dry-run

# 実際の適用
python scripts/apply_changes.py --changes-file changes.json
```

### 環境設定
- `GEMINI_API_KEY` 環境変数（LLM 判定用、オプション）
- upstream リモートの設定（`git remote add upstream ...`）
- Poetry による依存関係管理

## テスト結果

```
64 passed, 0 failed
- line_diff: 20 tests passed
- discover_changes: 16 tests passed  
- apply_changes: 28 tests passed
```

## セキュリティ・ガード

- ✅ YES/NO 判定のみでLLM 出力を制限
- ✅ API エラー時のフォールバック処理
- ✅ レート制御前提の設計
- ✅ モッキング可能なテスト設計

## 統合テスト結果

統合テストでは実際の markdown ドキュメントの差分検出・適用を実行し、以下を確認：

- 8個の操作（equal: 4, replace: 4）を正確に検出
- 軽微変更判定の適切な動作
- 意味変更検出による再翻訳ポリシーの適用
- フォールバック判定機能の動作

## まとめ

Issue #29 で要求された差分検出・適用器を完全に実装しました。equal/insert/delete/replace の全操作パターンに対応し、軽微変更スキップと意味判定による再翻訳の分岐を網羅的にテストしています。置換レンジでの 1:1 行対応と削除時の行数整合性も厳密に維持されており、すべての受入基準を満たしています。
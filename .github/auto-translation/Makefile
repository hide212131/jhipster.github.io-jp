# JHipster日本語ドキュメント自動翻訳システム Makefile

.PHONY: install test run clean help run-dev

# デフォルトターゲット
help:
	@echo "JHipster日本語ドキュメント自動翻訳システム"
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  install     - 依存関係をインストール"
	@echo "  test        - テストを実行"
	@echo "  run         - 自動翻訳を実行（全体）"
	@echo "  run-dry     - 自動翻訳をドライランモードで実行"
	@echo "  run-new     - 新規ファイルのみ翻訳"
	@echo "  run-dev     - 開発モードで実行（フィルタオプション利用可能）"
	@echo "  clean       - 一時ファイルをクリーンアップ"
	@echo "  lint        - コード品質チェック"
	@echo ""
	@echo "環境変数:"
	@echo "  GEMINI_API_KEY  - Gemini APIキー（必須）"
	@echo "  GH_TOKEN        - GitHub Token（PR作成用）"
	@echo "  COMMIT_HASH     - 特定のコミットハッシュを指定"
	@echo ""
	@echo "開発モードオプション例:"
	@echo "  make run-dev LIMIT=5                    # 5ファイルまで処理"
	@echo "  make run-dev PATHS='docs/ src/'         # 特定パスのみ"
	@echo "  make run-dev BEFORE=abc1234             # 指定コミット以前の変更のみ"
	@echo "  make run-dev LIMIT=3 PATHS='docs/'     # 組み合わせ"

# 依存関係インストール
install:
	@echo "📦 Installing dependencies..."
	poetry install

# テスト実行
test:
	@echo "🧪 Running tests..."
	poetry run pytest tests/ -v

# コード品質チェック
lint:
	@echo "🔍 Running code quality checks..."
	poetry run python -m py_compile scripts/*.py
	@echo "✅ Code quality check completed"

# 自動翻訳実行（全体）
run: check-env
	@echo "🚀 Running auto-translation (full mode)..."
	@if [ -n "$(COMMIT_HASH)" ]; then \
		poetry run python scripts/fetch_upstream.py --hash "$(COMMIT_HASH)"; \
	else \
		poetry run python scripts/fetch_upstream.py; \
	fi
	@poetry run python scripts/classify_changes.py --output-format json > classification.json
	@poetry run python scripts/classify_changes.py --output-format summary
	@poetry run python scripts/translate_chunk.py --classification classification.json --mode all
	@poetry run python scripts/postprocess.py --classification classification.json
	@poetry run python scripts/commit_and_pr.py --classification classification.json

# ドライランモードで実行
run-dry: check-env
	@echo "🧪 Running auto-translation (dry-run mode)..."
	@export DRY_RUN=true && $(MAKE) run

# 新規ファイルのみ翻訳
run-new: check-env
	@echo "🆕 Running auto-translation (new files only)..."
	@if [ -n "$(COMMIT_HASH)" ]; then \
		poetry run python scripts/fetch_upstream.py --hash "$(COMMIT_HASH)"; \
	else \
		poetry run python scripts/fetch_upstream.py; \
	fi
	@poetry run python scripts/classify_changes.py --output-format json > classification.json
	@poetry run python scripts/translate_chunk.py --classification classification.json --mode new-only
	@poetry run python scripts/postprocess.py --classification classification.json
	@poetry run python scripts/commit_and_pr.py --classification classification.json

# 選択的翻訳（衝突ファイル除外）
run-selective: check-env
	@echo "📝 Running auto-translation (selective mode)..."
	@if [ -n "$(COMMIT_HASH)" ]; then \
		poetry run python scripts/fetch_upstream.py --hash "$(COMMIT_HASH)"; \
	else \
		poetry run python scripts/fetch_upstream.py; \
	fi
	@poetry run python scripts/classify_changes.py --output-format json > classification.json
	@poetry run python scripts/translate_chunk.py --classification classification.json --mode selective
	@poetry run python scripts/postprocess.py --classification classification.json
	@poetry run python scripts/commit_and_pr.py --classification classification.json

# クリーンアップ
clean:
	@echo "🧹 Cleaning up..."
	@rm -f classification.json
	@rm -f *.log
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed"

# 環境変数チェック
check-env:
	@if [ -z "$(GEMINI_API_KEY)" ] || [ "$(GEMINI_API_KEY)" = "fake_api_key_for_development" ]; then \
		echo "❌ GEMINI_API_KEY environment variable is required"; \
		echo "   Please set your Gemini API key:"; \
		echo "   export GEMINI_API_KEY=your_actual_api_key"; \
		exit 1; \
	fi

# 開発環境セットアップ
dev-setup: install
	@echo "🔧 Setting up development environment..."
	@cp .env.sample .env || true
	@echo "✅ Development environment setup completed"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env file with your actual API keys"
	@echo "2. Run 'make test' to verify setup"
	@echo "3. Run 'make run-dry' to test translation workflow"

# 個別スクリプト実行
fetch:
	@poetry run python scripts/fetch_upstream.py $(if $(COMMIT_HASH),--hash $(COMMIT_HASH))

classify:
	@poetry run python scripts/classify_changes.py

translate:
	@poetry run python scripts/translate_chunk.py --classification classification.json --mode selective

postprocess:
	@poetry run python scripts/postprocess.py --classification classification.json

commit:
	@poetry run python scripts/commit_and_pr.py --classification classification.json

# 開発モード実行
run-dev:
	@echo "🧪 Running auto-translation (development mode)..."
	@$(eval DEV_ARGS := --mode dev)
	@$(eval DEV_ARGS += $(if $(COMMIT_HASH),--hash $(COMMIT_HASH),--hash HEAD))
	@$(eval DEV_ARGS += $(if $(BEFORE),--before $(BEFORE)))
	@$(eval DEV_ARGS += $(if $(LIMIT),--limit $(LIMIT)))
	@$(eval DEV_ARGS += $(if $(PATHS),--paths $(PATHS)))
	@$(eval DEV_ARGS += $(if $(DRY_RUN),--dry-run))
	@echo "   Options: $(DEV_ARGS)"
	@cd ../.. && python .github/auto-translation/scripts/run_translation_pipeline.py $(DEV_ARGS)

# 開発モードドライラン
run-dev-dry:
	@echo "🧪 Running auto-translation (development mode - dry run)..."
	@$(MAKE) run-dev DRY_RUN=1
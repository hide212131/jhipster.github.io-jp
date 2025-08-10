# JHipsterの公開[Webサイト（日本語）](https://www.jhipster.tech/jp/) のソースです

- 本家のWebサイト： https://www.jhipster.tech/
- 本家のリポジトリ： https://github.com/jhipster/jhipster.github.io 
- [日本語訳について](#日本語訳について)
- [自動翻訳システム](#自動翻訳システム)

<p align="center">
  <br />
  <a href="https://jhipster.tech">
    <img src="./static/images/logo/logo-jhipster.svg" height="60px">
  </a>
</p>

<p align="center">
  <a href="https://jhipster.tech">JHipster</a> ウェブサイトは、最新の静的サイトジェネレーターである <a href="https://docusaurus.io/">Docusaurus</a> を使用して構築されています。
</p>
<br />

### インストール

```
npm install
```

### ローカル開発

```
npm start
```

このコマンドにより、ローカル開発サーバーが起動し、ブラウザウィンドウが開きます。ほとんどの変更は、サーバーの再起動を必要とせずにライブで反映されます。

### ビルド

```
npm run build
```

このコマンドは、`build`ディレクトリに静的コンテンツを生成し、任意の静的コンテンツホスティングサービスで提供できます。

### デプロイ

SSHを使用する場合:

```
USE_SSH=true npm run deploy
```

SSHを使用しない場合:

```
GIT_USER=<あなたのGitHubユーザー名> npm run deploy
```

GitHub Pagesをホスティングに使用している場合、このコマンドはウェブサイトをビルドして`gh-pages`ブランチにプッシュする便利な方法です。

## 日本語訳について
本サイトの日本語訳にあたっては、OSS活動へも使用可能な[みんなの自動翻訳＠TexTra®](https://mt-auto-minhon-mlt.ucri.jgn-x.jp/)の翻訳内容を活用させていただきました。この場を借りてお礼を申し上げます。

翻訳の文体は、本家のpackage.jsonにtextlintパッケージを加えての指摘と、TexTraの翻訳内容になるべく従うことで、統一させています。

誤訳や不自然な言い回しが無いよう、注意しながら進めてはいますが、もし問題がありましたら、Issue/PRでご指摘ください。

## 本家の追従方法
本家の更新に伴う日本語訳の追従については、ReactやVueの翻訳での実績がある、[オープンソースドキュメント翻訳プラットフォームとしての GitHub](https://zenn.dev/smikitky/articles/0d250f7367eda9)の運用方法がとても素晴らしく、参考にしています。この場を借りてお礼を申し上げます。

運用方法は以下の通りです。
- [Github Actions](https://github.com/jhipster/jp/actions/workflows/sync-upstream.yml)で以下を処理
  - 定期的に本家の`main`をチェック
  - 更新があれば翻訳用`sync`ブランチを作成
  - 本家の差分を翻訳中（コンフリクトマーカー有）状態として`sync`へコミット
  - `sync`を`main`にマージするプルリクエストを作成
- 翻訳者がプルリクエストの内容を確認し、`sync`の内容を翻訳しコミット
- `main`にマージ

## ページ表示
本家と同様、Github Pagesを使って表示します。表示元は`gh-pages`ブランチの内容になります。

`gh-pages`はほぼ全て`main`ブランチと同様ですが、ごく一部、日本語サイト表示のために`gh-pages`のみ変更した内容があります。
`main`との差分は[こちら](https://github.com/jhipster/jp/compare/main...gh-pages)を見て確認してください。
`main`に書かない理由は、本家のサイトの構造上、`main`に入れるとローカルのテスト環境で動かないためです。
結果、本家との差分が`main`と`gh-pages`で散在しまいますが、`gh-pages`の変更箇所は大幅なサイトの変更がない限りほぼ更新することはないので、しばらくこの構造で運用していきます。

## 自動翻訳システム

このリポジトリには、upstream（本家）の更新を自動的に翻訳するシステムが組み込まれています。

### 概要

- **LLM**: Google Gemini APIを使用した自動翻訳
- **スケジュール**: 毎日12:00 JST（UTC 03:00）に自動実行
- **プロセス**: upstream取得 → 変更分類 → 翻訳 → ポストプロセッシング → PR作成

### システム要件

- Python 3.11+
- Poetry（依存関係管理）
- 必要なAPIキー（Gemini API、GitHub Token）

### ローカル実行

#### 1. 環境セットアップ

```bash
# 自動翻訳ディレクトリに移動
cd .github/auto-translation

# 依存関係インストール
make install

# 開発環境セットアップ
make dev-setup

# 環境変数設定（.envファイルを編集）
cp .env.sample .env
# GEMINI_API_KEY、GH_TOKEN等を設定
```

#### 2. 自動翻訳実行

```bash
# 自動翻訳ディレクトリ内で実行
cd .github/auto-translation

# ドライランモード（実際のコミット・PRなし）
make run-dry

# 新規ファイルのみ翻訳
make run-new

# 選択的翻訳（衝突ファイル除外）
make run-selective

# 全ファイル翻訳
make run
```

#### 3. 個別スクリプト実行

```bash
# 自動翻訳ディレクトリ内で実行
cd .github/auto-translation

# upstream取得
make fetch

# 変更分類
make classify

# 翻訳
make translate

# ポストプロセッシング
make postprocess

# コミット＆PR作成
make commit
```

### ファイル構成

```
├── .github/auto-translation/     # 自動翻訳システム
│   ├── scripts/                  # Python翻訳スクリプト
│   │   ├── fetch_upstream.py     # upstream取得とマージ
│   │   ├── classify_changes.py   # 変更ファイル分類
│   │   ├── translate_chunk.py    # Gemini翻訳
│   │   ├── postprocess.py        # ポストプロセッシング
│   │   └── commit_and_pr.py      # コミット＆PR作成
│   ├── tests/                    # テストファイル
│   ├── docs/style-guide.md       # 翻訳スタイルガイド
│   ├── spec.md                   # システム仕様書
│   ├── tasks.md                  # タスク一覧
│   ├── pyproject.toml           # Poetry設定
│   ├── Makefile                 # 実行用コマンド
│   └── .env.sample              # 環境変数サンプル
└── .github/workflows/
    └── auto-translation.yml      # 自動翻訳ワークフロー
```

### 翻訳品質

- **スタイルガイド**: `.github/auto-translation/docs/style-guide.md`に統一ルールを定義
- **品質チェック**: LanguageToolによる文法チェック
- **一貫性**: 既存翻訳との用語統一
- **レビュー**: 自動生成されたPRは人間による確認が推奨

### 制約事項

- **API制限**: Gemini APIの利用制限に注意
- **翻訳精度**: LLM翻訳のため人間によるレビューが必要
- **コンフリクト**: 大きな変更がある場合は手動解決が必要

### トラブルシューティング

#### よくある問題

1. **API エラー**
   ```bash
   # API キーを確認
   echo $GEMINI_API_KEY
   ```

2. **翻訳品質の問題**
   - `.github/auto-translation/docs/style-guide.md`を更新
   - テスト実行で検証: `cd .github/auto-translation && make test`

3. **Git エラー**
   ```bash
   # リポジトリ状態をクリーンアップ
   git status
   git clean -fd
   ```

詳細な仕様については以下のドキュメントを参照してください：
- 仕様書: `.github/auto-translation/spec.md`
- タスク一覧: `.github/auto-translation/tasks.md`

**注意**: 自動翻訳システムは`.github/auto-translation`ディレクトリ内で完結して管理されており、メインプロジェクトのファイル構成に影響しません。

## Secrets運用方針

### GEMINI_API_KEY の取り扱いについて

**重要**: このリポジトリでは以下のSecrets運用方針を採用しています：

- ✅ **上流リポジトリのみ**: `GEMINI_API_KEY` はメインリポジトリでのみ使用
- ❌ **フォークでは無効**: フォークされたリポジトリでは自動翻訳は利用不可
- ❌ **PRでは無効**: プルリクエストイベントでは `GEMINI_API_KEY` は参照不可

これにより、機密情報の漏洩を防ぎつつ、安全な自動翻訳システムを運用しています。

詳細については `SECURITY.md` を参照してください。

## GitHub CLI の活用

### PR作成での使用

このプロジェクトでは、効率的なPR作成のためにGitHub CLI (`gh`) の使用を推奨します：

```bash
# GitHub CLI のインストール確認
gh --version

# PR作成
gh pr create --title "機能: 新機能の追加" --body "変更内容の詳細説明"

# ドラフトPRとして作成
gh pr create --draft --title "WIP: 作業中の機能"

# PR状態確認
gh pr status

# PR一覧表示
gh pr list --state open

# PRレビュー
gh pr review --approve
gh pr review --request-changes --body "修正が必要です"
```

### ラベル管理

リポジトリでは以下のラベルを使用します：

- `area:translation-pipeline`: 自動翻訳パイプライン関連
- `agent:copilot`: GitHub Copilotによる支援
- `priority:P2`: 中優先度
- `ci`: CI/CD関連  
- `security`: セキュリティ関連

```bash
# Issueにラベル追加
gh issue edit [issue-number] --add-label "area:translation-pipeline,priority:P2"
```

詳細な開発ガイドラインは `CONTRIBUTING.md` を参照してください。

### 貢献

自動翻訳システムの改善提案やバグ報告は、GitHubのIssueでお知らせください。
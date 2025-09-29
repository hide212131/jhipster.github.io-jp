# JHipsterの公開[Webサイト（日本語）](https://www.jhipster.tech/jp/) のソースです

- 本家のWebサイト： https://www.jhipster.tech/
- 本家のリポジトリ： https://github.com/jhipster/jhipster.github.io 
- [日本語訳について](#日本語訳について)
- [翻訳オートメーション](#翻訳オートメーション)

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
npm run build -- --locale en
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

## 翻訳オートメーション

upstream（本家）の更新は、Java 製の [`ai-docsite-translator`](https://github.com/hide212131/ai-docsite-translator) を利用して自動追従します。

### GitHub Actions ワークフロー

- **ワークフロー名**: `ai-docsite-translation`
- **スケジュール**: 毎日 12:30 JST (`cron: "30 3 * * *"`)
- **実行内容**: upstream 取得 → 翻訳 → PR 作成 (`sync-<upstream-short-sha>` ブランチ)
- **主要依存**: Java 21 / Gemini API (`GEMINI_API_KEY`), `GITHUB_TOKEN`
- **設定詳細**: `.github/workflows/ai-docsite-translation.yml`

### ローカル / `act` 検証

`tools/run-ai-docsite-translator.sh` でローカル実行、`act -j translate` で GitHub Actions を再現できます。環境変数は `.env.translator`（Git 管理外）および `.secrets.translator` で管理します。詳細手順は `.github/llm-translation/docs/runbook.md` を参照してください。

### 切り戻し手順

旧 Python パイプラインは撤去済みです。`ai-docsite-translator` に関する不具合が発生した場合は runbook のトラブルシュート節に従って手動同期を実施してください。

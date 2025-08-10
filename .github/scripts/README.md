# リポジトリ管理スクリプト

このディレクトリには、リポジトリの管理を自動化するスクリプトが含まれています。

## 利用可能なスクリプト

### setup-labels.sh
GitHub リポジトリに必要なラベルを一括作成するスクリプトです。

**使用方法:**
```bash
# 実行権限を確認
chmod +x .github/scripts/setup-labels.sh

# スクリプト実行
./.github/scripts/setup-labels.sh
```

**必要条件:**
- GitHub CLI (`gh`) がインストールされていること
- GitHub に認証済みであること (`gh auth login`)
- リポジトリに対する管理権限があること

**作成されるラベル:**
- `area:translation-pipeline` - 自動翻訳パイプライン関連
- `agent:copilot` - GitHub Copilot による支援
- `priority:P2` - 中優先度
- `ci` - CI/CD 関連
- `security` - セキュリティ関連

## 実行前の確認

```bash
# GitHub CLI の確認
gh --version

# 認証状態の確認
gh auth status

# リポジトリアクセス権限の確認
gh repo view --json permissions
```

## トラブルシューティング

### GitHub CLI がインストールされていない
```bash
# macOS (Homebrew)
brew install gh

# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

### 認証エラー
```bash
# GitHub への認証
gh auth login
```

### 権限エラー
リポジトリの管理者権限が必要です。リポジトリオーナーに権限の確認を依頼してください。
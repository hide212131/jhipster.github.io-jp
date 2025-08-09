#!/bin/bash

# GitHub ラベル管理スクリプト
# GitHub CLI (gh) を使用してラベルを作成・管理します

set -e

echo "🏷️  GitHub ラベル管理スクリプト"
echo "=============================="

# GitHub CLI の確認
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) がインストールされていません"
    echo "   インストール方法: https://cli.github.com/"
    exit 1
fi

# 認証確認
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI の認証が必要です"
    echo "   実行: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI の準備完了"
echo ""

# ラベル作成関数
create_label() {
    local name="$1"
    local description="$2"
    local color="$3"
    
    echo "📌 ラベル作成: $name"
    
    if gh label list | grep -q "^$name"; then
        echo "   ⚠️  既に存在します - スキップ"
    else
        if gh label create "$name" --description "$description" --color "$color"; then
            echo "   ✅ 作成完了"
        else
            echo "   ❌ 作成失敗"
        fi
    fi
}

echo "ラベル作成を開始..."
echo ""

# 必要なラベルを作成
create_label "area:translation-pipeline" "Issues related to the automatic translation pipeline and localization workflow" "0366d6"
create_label "agent:copilot" "Issues and PRs created or assisted by GitHub Copilot" "7C4DFF"
create_label "priority:P2" "Medium priority issue - should be addressed in current iteration" "fbca04"
create_label "ci" "Continuous Integration related issues" "1d76db"
create_label "security" "Security-related issues and enhancements" "d73a4a"

echo ""
echo "🎉 ラベル設定完了！"
echo ""
echo "📋 作成されたラベル一覧:"
gh label list | grep -E "(area:translation-pipeline|agent:copilot|priority:P2|ci|security)"

echo ""
echo "💡 使用方法:"
echo "   gh issue edit [issue-number] --add-label 'area:translation-pipeline'"
echo "   gh pr edit [pr-number] --add-label 'priority:P2,ci'"
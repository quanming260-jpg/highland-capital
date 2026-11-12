#!/usr/bin/env bash
# ==============================================================================
# HIGHLAND CAPITAL · 一键部署到 GitHub 脚本
# ==============================================================================
set -e

PROJECT_DIR="/Users/qiaoquanming/.gemini/antigravity/scratch/highland_capital"
cd "$PROJECT_DIR"

echo "=========================================================="
echo "  HIGHLAND CAPITAL · GitHub 仓库与在线 Pages 部署向导"
echo "=========================================================="
echo ""

# 检查 git
if ! command -v git &> /dev/null; then
    echo "❌ 未检测到 git，请先安装 git。"
    exit 1
fi

# 检查当前 git status
echo "📦 正在检查本地代码变更..."
git add .
if git status -s | grep -q .; then
    git commit -m "update: sync Highland Capital latest changes" || true
    echo "✅ 本地变更已自动提交。"
else
    echo "✅ 本地代码已是最新提交状态。"
fi

# 检查是否已配置 remote origin
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REMOTE_URL" ]; then
    echo ""
    echo "🔍 当前仓库尚未关联 GitHub 远程仓库。"
    echo "----------------------------------------------------------"
    echo "请在下方粘贴您在 GitHub 新建的仓库地址："
    echo "例如: https://github.com/<您的用户名>/highland-capital.git"
    echo "或者: git@github.com:<您的用户名>/highland-capital.git"
    echo "----------------------------------------------------------"
    read -p "请输入仓库地址: " INPUT_URL

    if [ -z "$INPUT_URL" ]; then
        echo "❌ 未输入仓库地址，取消部署。"
        exit 1
    fi

    git remote add origin "$INPUT_URL"
    echo "✅ 成功关联远程仓库: $INPUT_URL"
else
    echo "🔗 已检测到关联的远程仓库: $REMOTE_URL"
fi

# 执行推送
echo ""
echo "🚀 正在推送到 GitHub main 分支..."
git branch -M main
git push -u origin main

echo ""
echo "=========================================================="
echo "🎉 恭喜！项目已成功推送到您的 GitHub 仓库！"
echo "=========================================================="
echo ""
echo "📱 如何在手机/外网直接查看 3D 交易室："
echo "1. 打开您的 GitHub 仓库页面"
echo "2. 点击右上角 Settings -> 侧边栏 Pages"
echo "3. 在 'Build and deployment' 下的 Source 选择 'GitHub Actions' (或 Deploy from a branch: main)"
echo "4. 等待 30 秒，GitHub Pages 将生成专属在线链接："
echo "   👉 https://<您的GitHub用户名>.github.io/<仓库名>/"
echo "   用手机或外部电脑浏览器直接打开即可全屏畅玩 3D Loft、看盘和简报！"
echo "=========================================================="

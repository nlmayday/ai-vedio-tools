#!/bin/bash

# 封面生成快捷脚本

if [ -z "$1" ]; then
    echo "用法: ./generate_cover.sh <视频文件>"
    echo ""
    echo "示例:"
    echo "  ./generate_cover.sh ./data/video.mp4"
    exit 1
fi

VIDEO="$1"

if [ ! -f "$VIDEO" ]; then
    echo "❌ 视频文件不存在: $VIDEO"
    exit 1
fi

# 检查 API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  未设置 DEEPSEEK_API_KEY"
    echo ""
    echo "AI 将无法生成文案，将使用默认文案。"
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🎨 生成封面: $(basename "$VIDEO")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../src/auto_generate_cover.py" --video "$VIDEO"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 完成！查看输出："
echo "   ls -lh output/$(basename "${VIDEO%.*}")/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


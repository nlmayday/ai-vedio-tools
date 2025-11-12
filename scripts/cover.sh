#!/bin/bash

# 封面生成快捷脚本

if [ -z "$1" ]; then
    echo "用法: ./cover.sh <视频文件>"
    echo ""
    echo "示例:"
    echo "  ./cover.sh ../data/video.mp4"
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
    echo "设置方法："
    echo "  export DEEPSEEK_API_KEY=\"your_api_key\""
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🎨 生成封面"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📹 视频: $(basename "$VIDEO")"
echo ""

python ../src/auto_generate_cover.py --video "$VIDEO"

VIDEO_NAME=$(basename "${VIDEO%.*}")
OUTPUT_DIR="../output/$VIDEO_NAME"

if [ -d "$OUTPUT_DIR" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 生成完成！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📁 输出目录: $OUTPUT_DIR/"
    echo ""
    echo "📄 生成的文件："
    ls -lh "$OUTPUT_DIR"/*.jpg 2>/dev/null | awk '{print "   ", $9, "-", $5}'
    echo ""
    echo "📝 B站信息:"
    echo "   cat $OUTPUT_DIR/cover_texts.json"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi


#!/bin/bash

# 从图片生成封面快捷脚本

if [ -z "$1" ]; then
    echo "用法: ./image_to_cover.sh <背景图片> [标题1] [标题2] [中文字幕] [英文字幕] [其他选项...]"
    echo ""
    echo "示例:"
    echo "  ./image_to_cover.sh ./data/background.jpg \"精彩内容\" \"即将开始\""
    echo "  ./image_to_cover.sh ./data/photo.png \"AI工具\" \"\" \"智能工具集\" \"AI Tools\""
    echo "  ./image_to_cover.sh ./data/photo.png \"标题\" \"\" \"\" \"\" -s vibrant"
    echo "  ./image_to_cover.sh ./data/photo.png \"标题\" \"\" \"\" \"\" --scheme elegant -o my_cover.jpg"
    echo ""
    echo "参数说明:"
    echo "  背景图片: 必需，图片文件路径"
    echo "  标题1: 可选，主标题第一行"
    echo "  标题2: 可选，主标题第二行"
    echo "  中文字幕: 可选"
    echo "  英文字幕: 可选"
    echo "  其他选项: -s/--scheme <方案>, -o/--output <文件>, -w/--width <宽>, -ht/--height <高>"
    echo ""
    echo "配色方案: modern(默认), vibrant, elegant, fresh"
    exit 1
fi

IMAGE_PATH="$1"
TITLE1="${2:-}"
TITLE2="${3:-}"
SUBTITLE_CN="${4:-}"
SUBTITLE_EN="${5:-}"

# 获取其他参数（从第6个参数开始）
shift 5
EXTRA_ARGS="$@"

echo "🖼️  从图片生成封面"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📸 背景图片: $(basename "$IMAGE_PATH")"
if [ -n "$TITLE1" ]; then
    echo "📝 标题1: $TITLE1"
fi
if [ -n "$TITLE2" ]; then
    echo "📝 标题2: $TITLE2"
fi
if [ -n "$SUBTITLE_CN" ]; then
    echo "🇨🇳 中文字幕: $SUBTITLE_CN"
fi
if [ -n "$SUBTITLE_EN" ]; then
    echo "🇬🇧 英文字幕: $SUBTITLE_EN"
fi
if [ -n "$EXTRA_ARGS" ]; then
    echo "⚙️  额外参数: $EXTRA_ARGS"
fi
echo ""

# 检查图片文件
if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ 背景图片不存在: $IMAGE_PATH"
    exit 1
fi

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 构建命令
CMD="python3 \"$SCRIPT_DIR/../src/image_to_cover.py\" --image \"$IMAGE_PATH\""

if [ -n "$TITLE1" ]; then
    CMD="$CMD --title1 \"$TITLE1\""
fi

if [ -n "$TITLE2" ]; then
    CMD="$CMD --title2 \"$TITLE2\""
fi

if [ -n "$SUBTITLE_CN" ]; then
    CMD="$CMD --subtitle-cn \"$SUBTITLE_CN\""
fi

if [ -n "$SUBTITLE_EN" ]; then
    CMD="$CMD --subtitle-en \"$SUBTITLE_EN\""
fi

# 添加额外参数
if [ -n "$EXTRA_ARGS" ]; then
    CMD="$CMD $EXTRA_ARGS"
fi

# 执行命令
eval "$CMD"

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 生成完成！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📁 查看输出文件: cover.jpg"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ 生成失败"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    exit 1
fi

#!/bin/bash

# 字幕翻译快捷脚本

if [ -z "$1" ]; then
    echo "用法: ./translate.sh <英文字幕文件>"
    echo ""
    echo "示例:"
    echo "  ./translate.sh ./data/video.en.vtt"
    echo ""
    echo "或批量翻译："
    echo "  ./translate.sh --batch ./data"
    exit 1
fi

# 检查 API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ 请先设置 DEEPSEEK_API_KEY"
    echo ""
    echo "设置方法："
    echo "  export DEEPSEEK_API_KEY=\"your_api_key\""
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ "$1" = "--batch" ]; then
    # 批量翻译
    DIR="${2:-$PROJECT_ROOT/data}"
    echo "📝 批量翻译目录: $DIR"
    python "$SCRIPT_DIR/../src/batch_translate_subtitles.py" --input-dir "$DIR"
else
    # 单文件翻译
    INPUT="$1"

    if [ ! -f "$INPUT" ]; then
        echo "❌ 文件不存在: $INPUT"
        exit 1
    fi

    echo "📝 翻译字幕: $INPUT"
    echo "🤖 使用智能翻译器..."
    python "$SCRIPT_DIR/../src/subtitle_translator_smart.py" --input "$INPUT"
fi


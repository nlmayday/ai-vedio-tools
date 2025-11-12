#!/bin/bash

# 字幕合并快捷脚本

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "用法: ./merge_subtitle.sh <视频> <英文字幕> <中文字幕>"
    echo ""
    echo "示例:"
    echo "  ./merge_subtitle.sh \\"
    echo "    ./data/video.webm \\"
    echo "    ./data/video.en.vtt \\"
    echo "    ./data/video.zh.vtt"
    exit 1
fi

VIDEO="$1"
EN_SUB="$2"
ZH_SUB="$3"

# 检查文件
for file in "$VIDEO" "$EN_SUB" "$ZH_SUB"; do
    if [ ! -f "$file" ]; then
        echo "❌ 文件不存在: $file"
        exit 1
    fi
done

echo "🎬 合并字幕到视频"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📹 视频: $(basename "$VIDEO")"
echo "🇬🇧 英文: $(basename "$EN_SUB")"
echo "🇨🇳 中文: $(basename "$ZH_SUB")"
echo ""

# 从配置文件读取字幕类型
SUBTITLE_TYPE=$(grep "type:" ../config.yaml | awk '{print $2}')
SUBTITLE_TYPE=${SUBTITLE_TYPE:-soft}

echo "📦 字幕类型: $SUBTITLE_TYPE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 生成输出路径
VIDEO_NAME=$(basename "${VIDEO%.*}")
OUTPUT_DIR="../output/$VIDEO_NAME"
mkdir -p "$OUTPUT_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../src/video_subtitle_merger.py" \
  --video "$VIDEO" \
  --en-subtitle "$EN_SUB" \
  --zh-subtitle "$ZH_SUB" \
  --output "$OUTPUT_DIR/video_bilingual_${SUBTITLE_TYPE}.mp4"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 完成！输出目录："
echo "   $OUTPUT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


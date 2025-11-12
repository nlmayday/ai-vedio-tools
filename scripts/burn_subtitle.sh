#!/bin/bash

# 硬字幕烧录快捷脚本（适合B站）

if [ -z "$1" ]; then
    echo "用法: ./burn_subtitle.sh <视频文件> [字幕文件]"
    echo ""
    echo "示例:"
    echo "  ./burn_subtitle.sh ../data/video.webm"
    echo "  ./burn_subtitle.sh ../data/video.webm ../data/video_bilingual.srt"
    echo ""
    echo "💡 提示："
    echo "  - 如果不指定字幕文件，会自动查找同名的 _bilingual.srt"
    echo "  - 需要在新终端窗口运行"
    echo "  - 预计时间：15-20分钟"
    exit 1
fi

VIDEO="$1"
SRT="$2"

if [ ! -f "$VIDEO" ]; then
    echo "❌ 视频文件不存在: $VIDEO"
    exit 1
fi

# 自动查找字幕文件
if [ -z "$SRT" ]; then
    VIDEO_BASE="${VIDEO%.*}"
    SRT="${VIDEO_BASE}_bilingual.srt"
    
    if [ ! -f "$SRT" ]; then
        echo "❌ 未找到字幕文件: $SRT"
        echo ""
        echo "请先生成字幕或手动指定字幕文件"
        exit 1
    fi
    
    echo "✅ 自动找到字幕: $(basename "$SRT")"
    echo ""
fi

VIDEO_NAME=$(basename "${VIDEO%.*}")
OUTPUT_DIR="../output/$VIDEO_NAME"
mkdir -p "$OUTPUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔥 烧录硬字幕（B站专用）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📹 视频: $(basename "$VIDEO")"
echo "📄 字幕: $(basename "$SRT")"
echo "📁 输出: $OUTPUT_DIR/video_bilingual_hard.mp4"
echo ""
echo "⏱️  预计时间: 15-20 分钟"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 获取视频和字幕的绝对路径
VIDEO_ABS=$(cd "$(dirname "$VIDEO")" && pwd)/$(basename "$VIDEO")
SRT_ABS=$(cd "$(dirname "$SRT")" && pwd)/$(basename "$SRT")
OUTPUT_ABS="$OUTPUT_DIR/video_bilingual_hard.mp4"

# 确保输出目录存在
mkdir -p "$(dirname "$OUTPUT_ABS")"

# 切换到输出目录避免路径问题
cd "$OUTPUT_DIR"

# 复制字幕为简单名字
cp "$SRT_ABS" "temp_subtitle.srt"

echo "开始烧录..."
echo ""

# 烧录硬字幕
ffmpeg -i "$VIDEO_ABS" \
  -vf "subtitles=temp_subtitle.srt" \
  -c:a copy \
  -y "video_bilingual_hard.mp4"

# 清理临时文件
rm -f temp_subtitle.srt

# 检查结果
if [ -f "video_bilingual_hard.mp4" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 硬字幕视频生成成功！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ls -lh video_bilingual_hard.mp4
    echo ""
    echo "📁 输出位置: $OUTPUT_DIR/"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "❌ 生成失败"
fi


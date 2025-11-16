#!/bin/bash
# 视频分段变速处理脚本 - 裁剪模式 + 自动生成封面
# 只保留配置的片段，删除未配置的部分，然后自动生成4种配色封面
# 使用方法: ./adjust_speed_cut.sh <输入视频>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/../src/speed_adjuster_cut.py"
THUMBNAIL_SCRIPT="${SCRIPT_DIR}/../src/thumbnail_generator.py"

# 检查参数
if [ $# -lt 1 ]; then
    echo "============================================"
    echo "视频分段变速工具 - 裁剪模式 + 自动封面"
    echo "============================================"
    echo "⚠️  只保留配置的片段，删除未配置的部分"
    echo "✅ 处理完成后自动生成4种配色封面"
    echo ""
    echo "用法: $0 <输入视频>"
    echo ""
    echo "示例:"
    echo "  $0 ./input/07.mp4"
    echo ""
    echo "输出:"
    echo "  - 变速视频: ./output/07/07.mp4"
    echo "  - 封面: ./output/07/{modern,vibrant,elegant,fresh}.jpg"
    exit 1
fi

INPUT_VIDEO="$1"

# 检查输入文件
if [ ! -f "$INPUT_VIDEO" ]; then
    echo "❌ 错误: 输入视频不存在: $INPUT_VIDEO"
    exit 1
fi

# 自动使用默认配置文件
CONFIG_FILE="${PROJECT_ROOT}/examples/speed_config_example.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 从输入文件名提取名称（不含扩展名和路径）
INPUT_NAME=$(basename "$INPUT_VIDEO")
VIDEO_BASE="${INPUT_NAME%.*}"

# 生成输出路径：./output/07/07.mp4
OUTPUT_DIR="${PROJECT_ROOT}/output/${VIDEO_BASE}"
OUTPUT_VIDEO="${OUTPUT_DIR}/${VIDEO_BASE}.mp4"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo "============================================"
echo "视频分段变速处理 - 裁剪模式"
echo "============================================"
echo "⚠️  警告：未配置的片段将被删除！"
echo "============================================"
echo "输入视频: $INPUT_VIDEO"
echo "配置文件: $CONFIG_FILE"
echo "输出视频: $OUTPUT_VIDEO"
echo "============================================"
echo ""

# 执行 Python 脚本进行视频变速处理
python3 "$PYTHON_SCRIPT" "$INPUT_VIDEO" "$CONFIG_FILE" "$OUTPUT_VIDEO"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 视频处理失败！"
    exit 1
fi

echo ""
echo "============================================"
echo "✅ 视频处理完成！"
echo "输出文件: $OUTPUT_VIDEO"
echo "============================================"
echo ""
echo "🎨 开始生成封面..."
echo ""

# 生成4种配色的封面
for scheme in modern vibrant elegant fresh; do
    echo "生成 ${scheme} 封面..."
    python3 "$THUMBNAIL_SCRIPT" \
        --video "$OUTPUT_VIDEO" \
        --title1 "$VIDEO_BASE" \
        --title2 "" \
        --subtitle-cn "" \
        --scheme "$scheme" \
        --output "${OUTPUT_DIR}/${scheme}.jpg"
done

echo ""
echo "============================================"
echo "✨ 全部完成！"
echo "============================================"
echo "📁 输出目录: $OUTPUT_DIR"
echo ""
echo "生成的文件:"
echo "  - 视频: $OUTPUT_VIDEO"
echo "  - 封面: ${OUTPUT_DIR}/modern.jpg, ${OUTPUT_DIR}/vibrant.jpg, ${OUTPUT_DIR}/elegant.jpg, ${OUTPUT_DIR}/fresh.jpg"
echo "============================================"


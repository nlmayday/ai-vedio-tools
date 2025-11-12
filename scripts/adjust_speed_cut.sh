#!/bin/bash
# 视频分段变速处理脚本 - 裁剪模式
# 只保留配置的片段，删除未配置的部分
# 使用方法: ./adjust_speed_cut.sh <输入视频> <配置JSON文件> [输出视频]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/../src/speed_adjuster_cut.py"

# 检查参数
if [ $# -lt 2 ]; then
    echo "============================================"
    echo "视频分段变速工具 - 裁剪模式"
    echo "============================================"
    echo "⚠️  只保留配置的片段，删除未配置的部分"
    echo ""
    echo "用法: $0 <输入视频> <配置JSON文件> [输出视频]"
    echo ""
    echo "示例:"
    echo "  $0 input.mp4 speed_config.json output_cut.mp4"
    exit 1
fi

INPUT_VIDEO="$1"
CONFIG_FILE="$2"
OUTPUT_VIDEO="${3:-}"

# 检查输入文件
if [ ! -f "$INPUT_VIDEO" ]; then
    echo "❌ 错误: 输入视频不存在: $INPUT_VIDEO"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 如果没有指定输出文件，自动生成
if [ -z "$OUTPUT_VIDEO" ]; then
    INPUT_DIR=$(dirname "$INPUT_VIDEO")
    INPUT_NAME=$(basename "$INPUT_VIDEO")
    INPUT_BASE="${INPUT_NAME%.*}"
    INPUT_EXT="${INPUT_NAME##*.}"
    OUTPUT_VIDEO="${INPUT_DIR}/${INPUT_BASE}_cut.${INPUT_EXT}"
fi

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

# 执行 Python 脚本
python3 "$PYTHON_SCRIPT" "$INPUT_VIDEO" "$CONFIG_FILE" "$OUTPUT_VIDEO"

echo ""
echo "============================================"
echo "✅ 处理完成！"
echo "输出文件: $OUTPUT_VIDEO"
echo "============================================"


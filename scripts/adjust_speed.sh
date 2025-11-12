#!/bin/bash
# 视频分段变速处理脚本
# 使用方法: ./adjust_speed.sh <输入视频> <配置JSON文件> [输出视频]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/../src/speed_adjuster.py"

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法: $0 <输入视频> <配置JSON文件> [输出视频]"
    echo ""
    echo "参数说明:"
    echo "  输入视频       - 要处理的视频文件路径"
    echo "  配置JSON文件   - 包含速度配置的 JSON 文件"
    echo "  输出视频       - 输出视频路径（可选，默认为 <输入视频>_speed_adjusted.mp4）"
    echo ""
    echo "示例:"
    echo "  $0 input.mp4 speed_config.json"
    echo "  $0 input.mp4 speed_config.json output.mp4"
    echo ""
    echo "配置文件格式:"
    echo '  {'
    echo '      "part": ['
    echo '          {'
    echo '              "timestamp": "00:00:50 - 00:01:00",'
    echo '              "speed": 1.2'
    echo '          },'
    echo '          {'
    echo '              "timestamp": "00:01:00 - 00:01:10",'
    echo '              "speed": 1.0'
    echo '          }'
    echo '      ]'
    echo '  }'
    exit 1
fi

INPUT_VIDEO="$1"
CONFIG_FILE="$2"
OUTPUT_VIDEO="${3:-}"

# 检查输入文件是否存在
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
    OUTPUT_VIDEO="${INPUT_DIR}/${INPUT_BASE}_speed_adjusted.${INPUT_EXT}"
fi

echo "============================================"
echo "视频分段变速处理"
echo "============================================"
echo "输入视频: $INPUT_VIDEO"
echo "配置文件: $CONFIG_FILE"
echo "输出视频: $OUTPUT_VIDEO"
echo "============================================"
echo ""

# 检查 Python 脚本是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ 错误: Python 脚本不存在: $PYTHON_SCRIPT"
    exit 1
fi

# 执行 Python 脚本
python3 "$PYTHON_SCRIPT" "$INPUT_VIDEO" "$CONFIG_FILE" "$OUTPUT_VIDEO"

echo ""
echo "============================================"
echo "✅ 处理完成！"
echo "输出文件: $OUTPUT_VIDEO"
echo "============================================"


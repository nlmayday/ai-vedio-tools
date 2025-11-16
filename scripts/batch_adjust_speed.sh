#!/bin/bash
# 批量处理视频变速脚本
# 从 ./input 目录找到指定范围的视频文件，执行变速处理
# 使用方法: ./batch_adjust_speed.sh [起始编号] [结束编号]
# 示例: ./batch_adjust_speed.sh 8 15  # 处理 08.mp4 到 15.mp4

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 检查参数
if [ $# -gt 0 ] && [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "批量视频变速处理脚本"
    echo ""
    echo "用法: $0 [起始编号] [结束编号]"
    echo ""
    echo "示例:"
    echo "  $0 8 15    # 处理 08.mp4 到 15.mp4"
    echo "  $0 1 5     # 处理 01.mp4 到 05.mp4"
    echo "  $0         # 默认处理 08.mp4 到 15.mp4"
    echo ""
    echo "说明:"
    echo "  - 从 ./input 目录查找视频文件"
    echo "  - 执行变速处理并生成封面"
    echo "  - 输出到 ./output/编号/编号.mp4"
    exit 0
fi

START_NUM="${1:-8}"
END_NUM="${2:-15}"

# 移除前导零（如果有）
START_NUM=$((10#$START_NUM))
END_NUM=$((10#$END_NUM))

echo "============================================"
echo "批量视频变速处理"
echo "============================================"
echo "处理范围: $(printf "%02d" $START_NUM).mp4 到 $(printf "%02d" $END_NUM).mp4"
echo "输入目录: ${PROJECT_ROOT}/input"
echo "============================================"
echo ""

# 确保 input 目录存在
INPUT_DIR="${PROJECT_ROOT}/input"
mkdir -p "$INPUT_DIR"

# 计数器
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# 处理每个文件
# 将数字转换为两位数格式（08, 09, 10, ...）
for num in $(seq $START_NUM $END_NUM); do
    # 格式化为两位数
    num=$(printf "%02d" $num)
    INPUT_VIDEO="${INPUT_DIR}/${num}.mp4"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "处理: ${num}.mp4"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 检查文件是否存在
    if [ ! -f "$INPUT_VIDEO" ]; then
        echo "⚠️  文件不存在，跳过: $INPUT_VIDEO"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi
    
    # 执行变速处理
    echo "🚀 开始处理..."
    if "${SCRIPT_DIR}/adjust_speed_cut.sh" "$INPUT_VIDEO"; then
        echo "✅ ${num}.mp4 处理成功"
        
        # 重新生成封面，添加自定义标题和集数
        OUTPUT_DIR="${PROJECT_ROOT}/output/${num}"
        OUTPUT_VIDEO="${OUTPUT_DIR}/${num}.mp4"
        THUMBNAIL_SCRIPT="${SCRIPT_DIR}/../src/thumbnail_generator.py"
        
        # 转换为中文数字
        # 将两位数字符串转为数字（去除前导零）
        NUM_INT=$((10#$num))
        CHINESE_NUMBERS=("一" "二" "三" "四" "五" "六" "七" "八" "九" "十" "十一" "十二" "十三" "十四" "十五")
        NUM_INDEX=$((NUM_INT - 1))
        if [ $NUM_INDEX -ge 0 ] && [ $NUM_INDEX -lt ${#CHINESE_NUMBERS[@]} ]; then
            CHINESE_NUM="${CHINESE_NUMBERS[$NUM_INDEX]}"
        else
            CHINESE_NUM="$NUM_INT"
        fi
        
        if [ -f "$OUTPUT_VIDEO" ]; then
            echo "🎨 重新生成封面（带标题和集数）..."
            
            # 生成4种配色的封面
            for scheme in modern vibrant elegant fresh; do
                python3 "$THUMBNAIL_SCRIPT" \
                    --video "$OUTPUT_VIDEO" \
                    --title1 "斗破苍穹" \
                    --title2 "迦南学院" \
                    --subtitle-cn "第${CHINESE_NUM}集" \
                    --scheme "$scheme" \
                    --output "${OUTPUT_DIR}/${scheme}.jpg" 2>/dev/null || true
            done
            echo "✅ 封面生成完成"
        fi
        
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌ ${num}.mp4 处理失败"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
echo "============================================"
echo "✨ 批量处理完成"
echo "============================================"
echo "成功: $SUCCESS_COUNT"
echo "失败: $FAIL_COUNT"
echo "跳过: $SKIP_COUNT"
echo "总计: $((SUCCESS_COUNT + FAIL_COUNT + SKIP_COUNT))"
echo "============================================"


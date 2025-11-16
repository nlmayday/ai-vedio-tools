#!/bin/bash
# 批量生成封面脚本
# 为已有的视频生成封面（带标题和集数）
# 使用方法: ./batch_generate_covers.sh [起始编号] [结束编号]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
THUMBNAIL_SCRIPT="${SCRIPT_DIR}/../src/thumbnail_generator.py"

# 检查参数
if [ $# -gt 0 ] && [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "批量生成封面脚本"
    echo ""
    echo "用法: $0 [起始编号] [结束编号]"
    echo ""
    echo "示例:"
    echo "  $0 10 15    # 为 10-15 生成封面"
    echo "  $0 8 12     # 为 08-12 生成封面"
    exit 0
fi

START_NUM="${1:-10}"
END_NUM="${2:-15}"

# 移除前导零（如果有）
START_NUM=$((10#$START_NUM))
END_NUM=$((10#$END_NUM))

echo "============================================"
echo "批量生成封面"
echo "============================================"
echo "处理范围: $(printf "%02d" $START_NUM).mp4 到 $(printf "%02d" $END_NUM).mp4"
echo "输出目录: ${PROJECT_ROOT}/output"
echo "============================================"
echo ""

# 计数器
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# 中文数字数组
CHINESE_NUMBERS=("一" "二" "三" "四" "五" "六" "七" "八" "九" "十" "十一" "十二" "十三" "十四" "十五" "十六" "十七" "十八" "十九" "二十")

# 处理每个文件
for num in $(seq $START_NUM $END_NUM); do
    # 格式化为两位数
    num=$(printf "%02d" $num)
    OUTPUT_DIR="${PROJECT_ROOT}/output/${num}"
    OUTPUT_VIDEO="${OUTPUT_DIR}/${num}.mp4"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "处理: ${num}.mp4"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 检查视频文件是否存在
    if [ ! -f "$OUTPUT_VIDEO" ]; then
        echo "⚠️  视频不存在，跳过: $OUTPUT_VIDEO"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi
    
    # 转换为中文数字
    NUM_INT=$((10#$num))
    NUM_INDEX=$((NUM_INT - 1))
    if [ $NUM_INDEX -ge 0 ] && [ $NUM_INDEX -lt ${#CHINESE_NUMBERS[@]} ]; then
        CHINESE_NUM="${CHINESE_NUMBERS[$NUM_INDEX]}"
    else
        CHINESE_NUM="$NUM_INT"
    fi
    
    echo "🎨 生成封面（带标题和集数）..."
    echo "   标题1: 斗破苍穹"
    echo "   标题2: 迦南学院"
    echo "   集数: 第${CHINESE_NUM}集"
    
    # 生成4种配色的封面
    COVER_SUCCESS=0
    for scheme in modern vibrant elegant fresh; do
        if python3 "$THUMBNAIL_SCRIPT" \
            --video "$OUTPUT_VIDEO" \
            --title1 "斗破苍穹" \
            --title2 "迦南学院" \
            --subtitle-cn "第${CHINESE_NUM}集" \
            --scheme "$scheme" \
            --output "${OUTPUT_DIR}/${scheme}.jpg" 2>/dev/null; then
            COVER_SUCCESS=$((COVER_SUCCESS + 1))
        fi
    done
    
    if [ $COVER_SUCCESS -eq 4 ]; then
        echo "✅ ${num}.mp4 封面生成成功（4种配色）"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "⚠️  ${num}.mp4 封面生成部分失败（${COVER_SUCCESS}/4）"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
echo "============================================"
echo "✨ 批量生成完成"
echo "============================================"
echo "成功: $SUCCESS_COUNT"
echo "失败: $FAIL_COUNT"
echo "跳过: $SKIP_COUNT"
echo "总计: $((SUCCESS_COUNT + FAIL_COUNT + SKIP_COUNT))"
echo "============================================"


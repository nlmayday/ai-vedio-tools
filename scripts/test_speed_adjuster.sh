#!/bin/bash
# 视频分段变速工具测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "视频分段变速工具 - 测试"
echo "============================================"
echo ""

# 检查是否有测试视频
TEST_VIDEO=""
if [ -f "./data/AI and human evolution ｜ Yuval Noah Harari [jt3Ul3rPXaE].mp4" ]; then
    TEST_VIDEO="./data/AI and human evolution ｜ Yuval Noah Harari [jt3Ul3rPXaE].mp4"
elif [ -f "../output/AI and human evolution ｜ Yuval Noah Harari [jt3Ul3rPXaE]/video_bilingual_soft.mp4" ]; then
    TEST_VIDEO="../output/AI and human evolution ｜ Yuval Noah Harari [jt3Ul3rPXaE]/video_bilingual_soft.mp4"
else
    echo "未找到测试视频文件。"
    echo "请提供一个视频文件路径："
    read -r TEST_VIDEO
    
    if [ ! -f "$TEST_VIDEO" ]; then
        echo "❌ 错误: 文件不存在: $TEST_VIDEO"
        exit 1
    fi
fi

echo "使用测试视频: $TEST_VIDEO"
echo ""

# 创建测试配置
TEST_CONFIG="/tmp/test_speed_config.json"
cat > "$TEST_CONFIG" << 'EOF'
{
    "part": [
        {
            "timestamp": "00:00:05 - 00:00:15",
            "speed": 1.5,
            "comment": "前 10 秒加速 1.5 倍"
        },
        {
            "timestamp": "00:00:20 - 00:00:30",
            "speed": 0.8,
            "comment": "中间减速到 0.8 倍"
        },
        {
            "timestamp": "00:00:35 - 00:00:45",
            "speed": 1.3,
            "comment": "后面再加速 1.3 倍"
        }
    ]
}
EOF

echo "测试配置已生成: $TEST_CONFIG"
cat "$TEST_CONFIG"
echo ""

# 设置输出文件
OUTPUT_VIDEO="/tmp/test_speed_adjusted.mp4"

echo "============================================"
echo "开始处理..."
echo "============================================"
echo ""

# 执行处理
"${SCRIPT_DIR}/adjust_speed.sh" "$TEST_VIDEO" "$TEST_CONFIG" "$OUTPUT_VIDEO"

echo ""
echo "============================================"
echo "✅ 测试完成！"
echo "============================================"
echo "输出文件: $OUTPUT_VIDEO"
echo ""
echo "您可以使用以下命令查看视频："
echo "  open '$OUTPUT_VIDEO'"
echo "  # 或者"
echo "  vlc '$OUTPUT_VIDEO'"
echo ""
echo "如果效果满意，您可以："
echo "1. 修改配置文件 speed_config_example.json"
echo "2. 使用 ./adjust_speed.sh 处理您自己的视频"
echo ""


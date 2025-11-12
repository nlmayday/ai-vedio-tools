#!/bin/bash

# 自动处理系统快捷启动脚本

# 检查 API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ 请先设置 DEEPSEEK_API_KEY"
    echo ""
    echo "设置方法："
    echo "  export DEEPSEEK_API_KEY=\"your_api_key\""
    exit 1
fi

# 显示菜单
echo "🤖 视频自动处理系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "选择模式："
echo "  1) 执行一次处理"
echo "  2) 持续监控（推荐）"
echo "  3) 查看处理状态"
echo ""
read -p "请选择 (1-3): " choice
echo ""

case $choice in
    1)
        echo "▶️  执行一次处理..."
        python ../src/auto_process_videos.py
        ;;
    2)
        echo "🔄 启动持续监控（按 Ctrl+C 停止）..."
        python ../src/auto_process_videos.py --watch
        ;;
    3)
        echo "📊 处理状态："
        python ../src/auto_process_videos.py --status
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac


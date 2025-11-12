#!/bin/bash

# 准备B站上传（生成配置文件）
# 用法：./prepare_upload.sh "../output/视频名/"

if [ $# -eq 0 ]; then
    echo "❌ 请提供视频目录"
    echo ""
    echo "用法："
    echo "  ./prepare_upload.sh \"../output/视频名/\""
    echo ""
    echo "或查看所有可上传的视频："
    echo "  ./show_output.sh"
    exit 1
fi

VIDEO_DIR="$1"

# 运行配置生成
python3 ../src/bilibili_auto_upload.py --video-dir "$VIDEO_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 下一步：告诉 AI 执行上传"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "在 Cursor 中输入："
echo ""
echo "  @prepare_upload.sh 的输出"
echo "  请使用 MCP Playwright 帮我上传这个视频到B站"
echo ""


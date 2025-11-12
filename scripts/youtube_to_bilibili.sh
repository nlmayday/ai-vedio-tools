#!/bin/bash

# YouTube 视频自动处理并上传到 B 站
# 用法：./youtube_to_bilibili.sh "https://www.youtube.com/watch?v=VIDEO_ID"

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ 缺少 YouTube 链接${NC}"
    echo ""
    echo "用法："
    echo "  ./youtube_to_bilibili.sh \"https://www.youtube.com/watch?v=VIDEO_ID\""
    echo ""
    echo "示例："
    echo "  ./youtube_to_bilibili.sh \"https://www.youtube.com/watch?v=0zXSrsKlm5A\""
    exit 1
fi

YOUTUBE_URL="$1"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎥 YouTube 视频自动处理并上传到 B 站${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📺 YouTube:${NC} $YOUTUBE_URL"
echo ""

# 检查 yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${RED}❌ 未安装 yt-dlp${NC}"
    echo ""
    echo "请先安装："
    echo "  pip install yt-dlp"
    echo ""
    exit 1
fi

# 检查 DeepSeek API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  未设置 DEEPSEEK_API_KEY${NC}"
    echo ""
    echo "请先设置 API Key："
    echo "  export DEEPSEEK_API_KEY=\"your_api_key\""
    echo ""
    exit 1
fi

# 执行处理
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/../src/youtube_to_bilibili.py" "$YOUTUBE_URL"

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✨ 处理完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📝 下一步：在 Cursor 中告诉 AI 上传视频到B站${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 处理失败${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 1
fi


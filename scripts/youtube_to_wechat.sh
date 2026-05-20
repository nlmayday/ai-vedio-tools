#!/bin/bash
# YouTube转微信公众号文章 - 快速开始脚本

# 检查环境
check_env() {
    echo "🔍 检查环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ 未找到Python3，请先安装"
        exit 1
    fi
    echo "✅ Python3: $(python3 --version)"
    
    # 检查yt-dlp
    if ! command -v yt-dlp &> /dev/null; then
        echo "⚠️  未找到yt-dlp，正在安装..."
        pip3 install yt-dlp
    fi
    echo "✅ yt-dlp: $(yt-dlp --version)"
    
    # 检查API Key
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo "❌ 请设置环境变量 DEEPSEEK_API_KEY"
        echo "   export DEEPSEEK_API_KEY='your-api-key'"
        exit 1
    fi
    echo "✅ DeepSeek API Key已设置"
    echo ""
}

# 显示用法
usage() {
    cat << EOF
使用方法:
  $0 <YouTube URL> [选项]

选项:
  -w, --word-count <数字>    目标字数（默认: 2000）
  -s, --style <风格>         文章风格: professional/casual/academic（默认: professional）
  -o, --output <目录>        输出目录（默认: ../output/{video_id}）
  --skip-download           跳过下载，使用已有文件

示例:
  $0 https://www.youtube.com/watch?v=jt3Ul3rPXaE
  $0 https://www.youtube.com/watch?v=jt3Ul3rPXaE -w 3000 -s casual
  $0 https://www.youtube.com/watch?v=jt3Ul3rPXaE --skip-download

EOF
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi
    
    URL="$1"
    shift
    
    # 检查环境
    check_env
    
    # 进入src目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR/../src" || exit 1
    
    # 执行转换
    echo "🚀 开始转换..."
    echo ""
    python3 youtube_to_wechat.py "$URL" "$@"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅ 转换成功！"
        echo ""
        echo "📝 接下来的步骤："
        echo "1. 打开输出目录查看生成的文章"
        echo "2. 使用Markdown编辑器美化排版（推荐: https://editor.mdnice.com/）"
        echo "3. 复制到微信公众号后台发布"
        echo ""
    else
        echo ""
        echo "❌ 转换失败，请检查错误信息"
        exit $EXIT_CODE
    fi
}

main "$@"

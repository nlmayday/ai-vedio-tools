#!/bin/bash

# 查看输出快捷脚本

if [ -z "$1" ]; then
    echo "用法: ./show_output.sh <视频名>"
    echo ""
    echo "示例:"
    echo "  ./show_output.sh \"NVIDIA CEO Jensen Huang's Vision for the Future\""
    echo ""
    echo "或列出所有:"
    echo "  ./show_output.sh --list"
    exit 1
fi

if [ "$1" = "--list" ]; then
    echo "📁 所有输出目录:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ -d "../output" ]; then
        for dir in ../output/*/; do
            if [ -d "$dir" ]; then
                VIDEO_NAME=$(basename "$dir")
                echo "📹 $VIDEO_NAME"
                
                # 统计文件
                FILE_COUNT=$(ls -1 "$dir" 2>/dev/null | wc -l | xargs)
                echo "   文件数: $FILE_COUNT"
                
                # 列出文件
                ls -1 "$dir" 2>/dev/null | sed 's/^/   - /'
                echo ""
            fi
        done
    else
        echo "   (空)"
    fi
    
    exit 0
fi

VIDEO_NAME="$1"
OUTPUT_DIR="../output/$VIDEO_NAME"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ 输出目录不存在: $OUTPUT_DIR"
    echo ""
    echo "可用的视频:"
    ./show_output.sh --list
    exit 1
fi

echo "📁 输出目录: $OUTPUT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 显示所有文件
echo "📄 所有文件:"
ls -lh "$OUTPUT_DIR" | grep -v "^total" | grep -v "^d" | awk '{print "   ", $9, "-", $5}'
echo ""

# 如果有 cover_texts.json，显示内容
if [ -f "$OUTPUT_DIR/cover_texts.json" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 B站发布信息:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    cat "$OUTPUT_DIR/cover_texts.json" | python3 -m json.tool 2>/dev/null || cat "$OUTPUT_DIR/cover_texts.json"
    
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 打开目录查看:"
echo "   open $OUTPUT_DIR"
echo ""


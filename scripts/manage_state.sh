#!/bin/bash

# 处理状态管理脚本

STATE_FILE=".processing_state.json"

show_help() {
    echo "🔧 处理状态管理"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "用法: ./manage_state.sh [命令]"
    echo ""
    echo "命令:"
    echo "  list        查看已处理的视频"
    echo "  clean       清理失败的处理记录（files为空）"
    echo "  reset       重置所有状态（重新处理所有视频）"
    echo "  remove      移除特定视频的处理状态"
    echo "  help        显示此帮助"
    echo ""
    echo "示例:"
    echo "  ./manage_state.sh list"
    echo "  ./manage_state.sh reset"
    echo "  ./manage_state.sh remove \"video.mp4\""
}

list_processed() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "📊 还没有处理过任何视频"
        return
    fi
    
    python -c "
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)

print('📊 已处理的视频：')
print('━' * 70)
for video_name, info in state['processed_videos'].items():
    print(f'✓ {video_name}')
    print(f'  处理时间: {info[\"processed_at\"]}')
    print()
"
}

reset_all() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "✅ 状态文件不存在，无需重置"
        return
    fi
    
    echo "⚠️  将重置所有处理状态，所有视频将重新处理"
    echo ""
    read -p "确认重置？(yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        rm -f "$STATE_FILE"
        echo "✅ 状态已重置"
        echo ""
        echo "运行以下命令重新处理："
        echo "  ./auto_process.sh"
    else
        echo "❌ 已取消"
    fi
}

remove_video() {
    if [ -z "$1" ]; then
        echo "❌ 请指定视频名称"
        echo ""
        echo "用法: ./manage_state.sh remove \"video.mp4\""
        return 1
    fi
    
    VIDEO_NAME="$1"
    
    if [ ! -f "$STATE_FILE" ]; then
        echo "✅ 状态文件不存在"
        return
    fi
    
    python -c "
import json
from pathlib import Path

video_name = '$VIDEO_NAME'

if Path('$STATE_FILE').exists():
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    
    if video_name in state['processed_videos']:
        del state['processed_videos'][video_name]
        
        with open('$STATE_FILE', 'w') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        print(f'✅ 已移除: {video_name}')
        print()
        print('该视频将在下次运行时重新处理')
    else:
        print(f'❌ 未找到: {video_name}')
        print()
        print('已处理的视频列表:')
        for name in state['processed_videos'].keys():
            print(f'  - {name}')
"
}

clean_failed() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "✅ 状态文件不存在"
        return
    fi
    
    python -c "
import json
from pathlib import Path

if Path('$STATE_FILE').exists():
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    
    # 查找 files 为空的记录
    failed_videos = []
    for video_name, info in state['processed_videos'].items():
        if not info.get('files'):
            failed_videos.append(video_name)
    
    if failed_videos:
        print(f'🔍 发现 {len(failed_videos)} 个失败的处理记录：')
        print('━' * 70)
        for video in failed_videos:
            print(f'  ✗ {video}')
        print()
        
        # 清理
        for video in failed_videos:
            del state['processed_videos'][video]
        
        with open('$STATE_FILE', 'w') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        print(f'✅ 已清理 {len(failed_videos)} 个失败记录')
        print()
        print('这些视频将在下次运行时重新处理')
    else:
        print('✅ 没有失败的处理记录')
"
}

# 主逻辑
CMD="${1:-help}"

case $CMD in
    list)
        list_processed
        ;;
    clean)
        clean_failed
        ;;
    reset)
        reset_all
        ;;
    remove)
        remove_video "$2"
        ;;
    help|*)
        show_help
        ;;
esac


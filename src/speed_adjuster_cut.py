#!/usr/bin/env python3
"""
视频分段变速处理工具 - 裁剪模式
只保留配置的片段，删除未配置的部分
"""

import json
import subprocess
import os
import sys
from pathlib import Path
import re


def parse_timestamp(timestamp_str):
    """
    解析时间戳字符串为秒数
    支持格式: 
    - HH:MM:SS:FF 或 HH:MM:SS.FF (FF为帧数，假设25fps)
    - HH:MM:SS 或 MM:SS 或 SS
    """
    timestamp_str = timestamp_str.strip()
    
    # 处理帧数：可能是冒号或点号分隔的最后一部分
    # 先尝试用冒号分割
    parts = timestamp_str.split(':')
    
    if len(parts) >= 3:
        # 检查最后一部分是否包含小数点（可能是秒.帧数格式）
        last_part = parts[-1]
        if '.' in last_part:
            # 格式：HH:MM:SS.FF
            sec_frame = last_part.split('.')
            parts[-1] = sec_frame[0]  # 秒
            frames = float(sec_frame[1])  # 帧数
            fps = 25  # 默认帧率
        else:
            frames = 0
            fps = 25
        
        parts = [float(p) for p in parts]
        
        if len(parts) == 4:  # HH:MM:SS:FF
            return parts[0] * 3600 + parts[1] * 60 + parts[2] + parts[3] / fps
        elif len(parts) == 3:  # HH:MM:SS 或 HH:MM:SS.FF
            return parts[0] * 3600 + parts[1] * 60 + parts[2] + frames / fps
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1] + frames / fps
    else:
        # 简单格式
        if '.' in timestamp_str:
            # 包含小数的秒数
            return float(timestamp_str)
        else:
            parts = [float(p) for p in parts]
            if len(parts) == 2:  # MM:SS
                return parts[0] * 60 + parts[1]
            elif len(parts) == 1:  # SS
                return parts[0]
    
    raise ValueError(f"无法解析时间戳: {timestamp_str}")


def parse_timestamp_range(timestamp_range):
    """解析时间戳范围字符串"""
    match = re.match(r'(.+?)\s*-\s*(.+)', timestamp_range)
    if not match:
        raise ValueError(f"无法解析时间戳范围: {timestamp_range}")
    
    start_str, end_str = match.groups()
    return parse_timestamp(start_str), parse_timestamp(end_str)


def build_audio_filter(tempo):
    """构建音频速度调整滤镜"""
    if tempo == 1.0:
        return "anull"
    
    if 0.5 <= tempo <= 2.0:
        return f"atempo={tempo}"
    
    filters = []
    remaining = tempo
    
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    
    if remaining != 1.0:
        filters.append(f"atempo={remaining}")
    
    return ",".join(filters)


def process_video_segment(input_video, output_video, start_time, end_time, speed):
    """处理单个视频片段"""
    duration = end_time - start_time
    video_pts = 1.0 / speed
    audio_tempo = speed
    audio_filter = build_audio_filter(audio_tempo)
    
    cmd = [
        'ffmpeg',
        '-ss', str(start_time),  # 放在 -i 之前，精确定位
        '-i', input_video,
        '-t', str(duration),
        '-filter_complex',
        f'[0:v]setpts={video_pts}*PTS[v];[0:a]{audio_filter}[a]',
        '-map', '[v]',
        '-map', '[a]',
        '-y',
        output_video
    ]
    
    print(f"处理片段: {start_time:.2f}s - {end_time:.2f}s, 速度: {speed}x")
    subprocess.run(cmd, check=True)


def concat_videos(video_files, output_video):
    """拼接多个视频文件"""
    concat_file = "/tmp/concat_list_cut.txt"
    with open(concat_file, 'w') as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")
    
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',
        '-y',
        output_video
    ]
    
    print(f"拼接 {len(video_files)} 个视频片段...")
    subprocess.run(cmd, check=True)
    
    os.remove(concat_file)


def process_video_cut_mode(input_video, config, output_video):
    """
    裁剪模式：只保留配置的片段
    
    Args:
        input_video: 输入视频路径
        config: 速度配置（JSON 对象或文件路径）
        output_video: 输出视频路径
    """
    # 解析配置
    if isinstance(config, str):
        if os.path.isfile(config):
            with open(config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            config_data = json.loads(config)
    else:
        config_data = config
    
    parts = config_data.get('part', [])
    if not parts:
        print("错误: 配置中没有找到 'part' 数组")
        return False
    
    # 解析所有时间段
    segments = []
    for i, part in enumerate(parts):
        timestamp = part.get('timestamp', '')
        speed = part.get('speed', 1.0)
        
        start_time, end_time = parse_timestamp_range(timestamp)
        segments.append({
            'index': i,
            'start': start_time,
            'end': end_time,
            'speed': speed
        })
    
    # 排序片段
    segments.sort(key=lambda x: x['start'])
    
    print(f"\n⚠️  裁剪模式：只保留 {len(segments)} 个配置的片段")
    print(f"未配置的部分将被删除！\n")
    
    # 创建临时目录
    temp_dir = Path("/tmp/video_speed_segments_cut")
    temp_dir.mkdir(exist_ok=True)
    
    # 只处理配置的片段
    segment_files = []
    try:
        for i, seg in enumerate(segments):
            temp_output = temp_dir / f"segment_{i:03d}.mp4"
            
            print(f"\n处理片段 {i+1}/{len(segments)}")
            
            process_video_segment(
                input_video,
                str(temp_output),
                seg['start'],
                seg['end'],
                seg['speed']
            )
            
            segment_files.append(str(temp_output))
        
        # 拼接所有片段
        print(f"\n开始拼接视频...")
        concat_videos(segment_files, output_video)
        
        print(f"\n✅ 处理完成！输出文件: {output_video}")
        return True
        
    finally:
        # 清理临时文件
        print("\n清理临时文件...")
        for segment_file in segment_files:
            if os.path.exists(segment_file):
                os.remove(segment_file)


def main():
    """命令行入口"""
    if len(sys.argv) < 4:
        print("视频分段变速工具 - 裁剪模式")
        print("=" * 50)
        print("只保留配置的片段，删除未配置的部分\n")
        print("用法: python speed_adjuster_cut.py <输入视频> <配置JSON> <输出视频>")
        print("\n示例:")
        print('  python speed_adjuster_cut.py input.mp4 config.json output.mp4')
        sys.exit(1)
    
    input_video = sys.argv[1]
    config = sys.argv[2]
    output_video = sys.argv[3]
    
    if not os.path.exists(input_video):
        print(f"错误: 输入视频不存在: {input_video}")
        sys.exit(1)
    
    try:
        success = process_video_cut_mode(input_video, config, output_video)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


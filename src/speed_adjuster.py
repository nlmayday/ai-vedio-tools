#!/usr/bin/env python3
"""
视频分段变速处理工具
根据 JSON 配置对视频的不同片段应用不同的播放速度
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
    """
    解析时间戳范围字符串
    格式: "00:00:50 - 00:01:00"
    返回: (start_seconds, end_seconds)
    """
    match = re.match(r'(.+?)\s*-\s*(.+)', timestamp_range)
    if not match:
        raise ValueError(f"无法解析时间戳范围: {timestamp_range}")
    
    start_str, end_str = match.groups()
    return parse_timestamp(start_str), parse_timestamp(end_str)


def get_video_duration(video_path):
    """获取视频时长（秒）"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def cut_video_segment(input_video, output_video, start_time, end_time):
    """
    第一步：从原视频切出片段（不变速，保持原速）
    """
    duration = end_time - start_time
    
    cmd = [
        'ffmpeg',
        '-ss', str(start_time),  # 精确定位
        '-i', input_video,
        '-t', str(duration),
        '-c', 'copy',  # 直接复制，不重新编码
        '-y',
        output_video
    ]
    
    print(f"  切片段: {start_time:.2f}s - {end_time:.2f}s (时长: {duration:.2f}s)")
    subprocess.run(cmd, check=True)


def apply_speed_to_segment(input_video, output_video, speed):
    """
    第二步：对已切好的片段应用变速
    """
    if speed == 1.0:
        # 速度为1.0，直接复制
        import shutil
        shutil.copy2(input_video, output_video)
        print(f"  速度: 1.0x (不变速，直接复制)")
        return
    
    video_pts = 1.0 / speed
    audio_tempo = speed
    audio_filter = build_audio_filter(audio_tempo)
    
    cmd = [
        'ffmpeg',
        '-i', input_video,
        '-filter_complex',
        f'[0:v]setpts={video_pts}*PTS[v];[0:a]{audio_filter}[a]',
        '-map', '[v]',
        '-map', '[a]',
        '-y',
        output_video
    ]
    
    print(f"  应用变速: {speed}x")
    subprocess.run(cmd, check=True)


def build_audio_filter(tempo):
    """
    构建音频速度调整滤镜
    atempo 只支持 0.5-2.0 的范围，需要链式调用来实现更大的速度变化
    """
    if tempo == 1.0:
        return "anull"
    
    # 如果速度在 0.5-2.0 范围内，直接使用 atempo
    if 0.5 <= tempo <= 2.0:
        return f"atempo={tempo}"
    
    # 如果速度超出范围，需要链式调用
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


def concat_videos(video_files, output_video):
    """
    拼接多个视频文件
    
    Args:
        video_files: 视频文件路径列表
        output_video: 输出视频路径
    """
    # 创建临时文件列表
    concat_file = "/tmp/concat_list.txt"
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
    
    # 清理临时文件
    os.remove(concat_file)


def process_video_with_speed_config(input_video, config, output_video):
    """
    根据配置处理视频
    
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
    
    # 获取视频总时长
    total_duration = get_video_duration(input_video)
    print(f"视频总时长: {total_duration:.2f}秒")
    
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
    
    # 排序片段（按开始时间）
    segments.sort(key=lambda x: x['start'])
    
    # 检查是否需要添加未处理的片段
    all_segments = []
    current_time = 0.0
    
    for seg in segments:
        # 如果有间隙，添加正常速度的片段
        if seg['start'] > current_time:
            all_segments.append({
                'start': current_time,
                'end': seg['start'],
                'speed': 1.0,
                'is_filler': True
            })
        
        # 添加当前片段
        all_segments.append({
            'start': seg['start'],
            'end': seg['end'],
            'speed': seg['speed'],
            'is_filler': False
        })
        
        current_time = seg['end']
    
    # 如果最后还有剩余部分，添加正常速度片段
    if current_time < total_duration:
        all_segments.append({
            'start': current_time,
            'end': total_duration,
            'speed': 1.0,
            'is_filler': True
        })
    
    # 创建临时目录
    temp_dir = Path("/tmp/video_speed_segments")
    temp_dir.mkdir(exist_ok=True)
    
    # 三步处理：先切 → 再变速 → 最后拼接
    cut_files = []
    speed_files = []
    
    try:
        # 第一步：切出所有片段（保持原速）
        print(f"\n{'='*60}")
        print("第一步：从原视频切出所有片段（原速）")
        print(f"{'='*60}")
        
        for i, seg in enumerate(all_segments):
            cut_file = temp_dir / f"cut_{i:03d}.mp4"
            
            filler_note = " (填充)" if seg.get('is_filler', False) else ""
            print(f"\n[{i+1}/{len(all_segments)}] 切片段{filler_note}")
            
            cut_video_segment(
                input_video,
                str(cut_file),
                seg['start'],
                seg['end']
            )
            
            cut_files.append(str(cut_file))
        
        # 第二步：对每个片段应用变速
        print(f"\n{'='*60}")
        print("第二步：对每个片段应用变速")
        print(f"{'='*60}")
        
        for i, (cut_file, seg) in enumerate(zip(cut_files, all_segments)):
            speed_file = temp_dir / f"speed_{i:03d}.mp4"
            
            filler_note = " (填充)" if seg.get('is_filler', False) else ""
            print(f"\n[{i+1}/{len(all_segments)}] 变速处理{filler_note}")
            
            apply_speed_to_segment(
                cut_file,
                str(speed_file),
                seg['speed']
            )
            
            speed_files.append(str(speed_file))
        
        # 第三步：拼接所有变速后的片段
        print(f"\n{'='*60}")
        print("第三步：拼接所有变速后的片段")
        print(f"{'='*60}")
        concat_videos(speed_files, output_video)
        
        print(f"\n✅ 处理完成！输出文件: {output_video}")
        return True
        
    finally:
        # 清理临时文件
        print("\n清理临时文件...")
        for temp_file in cut_files + speed_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


def main():
    """命令行入口"""
    if len(sys.argv) < 4:
        print("用法: python speed_adjuster.py <输入视频> <配置JSON> <输出视频>")
        print("\n示例:")
        print('  python speed_adjuster.py input.mp4 config.json output.mp4')
        print('  python speed_adjuster.py input.mp4 \'{"part":[...]}\' output.mp4')
        sys.exit(1)
    
    input_video = sys.argv[1]
    config = sys.argv[2]
    output_video = sys.argv[3]
    
    if not os.path.exists(input_video):
        print(f"错误: 输入视频不存在: {input_video}")
        sys.exit(1)
    
    try:
        success = process_video_with_speed_config(input_video, config, output_video)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


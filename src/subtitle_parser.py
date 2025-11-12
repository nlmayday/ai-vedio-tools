#!/usr/bin/env python3
"""
字幕解析器 - 支持 VTT 和 SRT 格式
"""

import re
from typing import List, Dict, Tuple


def detect_format(file_path: str) -> str:
    """
    检测字幕文件格式
    
    Returns:
        'vtt' 或 'srt'
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
    
    if first_line.startswith('WEBVTT'):
        return 'vtt'
    elif first_line.isdigit():
        return 'srt'
    else:
        # 默认按扩展名判断
        if file_path.lower().endswith('.vtt'):
            return 'vtt'
        elif file_path.lower().endswith('.srt'):
            return 'srt'
        else:
            raise ValueError(f"无法识别字幕格式: {file_path}")


def parse_vtt(file_path: str) -> List[Dict]:
    """解析 VTT 字幕"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            i += 1
            continue
        
        if '-->' in line:
            timestamp = line
            match = re.match(r'(\d+:\d+:\d+\.\d+)\s*-->\s*(\d+:\d+:\d+\.\d+)', timestamp)
            if match:
                start_time = match.group(1)
                end_time = match.group(2)
            else:
                i += 1
                continue
            
            text_lines = []
            i += 1
            
            while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                text_line = lines[i].strip()
                text_line = re.sub(r'&nbsp;', ' ', text_line)
                text_line = re.sub(r'<[^>]+>', '', text_line)
                if text_line:
                    text_lines.append(text_line)
                i += 1
            
            if text_lines:
                blocks.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': ' '.join(text_lines)
                })
        else:
            i += 1
    
    return blocks


def parse_srt(file_path: str) -> List[Dict]:
    """解析 SRT 字幕"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行
        if not line:
            i += 1
            continue
        
        # 序号行（纯数字）
        if line.isdigit():
            i += 1
            
            # 时间戳行
            if i < len(lines) and '-->' in lines[i]:
                timestamp = lines[i].strip()
                match = re.match(r'(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)', timestamp)
                if match:
                    start_time = match.group(1).replace(',', '.')  # 转换为统一格式
                    end_time = match.group(2).replace(',', '.')
                else:
                    i += 1
                    continue
                
                # 文本行
                text_lines = []
                i += 1
                
                while i < len(lines) and lines[i].strip():
                    text_line = lines[i].strip()
                    if text_line:
                        text_lines.append(text_line)
                    i += 1
                
                if text_lines:
                    blocks.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': ' '.join(text_lines)
                    })
        else:
            i += 1
    
    return blocks


def write_vtt(blocks: List[Dict], output_path: str):
    """写入 VTT 格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('WEBVTT\n')
        f.write('Kind: captions\n')
        f.write('Language: zh\n\n')
        
        for block in blocks:
            f.write(f"{block['start_time']} --> {block['end_time']}\n")
            f.write(f"{block['text']}\n\n")


def write_srt(blocks: List[Dict], output_path: str):
    """写入 SRT 格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, block in enumerate(blocks, 1):
            # 序号
            f.write(f"{i}\n")
            
            # 时间戳（SRT 用逗号分隔毫秒）
            start_time = block['start_time'].replace('.', ',')
            end_time = block['end_time'].replace('.', ',')
            f.write(f"{start_time} --> {end_time}\n")
            
            # 文本
            f.write(f"{block['text']}\n\n")


def parse_subtitle(file_path: str) -> Tuple[str, List[Dict]]:
    """
    自动检测并解析字幕文件
    
    Returns:
        (format, blocks)
        format: 'vtt' 或 'srt'
        blocks: 字幕块列表
    """
    format_type = detect_format(file_path)
    
    if format_type == 'vtt':
        blocks = parse_vtt(file_path)
    else:
        blocks = parse_srt(file_path)
    
    return format_type, blocks


def write_subtitle(blocks: List[Dict], output_path: str, format_type: str):
    """
    根据格式写入字幕文件
    
    Args:
        blocks: 字幕块列表
        output_path: 输出路径
        format_type: 'vtt' 或 'srt'
    """
    if format_type == 'vtt':
        write_vtt(blocks, output_path)
    else:
        write_srt(blocks, output_path)


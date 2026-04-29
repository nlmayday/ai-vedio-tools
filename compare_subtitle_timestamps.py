#!/usr/bin/env python3
"""
对比中英双语字幕和英文字幕的时间戳，检查是否存在时间不匹配
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def parse_time_to_seconds(time_str: str) -> float:
    """将时间戳转换为秒数"""
    # 处理逗号或点作为毫秒分隔符
    time_str = time_str.replace(',', '.')
    
    # 匹配格式：HH:MM:SS.mmm 或 MM:SS.mmm 或 SS.mmm
    parts = time_str.split(':')
    
    if len(parts) == 3:  # HH:MM:SS.mmm
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    elif len(parts) == 2:  # MM:SS.mmm
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    else:  # SS.mmm
        return float(parts[0])

def parse_srt(file_path: str) -> List[Dict]:
    """解析 SRT 字幕文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        if line.isdigit():
            i += 1
            
            if i < len(lines) and '-->' in lines[i]:
                timestamp = lines[i].strip()
                match = re.match(r'(\d+:\d+:\d+[,.]\d+)\s*-->\s*(\d+:\d+:\d+[,.]\d+)', timestamp)
                if match:
                    start_time_str = match.group(1)
                    end_time_str = match.group(2)
                    start_seconds = parse_time_to_seconds(start_time_str)
                    end_seconds = parse_time_to_seconds(end_time_str)
                    
                    text_lines = []
                    i += 1
                    
                    while i < len(lines) and lines[i].strip():
                        text_line = lines[i].strip()
                        if text_line:
                            text_lines.append(text_line)
                        i += 1
                    
                    if text_lines:
                        blocks.append({
                            'start': start_seconds,
                            'end': end_seconds,
                            'start_str': start_time_str,
                            'end_str': end_time_str,
                            'text': ' '.join(text_lines)
                        })
        else:
            i += 1
    
    return blocks

def parse_vtt(file_path: str) -> List[Dict]:
    """解析 VTT 字幕文件"""
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
                start_time_str = match.group(1)
                end_time_str = match.group(2)
                start_seconds = parse_time_to_seconds(start_time_str)
                end_seconds = parse_time_to_seconds(end_time_str)
                
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
                        'start': start_seconds,
                        'end': end_seconds,
                        'start_str': start_time_str,
                        'end_str': end_time_str,
                        'text': ' '.join(text_lines)
                    })
        else:
            i += 1
    
    return blocks

def compare_subtitles(bilingual_path: str, english_path: str):
    """对比两个字幕文件的时间戳"""
    print("=" * 80)
    print("📊 字幕时间戳对比分析")
    print("=" * 80)
    print()
    
    print(f"📄 中英双语字幕: {bilingual_path}")
    bilingual_blocks = parse_srt(bilingual_path)
    print(f"   共 {len(bilingual_blocks)} 个字幕块")
    print()
    
    print(f"📄 英文字幕: {english_path}")
    english_blocks = parse_vtt(english_path)
    print(f"   共 {len(english_blocks)} 个字幕块")
    print()
    
    print("=" * 80)
    print("🔍 时间戳对比（前30个条目）")
    print("=" * 80)
    print()
    
    # 提取英文字幕中的英文文本（用于匹配）
    max_compare = min(30, len(bilingual_blocks), len(english_blocks))
    
    differences = []
    matches = 0
    
    for i in range(max_compare):
        bi_block = bilingual_blocks[i]
        # 从双语字幕中提取英文部分（通常是第二行）
        bi_text_lines = bi_block['text'].split('\n')
        bi_english_text = bi_text_lines[-1] if len(bi_text_lines) > 1 else bi_text_lines[0]
        bi_english_text = bi_english_text.strip()
        
        # 查找匹配的英文字幕块（通过时间戳）
        best_match = None
        best_diff = float('inf')
        
        for en_block in english_blocks[:i+10]:  # 在当前索引附近查找
            # 计算开始时间的差异
            start_diff = abs(bi_block['start'] - en_block['start'])
            
            if start_diff < best_diff and start_diff < 0.1:  # 差异小于0.1秒
                best_diff = start_diff
                best_match = en_block
        
        if best_match:
            start_diff = bi_block['start'] - best_match['start']
            end_diff = bi_block['end'] - best_match['end']
            
            status = "✅" if abs(start_diff) < 0.01 and abs(end_diff) < 0.01 else "⚠️ "
            
            if abs(start_diff) >= 0.01 or abs(end_diff) >= 0.01:
                differences.append({
                    'index': i + 1,
                    'bilingual_start': bi_block['start_str'],
                    'english_start': best_match['start_str'],
                    'start_diff': start_diff,
                    'bilingual_end': bi_block['end_str'],
                    'english_end': best_match['end_str'],
                    'end_diff': end_diff
                })
            else:
                matches += 1
            
            print(f"{status} 第 {i+1:3d} 条:")
            print(f"   双语字幕: {bi_block['start_str']} --> {bi_block['end_str']}")
            print(f"   英文字幕: {best_match['start_str']} --> {best_match['end_str']}")
            if abs(start_diff) >= 0.01 or abs(end_diff) >= 0.01:
                print(f"   ⚠️  开始时间差异: {start_diff:+.3f} 秒")
                print(f"   ⚠️  结束时间差异: {end_diff:+.3f} 秒")
            print(f"   英文文本: {bi_english_text[:60]}...")
            print()
        else:
            print(f"❌ 第 {i+1:3d} 条: 未找到匹配的英文字幕块")
            print(f"   双语字幕: {bi_block['start_str']} --> {bi_block['end_str']}")
            print()
    
    print("=" * 80)
    print("📈 统计结果")
    print("=" * 80)
    print()
    
    total_compared = max_compare
    print(f"总对比条目数: {total_compared}")
    print(f"✅ 时间戳匹配: {matches} ({matches/total_compared*100:.1f}%)")
    print(f"⚠️  时间戳差异: {len(differences)} ({len(differences)/total_compared*100:.1f}%)")
    print()
    
    if differences:
        print("=" * 80)
        print("⚠️  发现时间戳差异的条目")
        print("=" * 80)
        print()
        
        for diff in differences[:10]:  # 只显示前10个差异
            print(f"条目 {diff['index']}:")
            print(f"  双语开始: {diff['bilingual_start']}")
            print(f"  英文开始: {diff['english_start']}")
            print(f"  开始差异: {diff['start_diff']:+.3f} 秒")
            print(f"  双语结束: {diff['bilingual_end']}")
            print(f"  英文结束: {diff['english_end']}")
            print(f"  结束差异: {diff['end_diff']:+.3f} 秒")
            print()
        
        if len(differences) > 10:
            print(f"... 还有 {len(differences) - 10} 个差异条目未显示")
            print()
        
        # 计算平均差异
        avg_start_diff = sum(d['start_diff'] for d in differences) / len(differences)
        avg_end_diff = sum(d['end_diff'] for d in differences) / len(differences)
        max_start_diff = max(abs(d['start_diff']) for d in differences)
        max_end_diff = max(abs(d['end_diff']) for d in differences)
        
        print("差异统计:")
        print(f"  平均开始时间差异: {avg_start_diff:+.3f} 秒")
        print(f"  平均结束时间差异: {avg_end_diff:+.3f} 秒")
        print(f"  最大开始时间差异: {max_start_diff:.3f} 秒")
        print(f"  最大结束时间差异: {max_end_diff:.3f} 秒")
        print()
    else:
        print("✅ 所有对比的时间戳都匹配！")
        print()

def main():
    if len(sys.argv) != 3:
        print("用法: python compare_subtitle_timestamps.py <双语字幕文件> <英文字幕文件>")
        print()
        print("示例:")
        print("  python compare_subtitle_timestamps.py output/video/video_bilingual.srt data/video.en.vtt")
        sys.exit(1)
    
    bilingual_path = sys.argv[1]
    english_path = sys.argv[2]
    
    if not Path(bilingual_path).exists():
        print(f"❌ 文件不存在: {bilingual_path}")
        sys.exit(1)
    
    if not Path(english_path).exists():
        print(f"❌ 文件不存在: {english_path}")
        sys.exit(1)
    
    compare_subtitles(bilingual_path, english_path)

if __name__ == '__main__':
    main()












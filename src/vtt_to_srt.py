#!/usr/bin/env python3
"""
字幕格式转换工具
支持 VTT ↔ SRT 互转
"""

import re
import argparse
import logging
from pathlib import Path
from subtitle_parser import parse_subtitle, write_subtitle, detect_format

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 使用 subtitle_parser 模块处理，这里只保留 main 函数


def main():
    parser = argparse.ArgumentParser(
        description='🎬 字幕格式转换工具（VTT ↔ SRT）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # VTT 转 SRT
  python vtt_to_srt.py --input video.zh.vtt --output video.zh.srt
  
  # SRT 转 VTT
  python vtt_to_srt.py --input video.zh.srt --output video.zh.vtt
  
  # 自动检测并转换（扩展名决定输出格式）
  python vtt_to_srt.py --input video.zh.vtt

💡 B站上传说明:
  1. 上传视频
  2. 视频管理 → 字幕设置
  3. 分别上传中文和英文 SRT 文件
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入字幕文件（VTT 或 SRT）'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出字幕文件（默认自动转换格式）'
    )
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not Path(args.input).exists():
        print(f"❌ 文件不存在: {args.input}")
        return 1
    
    try:
        # 检测输入格式
        input_format = detect_format(args.input)
        logger.info(f"📋 检测到输入格式: {input_format.upper()}")
        
        # 解析字幕
        _, blocks = parse_subtitle(args.input)
        logger.info(f"✅ 解析完成，共 {len(blocks)} 条字幕")
        
        # 决定输出格式
        if args.output:
            output_path = args.output
            # 根据扩展名决定输出格式
            if output_path.endswith('.vtt'):
                output_format = 'vtt'
            elif output_path.endswith('.srt'):
                output_format = 'srt'
            else:
                # 默认转换为另一种格式
                output_format = 'srt' if input_format == 'vtt' else 'vtt'
        else:
            # 默认输出路径：转换为另一种格式
            output_format = 'srt' if input_format == 'vtt' else 'vtt'
            output_path = str(Path(args.input).with_suffix(f'.{output_format}'))
        
        logger.info(f"📝 输出格式: {output_format.upper()}")
        
        # 写入字幕
        write_subtitle(blocks, output_path, output_format)
        
        logger.info("")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"✨ 转换完成！ {input_format.upper()} → {output_format.upper()}")
        logger.info(f"📁 输出: {output_path}")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 转换失败: {e}")
        return 1


if __name__ == '__main__':
    exit(main())


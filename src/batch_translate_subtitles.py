#!/usr/bin/env python3
"""
批量翻译 VTT 字幕文件
自动查找并翻译指定目录下的所有英文字幕
"""

import os
import sys
from pathlib import Path
import argparse
import logging

# 导入翻译器
from subtitle_translator import VTTTranslator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_vtt_files(directory: str, pattern: str = '*.en.vtt') -> list:
    """
    查找目录下的 VTT 文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式
        
    Returns:
        VTT 文件路径列表
    """
    directory = Path(directory)
    vtt_files = list(directory.glob(pattern))
    vtt_files.extend(directory.glob('**/' + pattern))  # 递归查找
    return [str(f) for f in vtt_files]


def batch_translate(
    input_dir: str,
    output_dir: str = None,
    api_key: str = None,
    batch_size: int = 20,
    pattern: str = '*.en.vtt'
):
    """
    批量翻译字幕文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录（可选）
        api_key: API Key
        batch_size: 批量翻译大小
        pattern: 文件匹配模式
    """
    print("\n" + "="*60)
    print("🌐 批量字幕翻译器")
    print("="*60)
    
    # 查找字幕文件
    vtt_files = find_vtt_files(input_dir, pattern)
    
    if not vtt_files:
        print(f"❌ 未找到匹配的字幕文件: {pattern}")
        return
    
    print(f"\n📁 输入目录: {input_dir}")
    print(f"📊 找到 {len(vtt_files)} 个字幕文件:\n")
    
    for i, vtt_file in enumerate(vtt_files, 1):
        print(f"  {i}. {Path(vtt_file).name}")
    
    print("\n" + "="*60)
    
    # 创建翻译器
    try:
        translator = VTTTranslator(api_key=api_key)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 翻译每个文件
    success_count = 0
    fail_count = 0
    
    for i, vtt_file in enumerate(vtt_files, 1):
        print(f"\n{'='*60}")
        print(f"📝 处理文件 {i}/{len(vtt_files)}")
        print(f"{'='*60}")
        
        try:
            # 确定输出路径
            if output_dir:
                output_file = Path(output_dir) / Path(vtt_file).name.replace('.en.vtt', '.zh.vtt')
            else:
                output_file = Path(vtt_file).parent / Path(vtt_file).name.replace('.en.vtt', '.zh.vtt')
            
            # 翻译
            result = translator.translate_vtt(
                input_path=vtt_file,
                output_path=str(output_file),
                batch_size=batch_size
            )
            
            if result:
                success_count += 1
            else:
                fail_count += 1
                
        except Exception as e:
            logger.error(f"❌ 处理文件失败: {vtt_file}")
            logger.error(f"   错误: {e}")
            fail_count += 1
    
    # 总结
    print("\n" + "="*60)
    print("✨ 批量翻译完成！")
    print("="*60)
    print(f"📊 统计:")
    print(f"   总文件数: {len(vtt_files)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {fail_count}")
    print("="*60 + "\n")


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🌐 批量 VTT 字幕翻译器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 翻译 data 目录下所有英文字幕
  export DEEPSEEK_API_KEY="your_api_key"
  python batch_translate_subtitles.py --input-dir ../data

  # 2. 指定输出目录
  python batch_translate_subtitles.py \\
    --input-dir ../data \\
    --output-dir ../data/translated

  # 3. 指定文件模式
  python batch_translate_subtitles.py \\
    --input-dir ../data \\
    --pattern "*.en.vtt"

💡 提示:
  - 自动查找指定目录下的所有 .en.vtt 文件
  - 翻译后的文件自动命名为 .zh.vtt
  - 支持递归查找子目录
        """
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        required=True,
        help='输入目录路径'
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='输出目录路径（默认与输入文件同目录）'
    )
    parser.add_argument(
        '--api-key',
        help='DeepSeek API Key（也可通过环境变量设置）'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=20,
        help='批量翻译大小（默认: 20）'
    )
    parser.add_argument(
        '--pattern', '-p',
        default='*.en.vtt',
        help='文件匹配模式（默认: *.en.vtt）'
    )
    
    args = parser.parse_args()
    
    try:
        batch_translate(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            api_key=args.api_key,
            batch_size=args.batch_size,
            pattern=args.pattern
        )
        return 0
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return 1


if __name__ == '__main__':
    exit(main())


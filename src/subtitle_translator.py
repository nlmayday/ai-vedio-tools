#!/usr/bin/env python3
"""
VTT 字幕翻译器
使用 DeepSeek API 将 VTT 字幕翻译成中文
"""

import os
import re
import json
import argparse
from pathlib import Path
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VTTTranslator:
    """VTT 字幕翻译器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化翻译器
        
        Args:
            api_key: DeepSeek API Key
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if not self.api_key:
            raise ValueError("请提供 DeepSeek API Key 或设置环境变量 DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def parse_vtt(self, vtt_path: str) -> list:
        """
        解析 VTT 字幕文件
        
        Args:
            vtt_path: VTT 文件路径
            
        Returns:
            字幕块列表，每个块包含 {timestamp, text}
        """
        logger.info(f"📖 读取字幕文件: {vtt_path}")
        
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割字幕块
        blocks = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行和头部信息
            if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                i += 1
                continue
            
            # 检查是否是时间戳行
            if '-->' in line:
                timestamp = line
                text_lines = []
                i += 1
                
                # 收集该时间戳下的所有文本
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text_line = lines[i].strip()
                    # 移除 HTML 标签和特殊字符
                    text_line = re.sub(r'&nbsp;', ' ', text_line)
                    text_line = re.sub(r'<[^>]+>', '', text_line)
                    if text_line:
                        text_lines.append(text_line)
                    i += 1
                
                if text_lines:
                    blocks.append({
                        'timestamp': timestamp,
                        'text': ' '.join(text_lines)
                    })
            else:
                i += 1
        
        logger.info(f"✅ 解析完成，共 {len(blocks)} 个字幕块")
        return blocks
    
    def translate_batch(self, texts: list, batch_size: int = 20) -> list:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译的文本列表
            batch_size: 每批翻译的数量
            
        Returns:
            翻译后的文本列表
        """
        translations = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"🤖 翻译批次 {batch_num}/{total_batches} ({len(batch)} 条字幕)...")
            
            # 构建翻译提示
            text_dict = {str(idx): text for idx, text in enumerate(batch)}
            
            prompt = f"""请将以下英文字幕翻译成中文。要求：
1. 保持原意，译文自然流畅
2. 适合字幕显示，简洁易读
3. 专业术语准确翻译
4. 返回 JSON 格式，key 是序号，value 是翻译后的文本

原文：
{json.dumps(text_dict, ensure_ascii=False, indent=2)}

请直接返回 JSON，不要有其他内容。"""

            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是专业的字幕翻译专家。请将英文字幕准确、自然地翻译成中文。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content.strip()
                
                # 提取 JSON
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                translated_dict = json.loads(content)
                
                # 按顺序提取翻译结果
                for idx in range(len(batch)):
                    translations.append(translated_dict.get(str(idx), batch[idx]))
                
                # 显示进度
                progress_percent = (batch_num * 100) // total_batches
                bar_length = 40
                filled = int(bar_length * progress_percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                logger.info(f"   ✅ 批次完成")
                logger.info(f"   📊 进度: [{bar}] {progress_percent}% ({batch_num}/{total_batches})")
                
            except Exception as e:
                logger.error(f"   ❌ 批次 {batch_num} 翻译失败: {e}")
                # 失败时保留原文
                translations.extend(batch)
        
        return translations
    
    def generate_vtt(
        self,
        blocks: list,
        output_path: str,
        language: str = 'zh'
    ):
        """
        生成 VTT 字幕文件
        
        Args:
            blocks: 字幕块列表
            output_path: 输出文件路径
            language: 语言代码
        """
        logger.info(f"💾 生成 VTT 文件: {output_path}")
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入头部
            f.write('WEBVTT\n')
            f.write('Kind: captions\n')
            f.write(f'Language: {language}\n\n')
            
            # 写入字幕块
            for block in blocks:
                f.write(f"{block['timestamp']}\n")
                f.write(f"{block['text']}\n\n")
        
        logger.info(f"✅ VTT 文件已生成")
    
    def translate_vtt(
        self,
        input_path: str,
        output_path: str = None,
        batch_size: int = 20
    ) -> str:
        """
        翻译 VTT 字幕文件
        
        Args:
            input_path: 输入 VTT 文件路径
            output_path: 输出 VTT 文件路径（可选）
            batch_size: 批量翻译大小
            
        Returns:
            输出文件路径
        """
        # 默认输出路径
        if not output_path:
            input_file = Path(input_path)
            # 将 .en.vtt 替换为 .zh.vtt
            if '.en.vtt' in input_file.name:
                output_name = input_file.name.replace('.en.vtt', '.zh_translated.vtt')
            else:
                output_name = input_file.stem + '_zh.vtt'
            output_path = input_file.parent / output_name
        
        logger.info("="*60)
        logger.info("🌐 VTT 字幕翻译器")
        logger.info("="*60)
        logger.info(f"📁 输入: {input_path}")
        logger.info(f"📁 输出: {output_path}")
        logger.info("")
        
        # 1. 解析 VTT
        blocks = self.parse_vtt(input_path)
        
        if not blocks:
            logger.error("❌ 未找到字幕内容")
            return None
        
        # 2. 提取文本
        texts = [block['text'] for block in blocks]
        
        # 3. 批量翻译
        logger.info("")
        logger.info(f"🚀 开始翻译 {len(texts)} 条字幕...")
        logger.info("")
        
        translated_texts = self.translate_batch(texts, batch_size)
        
        # 4. 更新字幕块
        for i, block in enumerate(blocks):
            block['text'] = translated_texts[i]
        
        # 5. 生成 VTT 文件
        logger.info("")
        self.generate_vtt(blocks, output_path, language='zh')
        
        logger.info("")
        logger.info("="*60)
        logger.info("✨ 翻译完成！")
        logger.info("="*60)
        logger.info(f"📊 统计:")
        logger.info(f"   字幕数量: {len(blocks)}")
        logger.info(f"   输出文件: {output_path}")
        logger.info("="*60)
        logger.info("")
        
        return str(output_path)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🌐 VTT 字幕翻译器 - 使用 DeepSeek AI 翻译字幕',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 翻译单个字幕文件
  export DEEPSEEK_API_KEY="your_api_key"
  python subtitle_translator.py --input subtitle.en.vtt

  # 2. 指定输出文件
  python subtitle_translator.py \\
    --input subtitle.en.vtt \\
    --output subtitle.zh.vtt

  # 3. 指定 API Key
  python subtitle_translator.py \\
    --input subtitle.en.vtt \\
    --api-key "your_key"

  # 4. 调整批量翻译大小
  python subtitle_translator.py \\
    --input subtitle.en.vtt \\
    --batch-size 30

💡 提示:
  - 批量翻译可以降低 API 调用次数和成本
  - 建议 batch-size 设置为 15-30
  - 自动保留原有的时间戳格式
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入 VTT 字幕文件路径'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出 VTT 字幕文件路径（默认自动生成）'
    )
    parser.add_argument(
        '--api-key',
        help='DeepSeek API Key（也可通过环境变量 DEEPSEEK_API_KEY 设置）'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=20,
        help='批量翻译大小（默认: 20）'
    )
    
    args = parser.parse_args()
    
    try:
        # 检查输入文件
        if not os.path.exists(args.input):
            print(f"❌ 错误：输入文件不存在: {args.input}")
            return 1
        
        # 创建翻译器
        translator = VTTTranslator(api_key=args.api_key)
        
        # 翻译字幕
        output_file = translator.translate_vtt(
            input_path=args.input,
            output_path=args.output,
            batch_size=args.batch_size
        )
        
        if output_file:
            return 0
        else:
            return 1
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.exception("详细错误信息:")
        return 1


if __name__ == '__main__':
    exit(main())


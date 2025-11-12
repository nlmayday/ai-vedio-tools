#!/usr/bin/env python3
"""
智能字幕翻译器（支持断点续传）
大文件分段翻译，自动保存进度，支持中断后继续
"""

import os
import re
import json
import argparse
from pathlib import Path
from openai import OpenAI
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SmartVTTTranslator:
    """支持断点续传的智能字幕翻译器"""
    
    def __init__(self, api_key: str = None):
        """初始化翻译器"""
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if not self.api_key:
            raise ValueError("请提供 DeepSeek API Key 或设置环境变量 DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def parse_vtt(self, vtt_path: str) -> list:
        """解析 VTT 字幕文件"""
        logger.info(f"📖 读取字幕文件: {vtt_path}")
        
        with open(vtt_path, 'r', encoding='utf-8') as f:
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
                        'timestamp': timestamp,
                        'text': ' '.join(text_lines),
                        'translated': None  # 翻译结果
                    })
            else:
                i += 1
        
        logger.info(f"✅ 解析完成，共 {len(blocks)} 个字幕块")
        return blocks
    
    def save_progress(self, progress_file: str, blocks: list, current_batch: int):
        """
        保存翻译进度
        
        Args:
            progress_file: 进度文件路径
            blocks: 字幕块列表
            current_batch: 当前批次
        """
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'current_batch': current_batch,
            'total_blocks': len(blocks),
            'blocks': blocks
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 进度已保存: {progress_file}")
    
    def load_progress(self, progress_file: str) -> tuple:
        """
        加载翻译进度
        
        Args:
            progress_file: 进度文件路径
            
        Returns:
            (blocks, current_batch) 或 (None, 0)
        """
        if not os.path.exists(progress_file):
            return None, 0
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            blocks = progress_data['blocks']
            current_batch = progress_data['current_batch']
            
            logger.info(f"📂 找到进度文件，上次翻译到批次 {current_batch}")
            logger.info(f"   时间: {progress_data['timestamp']}")
            
            # 统计已翻译数量
            translated_count = sum(1 for b in blocks if b.get('translated'))
            logger.info(f"   已翻译: {translated_count}/{len(blocks)} 条")
            
            return blocks, current_batch
            
        except Exception as e:
            logger.error(f"❌ 加载进度文件失败: {e}")
            return None, 0
    
    def translate_batch(self, texts: list) -> list:
        """
        翻译一批文本
        
        Args:
            texts: 待翻译的文本列表
            
        Returns:
            翻译后的文本列表
        """
        text_dict = {str(idx): text for idx, text in enumerate(texts)}
        
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
            translations = []
            for idx in range(len(texts)):
                translations.append(translated_dict.get(str(idx), texts[idx]))
            
            return translations
            
        except Exception as e:
            logger.error(f"❌ 翻译失败: {e}")
            # 失败时返回原文
            return texts
    
    def translate_vtt_smart(
        self,
        input_path: str,
        output_path: str = None,
        batch_size: int = 20,
        progress_dir: str = None,
        resume: bool = True
    ) -> str:
        """
        智能翻译 VTT 字幕（支持断点续传）
        
        Args:
            input_path: 输入 VTT 文件路径
            output_path: 输出 VTT 文件路径
            batch_size: 批量翻译大小
            progress_dir: 进度文件保存目录
            resume: 是否启用断点续传
            
        Returns:
            输出文件路径
        """
        # 默认输出路径
        if not output_path:
            input_file = Path(input_path)
            if '.en.vtt' in input_file.name:
                output_name = input_file.name.replace('.en.vtt', '.zh.vtt')
            else:
                output_name = input_file.stem + '_zh.vtt'
            output_path = input_file.parent / output_name
        
        # 进度文件路径
        if not progress_dir:
            progress_dir = Path(input_path).parent / '.translation_progress'
        os.makedirs(progress_dir, exist_ok=True)
        
        progress_file = Path(progress_dir) / f"{Path(input_path).stem}_progress.json"
        
        logger.info("="*60)
        logger.info("🌐 智能 VTT 字幕翻译器（支持断点续传）")
        logger.info("="*60)
        logger.info(f"📁 输入: {input_path}")
        logger.info(f"📁 输出: {output_path}")
        logger.info(f"💾 进度: {progress_file}")
        logger.info("")
        
        # 尝试加载进度
        blocks = None
        start_batch = 0
        
        if resume:
            blocks, start_batch = self.load_progress(progress_file)
        
        # 如果没有进度，重新解析
        if blocks is None:
            blocks = self.parse_vtt(input_path)
            if not blocks:
                logger.error("❌ 未找到字幕内容")
                return None
        
        total_blocks = len(blocks)
        total_batches = (total_blocks + batch_size - 1) // batch_size
        
        logger.info("")
        logger.info(f"📊 翻译任务:")
        logger.info(f"   总字幕数: {total_blocks}")
        logger.info(f"   批次大小: {batch_size}")
        logger.info(f"   总批次数: {total_batches}")
        
        if start_batch > 0:
            translated_count = sum(1 for b in blocks if b.get('translated'))
            logger.info(f"   已完成: {translated_count}/{total_blocks} ({translated_count*100//total_blocks}%)")
        
        logger.info("")
        logger.info("🚀 开始翻译...")
        logger.info("")
        
        # 分批翻译
        for batch_idx in range(start_batch, total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_blocks)
            batch_blocks = blocks[start_idx:end_idx]
            
            # 过滤已翻译的
            to_translate = []
            to_translate_indices = []
            
            for i, block in enumerate(batch_blocks):
                if not block.get('translated'):
                    to_translate.append(block['text'])
                    to_translate_indices.append(i)
            
            if not to_translate:
                logger.info(f"⏭️  批次 {batch_idx + 1}/{total_batches} 已翻译，跳过")
                continue
            
            logger.info(f"🤖 翻译批次 {batch_idx + 1}/{total_batches} ({len(to_translate)} 条待翻译)...")
            
            try:
                # 翻译
                translations = self.translate_batch(to_translate)
                
                # 更新翻译结果
                for idx, translation in zip(to_translate_indices, translations):
                    batch_blocks[idx]['translated'] = translation
                
                # 保存进度
                self.save_progress(progress_file, blocks, batch_idx + 1)
                
                # 显示进度
                total_translated = sum(1 for b in blocks if b.get('translated'))
                progress_percent = (total_translated * 100) // total_blocks
                
                # 进度条
                bar_length = 40
                filled = int(bar_length * progress_percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                logger.info(f"   ✅ 批次完成")
                logger.info(f"   📊 总进度: [{bar}] {progress_percent}% ({total_translated}/{total_blocks})")
                
            except Exception as e:
                logger.error(f"   ❌ 批次 {batch_idx + 1} 失败: {e}")
                logger.error(f"   💾 进度已保存，可以稍后继续")
                return None
        
        # 生成最终 VTT 文件
        logger.info("")
        logger.info("💾 生成最终 VTT 文件...")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n')
            f.write('Kind: captions\n')
            f.write('Language: zh\n\n')
            
            for block in blocks:
                f.write(f"{block['timestamp']}\n")
                # 使用翻译结果，如果没有则使用原文
                text = block.get('translated') or block['text']
                f.write(f"{text}\n\n")
        
        logger.info(f"✅ VTT 文件已生成: {output_path}")
        
        # 清理进度文件
        if os.path.exists(progress_file):
            os.remove(progress_file)
            logger.info("🗑️  进度文件已清理")
        
        logger.info("")
        logger.info("="*60)
        logger.info("✨ 翻译完成！")
        logger.info("="*60)
        logger.info(f"📊 统计:")
        logger.info(f"   字幕数量: {total_blocks}")
        logger.info(f"   输出文件: {output_path}")
        logger.info("="*60)
        logger.info("")
        
        return str(output_path)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🌐 智能 VTT 字幕翻译器（支持断点续传）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 智能翻译（自动保存进度）
  export DEEPSEEK_API_KEY="your_api_key"
  python subtitle_translator_resume.py --input subtitle.en.vtt

  # 2. 中断后继续翻译
  python subtitle_translator_resume.py --input subtitle.en.vtt --resume

  # 3. 不使用断点续传（重新开始）
  python subtitle_translator_resume.py --input subtitle.en.vtt --no-resume

  # 4. 指定进度文件目录
  python subtitle_translator_resume.py \\
    --input subtitle.en.vtt \\
    --progress-dir ./progress

💡 特点:
  - 自动保存翻译进度
  - 中断后可以继续（不会重复翻译）
  - 适合大文件（2000+ 条字幕）
  - 每批翻译后立即保存
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
    parser.add_argument(
        '--progress-dir',
        help='进度文件保存目录（默认: 输入文件同目录/.translation_progress）'
    )
    parser.add_argument(
        '--resume', '-r',
        action='store_true',
        default=True,
        help='启用断点续传（默认启用）'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='禁用断点续传，从头开始翻译'
    )
    
    args = parser.parse_args()
    
    # 处理 resume 参数
    if args.no_resume:
        args.resume = False
    
    try:
        # 检查输入文件
        if not os.path.exists(args.input):
            print(f"❌ 错误：输入文件不存在: {args.input}")
            return 1
        
        # 创建翻译器
        translator = SmartVTTTranslator(api_key=args.api_key)
        
        # 翻译字幕
        output_file = translator.translate_vtt_smart(
            input_path=args.input,
            output_path=args.output,
            batch_size=args.batch_size,
            progress_dir=args.progress_dir,
            resume=args.resume
        )
        
        if output_file:
            return 0
        else:
            return 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  翻译已中断")
        print("💡 提示: 再次运行相同命令可以继续翻译")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.exception("详细错误信息:")
        return 1


if __name__ == '__main__':
    exit(main())


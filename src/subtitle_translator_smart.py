#!/usr/bin/env python3
"""
超智能字幕翻译器
- 支持断点续传
- 智能分段（在自然断点处分批）
- 动态批次大小
- 保持上下文连贯
- 支持 VTT 和 SRT 格式
"""

import os
import re
import json
import argparse
from pathlib import Path
from openai import OpenAI
import logging
from datetime import datetime
from subtitle_parser import parse_subtitle, write_subtitle, detect_format

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SuperSmartVTTTranslator:
    """超智能字幕翻译器"""
    
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
                        'translated': None
                    })
            else:
                i += 1
        
        logger.info(f"✅ 解析完成，共 {len(blocks)} 个字幕块")
        return blocks
    
    def is_natural_breakpoint(self, text: str) -> bool:
        """
        判断是否是自然断点
        
        Args:
            text: 字幕文本
            
        Returns:
            是否是自然断点
        """
        # 检查是否以句号、问号、感叹号、省略号等结束
        sentence_endings = ['.', '!', '?', '...', '。', '！', '？', '…']
        
        text = text.strip()
        for ending in sentence_endings:
            if text.endswith(ending):
                return True
        
        # 检查是否是对话结束（引号后的标点）
        if text.endswith('."') or text.endswith('!"') or text.endswith('?"'):
            return True
        
        return False
    
    def create_smart_batches(
        self,
        blocks: list,
        target_size: int = 50,
        min_size: int = 30,
        max_size: int = 70
    ) -> list:
        """
        智能创建批次（在自然断点处分批）
        
        Args:
            blocks: 字幕块列表
            target_size: 目标批次大小
            min_size: 最小批次大小
            max_size: 最大批次大小
            
        Returns:
            批次列表，每个批次是字幕块的索引范围 [(start, end), ...]
        """
        logger.info(f"🧠 智能分批...")
        logger.info(f"   目标批次大小: {target_size}")
        logger.info(f"   允许范围: {min_size}-{max_size}")
        
        batches = []
        start_idx = 0
        current_size = 0
        
        for i, block in enumerate(blocks):
            current_size += 1
            
            # 检查是否达到目标大小附近
            if current_size >= min_size:
                # 如果是自然断点，或者达到最大大小
                if self.is_natural_breakpoint(block['text']) or current_size >= max_size:
                    batches.append((start_idx, i + 1))
                    logger.debug(f"   批次 {len(batches)}: [{start_idx}, {i+1}), 大小: {current_size}")
                    start_idx = i + 1
                    current_size = 0
        
        # 处理剩余的
        if start_idx < len(blocks):
            batches.append((start_idx, len(blocks)))
            logger.debug(f"   批次 {len(batches)}: [{start_idx}, {len(blocks)}), 大小: {len(blocks) - start_idx}")
        
        logger.info(f"✅ 分批完成，共 {len(batches)} 个批次")
        
        # 统计批次大小
        sizes = [end - start for start, end in batches]
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        logger.info(f"   平均批次大小: {avg_size:.1f}")
        logger.info(f"   最小批次: {min(sizes) if sizes else 0}")
        logger.info(f"   最大批次: {max(sizes) if sizes else 0}")
        
        return batches
    
    def save_progress(self, progress_file: str, blocks: list, current_batch: int, batches: list):
        """保存翻译进度"""
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'current_batch': current_batch,
            'total_blocks': len(blocks),
            'batches': batches,
            'blocks': blocks
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 进度已保存: {progress_file}")
    
    def load_progress(self, progress_file: str) -> tuple:
        """加载翻译进度"""
        if not os.path.exists(progress_file):
            return None, 0, None
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            blocks = progress_data['blocks']
            current_batch = progress_data['current_batch']
            batches = progress_data.get('batches')
            
            logger.info(f"📂 找到进度文件，上次翻译到批次 {current_batch}")
            logger.info(f"   时间: {progress_data['timestamp']}")
            
            translated_count = sum(1 for b in blocks if b.get('translated'))
            logger.info(f"   已翻译: {translated_count}/{len(blocks)} 条")
            
            return blocks, current_batch, batches
            
        except Exception as e:
            logger.error(f"❌ 加载进度文件失败: {e}")
            return None, 0, None
    
    def translate_batch(self, texts: list, retry_count: int = 0, max_retries: int = 3) -> list:
        """翻译一批文本（支持重试）"""
        text_dict = {str(idx): text for idx, text in enumerate(texts)}
        
        prompt = f"""请将以下英文字幕翻译成中文。要求：
1. 保持原意，译文自然流畅
2. 注意上下文连贯性，这些字幕是连续的
3. 适合字幕显示，简洁易读
4. 专业术语准确翻译
5. 返回纯 JSON 格式，key 是序号（字符串），value 是翻译后的文本
6. 不要添加任何解释或标记，只返回 JSON 对象

原文（共 {len(texts)} 条连续字幕）：
{json.dumps(text_dict, ensure_ascii=False, indent=2)}

请直接返回标准 JSON 对象，格式如：{{"0": "翻译文本", "1": "翻译文本", ...}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是专业的字幕翻译专家。只返回标准 JSON 格式的翻译结果，不要添加任何额外内容或标记。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            
            # 多种方式提取 JSON
            json_content = self.extract_json(content)
            
            if not json_content:
                logger.warning(f"⚠️  无法提取 JSON，原始响应前200字符：\n{content[:200]}")
                raise ValueError("无法从响应中提取有效的 JSON")
            
            translated_dict = json.loads(json_content)
            
            # 按顺序提取翻译结果
            translations = []
            for idx in range(len(texts)):
                translation = translated_dict.get(str(idx), texts[idx])
                translations.append(translation)
            
            # 检测翻译是否真的成功（检查是否有中文字符）
            chinese_count = sum(1 for t in translations if self.has_chinese(t))
            if chinese_count < len(translations) * 0.5:  # 如果超过50%没有中文，认为翻译失败
                logger.warning(f"⚠️  翻译结果检测：只有 {chinese_count}/{len(translations)} 条包含中文")
                raise ValueError("翻译结果不包含足够的中文内容，可能翻译失败")
            
            return translations
            
        except json.JSONDecodeError as e:
            if retry_count < max_retries:
                logger.warning(f"⚠️  JSON 解析失败（第 {retry_count + 1}/{max_retries} 次），重试中...")
                import time
                time.sleep(2)  # 等待2秒后重试
                return self.translate_batch(texts, retry_count + 1, max_retries)
            else:
                logger.error(f"❌ JSON 解析失败（已重试 {max_retries} 次）: {e}")
                raise
        except Exception as e:
            if retry_count < max_retries and "API" in str(e):
                logger.warning(f"⚠️  API 错误（第 {retry_count + 1}/{max_retries} 次），重试中...")
                import time
                time.sleep(2)
                return self.translate_batch(texts, retry_count + 1, max_retries)
            else:
                logger.error(f"❌ 翻译失败: {e}")
                raise
    
    def extract_json(self, content: str) -> str:
        """从响应中提取 JSON（支持多种格式）"""
        import re
        
        # 1. 尝试直接解析
        if content.startswith('{') and content.endswith('}'):
            return content
        
        # 2. 移除代码块标记
        if '```' in content:
            parts = content.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith('{') and part.endswith('}'):
                    return part
        
        # 3. 正则提取 JSON 对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        if matches:
            # 返回最长的匹配（通常是完整的 JSON）
            return max(matches, key=len)
        
        return None
    
    def has_chinese(self, text: str) -> bool:
        """检测文本是否包含中文字符"""
        import re
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    def translate_vtt_super_smart(
        self,
        input_path: str,
        output_path: str = None,
        target_batch_size: int = 50,
        min_batch_size: int = 30,
        max_batch_size: int = 70,
        progress_dir: str = None,
        resume: bool = True
    ) -> str:
        """
        超智能翻译字幕（支持 VTT 和 SRT 格式）
        
        Args:
            input_path: 输入字幕文件路径（VTT 或 SRT）
            output_path: 输出字幕文件路径（自动匹配格式）
            target_batch_size: 目标批次大小
            min_batch_size: 最小批次大小
            max_batch_size: 最大批次大小
            progress_dir: 进度文件保存目录
            resume: 是否启用断点续传
            
        Returns:
            输出文件路径
        """
        # 检测输入格式
        input_format = detect_format(input_path)
        logger.info(f"📋 检测到格式: {input_format.upper()}")
        
        # 默认输出路径
        if not output_path:
            input_file = Path(input_path)
            # 根据格式和命名生成输出路径
            if input_format == 'vtt':
                if '.en.vtt' in input_file.name:
                    output_name = input_file.name.replace('.en.vtt', '.zh.vtt')
                else:
                    output_name = input_file.stem + '_zh.vtt'
            else:  # srt
                if '.en.srt' in input_file.name:
                    output_name = input_file.name.replace('.en.srt', '.zh.srt')
                else:
                    output_name = input_file.stem + '_zh.srt'
            output_path = input_file.parent / output_name
        
        # 进度文件路径
        if not progress_dir:
            progress_dir = Path(input_path).parent / '.translation_progress'
        os.makedirs(progress_dir, exist_ok=True)
        
        progress_file = Path(progress_dir) / f"{Path(input_path).stem}_smart_progress.json"
        
        logger.info("="*60)
        logger.info("🚀 超智能字幕翻译器（支持 VTT/SRT）")
        logger.info("="*60)
        logger.info(f"📁 输入: {input_path}")
        logger.info(f"📁 输出: {output_path}")
        logger.info(f"💾 进度: {progress_file}")
        logger.info("")
        
        # 尝试加载进度
        blocks = None
        start_batch = 0
        batches = None
        
        if resume:
            blocks, start_batch, batches = self.load_progress(progress_file)
        
        # 如果没有进度，重新解析和分批
        if blocks is None:
            # 使用新的解析器，自动检测格式
            _, parsed_blocks = parse_subtitle(input_path)
            blocks = [{'text': b['text'], 'start_time': b['start_time'], 'end_time': b['end_time']} 
                      for b in parsed_blocks]
            if not blocks:
                logger.error("❌ 未找到字幕内容")
                return None
            
            # 智能分批
            logger.info("")
            batches = self.create_smart_batches(
                blocks,
                target_size=target_batch_size,
                min_size=min_batch_size,
                max_size=max_batch_size
            )
        
        total_blocks = len(blocks)
        total_batches = len(batches)
        
        logger.info("")
        logger.info(f"📊 翻译任务:")
        logger.info(f"   总字幕数: {total_blocks}")
        logger.info(f"   智能批次数: {total_batches}")
        logger.info(f"   批次大小范围: {min_batch_size}-{max_batch_size} (目标: {target_batch_size})")
        
        if start_batch > 0:
            translated_count = sum(1 for b in blocks if b.get('translated'))
            logger.info(f"   已完成: {translated_count}/{total_blocks} ({translated_count*100//total_blocks}%)")
        
        logger.info("")
        logger.info("🚀 开始翻译...")
        logger.info("")
        
        # 分批翻译
        for batch_idx in range(start_batch, total_batches):
            start_idx, end_idx = batches[batch_idx]
            batch_blocks = blocks[start_idx:end_idx]
            batch_size = end_idx - start_idx
            
            # 过滤已翻译的
            to_translate = []
            to_translate_indices = []
            
            for i, block in enumerate(batch_blocks):
                if not block.get('translated'):
                    to_translate.append(block['text'])
                    to_translate_indices.append(start_idx + i)
            
            if not to_translate:
                logger.info(f"⏭️  批次 {batch_idx + 1}/{total_batches} (大小: {batch_size}) 已翻译，跳过")
                continue
            
            logger.info(f"🤖 翻译批次 {batch_idx + 1}/{total_batches} (大小: {batch_size}, 待翻译: {len(to_translate)})...")
            
            # 显示批次的首尾字幕（用于确认分段合理）
            if to_translate:
                first_text = to_translate[0][:50] + "..." if len(to_translate[0]) > 50 else to_translate[0]
                last_text = to_translate[-1][:50] + "..." if len(to_translate[-1]) > 50 else to_translate[-1]
                logger.info(f"   首条: {first_text}")
                logger.info(f"   末条: {last_text}")
            
            try:
                # 翻译
                translations = self.translate_batch(to_translate)
                
                # 更新翻译结果
                for idx, translation in zip(to_translate_indices, translations):
                    blocks[idx]['translated'] = translation
                
                # 保存进度
                self.save_progress(progress_file, blocks, batch_idx + 1, batches)
                
                # 显示进度
                total_translated = sum(1 for b in blocks if b.get('translated'))
                progress_percent = (total_translated * 100) // total_blocks
                
                # 进度条
                bar_length = 40
                filled = int(bar_length * progress_percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                logger.info(f"   ✅ 批次完成")
                logger.info(f"   📊 总进度: [{bar}] {progress_percent}% ({total_translated}/{total_blocks})")
                logger.info("")
                
            except Exception as e:
                logger.error(f"   ❌ 批次 {batch_idx + 1} 失败: {e}")
                logger.error(f"   💾 进度已保存，可以稍后继续")
                return None
        
        # 生成最终字幕文件（根据输入格式）
        logger.info(f"💾 生成最终 {input_format.upper()} 文件...")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为 write_subtitle 需要的格式
        output_blocks = []
        for block in blocks:
            output_blocks.append({
                'start_time': block['start_time'],
                'end_time': block['end_time'],
                'text': block.get('translated') or block['text']
            })
        
        # 使用新的写入函数，自动处理格式
        write_subtitle(output_blocks, str(output_path), input_format)
        
        logger.info(f"✅ {input_format.upper()} 文件已生成: {output_path}")
        
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
        logger.info(f"   智能批次: {total_batches}")
        logger.info(f"   输出文件: {output_path}")
        logger.info("="*60)
        logger.info("")
        
        return str(output_path)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🚀 超智能字幕翻译器（支持 VTT/SRT + 智能分段 + 断点续传）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 翻译 VTT 字幕
  export DEEPSEEK_API_KEY="your_api_key"
  python subtitle_translator_smart.py --input subtitle.en.vtt
  
  # 2. 翻译 SRT 字幕
  python subtitle_translator_smart.py --input subtitle.en.srt

  # 3. 调整批次大小
  python subtitle_translator_smart.py \\
    --input subtitle.en.vtt \\
    --target-size 50 \\
    --min-size 30 \\
    --max-size 70

  # 3. 中断后继续
  python subtitle_translator_smart.py --input subtitle.en.vtt --resume

💡 特点:
  - 智能分段：在句子结束处分批，保持连贯
  - 动态批次：目标50条，但会在自然断点调整
  - 上下文完整：避免在句子中间截断
  - 断点续传：支持中断恢复
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入字幕文件路径（支持 VTT 或 SRT 格式）'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出字幕文件路径（默认自动生成，格式与输入一致）'
    )
    parser.add_argument(
        '--api-key',
        help='DeepSeek API Key（也可通过环境变量 DEEPSEEK_API_KEY 设置）'
    )
    parser.add_argument(
        '--target-size', '-t',
        type=int,
        default=50,
        help='目标批次大小（默认: 50）'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=30,
        help='最小批次大小（默认: 30）'
    )
    parser.add_argument(
        '--max-size',
        type=int,
        default=70,
        help='最大批次大小（默认: 70）'
    )
    parser.add_argument(
        '--progress-dir',
        help='进度文件保存目录'
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
    
    if args.no_resume:
        args.resume = False
    
    try:
        if not os.path.exists(args.input):
            print(f"❌ 错误：输入文件不存在: {args.input}")
            return 1
        
        translator = SuperSmartVTTTranslator(api_key=args.api_key)
        
        output_file = translator.translate_vtt_super_smart(
            input_path=args.input,
            output_path=args.output,
            target_batch_size=args.target_size,
            min_batch_size=args.min_size,
            max_batch_size=args.max_size,
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


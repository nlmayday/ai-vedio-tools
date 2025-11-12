#!/usr/bin/env python3
"""
智能视频封面生成器
自动从视频名称提取信息，通过 AI 生成文案，然后生成封面
"""

import os
import sys
import json
import argparse
from pathlib import Path
from openai import OpenAI
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutoCoverGenerator:
    """自动封面生成器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化
        
        Args:
            api_key: DeepSeek API Key，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if not self.api_key:
            raise ValueError("请提供 DeepSeek API Key 或设置环境变量 DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def extract_video_name(self, video_path: str) -> str:
        """
        从视频路径提取视频名称
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频名称（不含扩展名，保留完整名称）
        """
        video_name = Path(video_path).stem
        # 保留完整名称（包括ID）以确保目录名称一致
        
        logger.info(f"📝 提取的视频名称: {video_name}")
        return video_name
    
    def generate_cover_text(self, video_name: str) -> dict:
        """
        使用 DeepSeek API 生成封面文案
        
        Args:
            video_name: 视频名称
            
        Returns:
            包含 title1, title2, subtitle_cn, subtitle_en 的字典
        """
        logger.info("🤖 正在调用 DeepSeek API 生成封面文案...")
        
        prompt = f"""你是一个专业的视频封面文案设计师。请根据视频名称，生成吸引人的封面文案。

视频名称：{video_name}

要求：
1. title1（主标题第一行）：简短有力，3-8个字/单词，可以是中文或英文
2. title2（主标题第二行）：补充说明，3-8个字/单词，与title1形成呼应
3. subtitle_cn（中文副标题）：12-20个字，描述核心内容
4. subtitle_en（英文副标题）：对应的英文翻译，简洁地道

注意：
- 封面文案要专业、吸引人、符合视频主题
- 中英文要自然流畅
- B站标题要吸引点击（不超过80字符）
- 标签选择热门、相关的关键词（3-5个）
- 简介要详细介绍视频内容（200-1000字）

请直接返回 JSON 格式，不要有其他说明：
{{
    "title1": "封面主标题第一行",
    "title2": "封面主标题第二行",
    "subtitle_cn": "中文副标题",
    "subtitle_en": "English subtitle",
    "bilibili_title": "B站视频标题（吸引人的标题）",
    "bilibili_tags": ["标签1", "标签2", "标签3", "标签4"],
    "bilibili_description": "详细的视频简介，介绍视频主要内容、亮点、适合人群等（200-1000字）"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的视频封面文案设计师。请根据要求生成JSON格式的文案，不要有其他内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # 提取 JSON（移除可能的 markdown 代码块标记）
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            content = content.strip()
            
            result = json.loads(content)
            
            logger.info("✅ AI 生成的文案：")
            logger.info(f"   封面标题1: {result['title1']}")
            logger.info(f"   封面标题2: {result['title2']}")
            logger.info(f"   中文副标题: {result['subtitle_cn']}")
            logger.info(f"   英文副标题: {result['subtitle_en']}")
            logger.info(f"   B站标题: {result.get('bilibili_title', 'N/A')}")
            logger.info(f"   B站标签: {', '.join(result.get('bilibili_tags', []))}")
            logger.info(f"   B站简介: {result.get('bilibili_description', '')[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI 生成文案失败: {e}")
            # 返回默认文案
            return {
                "title1": video_name[:10],
                "title2": "精彩内容",
                "subtitle_cn": "观看完整视频了解更多",
                "subtitle_en": "Watch Full Video"
            }
    
    def generate_cover(
        self,
        video_path: str,
        texts: dict,
        scheme: str = 'modern',
        frame_position: float = 0.3,
        output_path: str = None,
        video_output_dir: str = None
    ) -> str:
        """
        生成封面
        
        Args:
            video_path: 视频路径
            texts: 包含文案的字典
            scheme: 配色方案
            frame_position: 视频帧位置
            output_path: 输出路径
            video_output_dir: 视频专属输出目录
            
        Returns:
            生成的封面路径
        """
        if not output_path:
            video_name = Path(video_path).stem
            # 使用视频专属目录
            if video_output_dir:
                output_path = os.path.join(video_output_dir, f"{scheme}.jpg")
            else:
                output_path = f"../output/{video_name}/{scheme}.jpg"
        
        # 构建命令
        cmd = [
            'python3', 'src/thumbnail_generator.py',
            '--video', video_path,
            '--title1', texts['title1'],
            '--title2', texts['title2'],
            '--subtitle-cn', texts['subtitle_cn'],
            '--subtitle-en', texts['subtitle_en'],
            '--scheme', scheme,
            '--frame-position', str(frame_position),
            '--output', output_path
        ]
        
        logger.info(f"🎨 生成 {scheme} 配色方案封面...")
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"✅ 封面生成成功: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 封面生成失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            raise
    
    def auto_generate(
        self,
        video_path: str,
        schemes: list = None,
        frame_positions: dict = None,
        output_dir: str = None
    ) -> list:
        """
        自动生成所有配色方案的封面
        
        Args:
            video_path: 视频路径
            schemes: 配色方案列表，默认全部生成
            frame_positions: 每个方案的帧位置，默认使用推荐位置
            output_dir: 输出基础目录
            
        Returns:
            生成的封面路径列表
        """
        # 默认配色方案
        if schemes is None:
            schemes = ['modern', 'vibrant', 'elegant', 'fresh']
        
        # 默认帧位置
        if frame_positions is None:
            frame_positions = {
                'modern': 0.3,
                'vibrant': 0.35,
                'elegant': 0.25,
                'fresh': 0.4
            }
        
        # 提取视频名称
        video_name = self.extract_video_name(video_path)
        
        # 创建视频专属输出目录
        if output_dir:
            video_output_dir = os.path.join(output_dir, video_name)
        else:
            video_output_dir = os.path.join("../output", video_name)
        
        # 确保目录存在
        os.makedirs(video_output_dir, exist_ok=True)
        logger.info(f"📁 输出目录: {video_output_dir}")
        
        # 检查是否已有文案文件
        texts_file = os.path.join(video_output_dir, "cover_texts.json")
        
        if os.path.exists(texts_file):
            logger.info(f"✅ 发现已有文案文件，直接使用（跳过 DeepSeek 请求）")
            try:
                with open(texts_file, 'r', encoding='utf-8') as f:
                    texts = json.load(f)
                logger.info(f"   封面标题: {texts.get('title1', 'N/A')} / {texts.get('title2', 'N/A')}")
            except Exception as e:
                logger.warning(f"   ⚠️  读取文案失败: {e}，重新生成")
                texts = self.generate_cover_text(video_name)
                with open(texts_file, 'w', encoding='utf-8') as f:
                    json.dump(texts, f, ensure_ascii=False, indent=2)
        else:
            # 生成新文案
            texts = self.generate_cover_text(video_name)
            
            # 保存文案到文件
            with open(texts_file, 'w', encoding='utf-8') as f:
                json.dump(texts, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 文案已保存: {texts_file}")
        
        # 生成所有封面
        generated_covers = []
        
        for scheme in schemes:
            try:
                frame_pos = frame_positions.get(scheme, 0.3)
                
                cover_path = self.generate_cover(
                    video_path=video_path,
                    texts=texts,
                    scheme=scheme,
                    frame_position=frame_pos,
                    video_output_dir=video_output_dir
                )
                
                generated_covers.append(cover_path)
                
            except Exception as e:
                logger.error(f"❌ 生成 {scheme} 配色封面失败: {e}")
                continue
        
        return generated_covers


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🎬 智能视频封面生成器 - 自动生成精美封面',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 自动生成所有配色方案（需要设置环境变量 DEEPSEEK_API_KEY）
  export DEEPSEEK_API_KEY="your_api_key"
  python auto_generate_cover.py --video ../data/video.mp4

  # 2. 指定 API Key
  python auto_generate_cover.py \\
    --video ../data/video.mp4 \\
    --api-key "your_api_key"

  # 3. 只生成指定配色方案
  python auto_generate_cover.py \\
    --video ../data/video.mp4 \\
    --schemes modern vibrant

  # 4. 指定输出目录
  python auto_generate_cover.py \\
    --video ../data/video.mp4 \\
    --output-dir ../output/covers

💡 提示：
  - 首次使用需要设置 DeepSeek API Key
  - 会自动生成 4 种配色方案的封面
  - AI 会根据视频名称智能生成文案
        """
    )
    
    parser.add_argument(
        '--video', '-v',
        required=True,
        help='视频文件路径'
    )
    parser.add_argument(
        '--api-key',
        help='DeepSeek API Key（也可通过环境变量 DEEPSEEK_API_KEY 设置）'
    )
    parser.add_argument(
        '--schemes', '-s',
        nargs='+',
        choices=['modern', 'vibrant', 'elegant', 'fresh'],
        help='要生成的配色方案（默认：全部）'
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='输出目录（默认：../output/）'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🎬 智能视频封面生成器")
    print("="*60)
    
    try:
        # 创建生成器
        generator = AutoCoverGenerator(api_key=args.api_key)
        
        # 检查视频文件
        if not os.path.exists(args.video):
            print(f"❌ 错误：视频文件不存在: {args.video}")
            return 1
        
        print(f"\n📹 视频文件: {args.video}")
        
        # 生成封面
        covers = generator.auto_generate(
            video_path=args.video,
            schemes=args.schemes,
            output_dir=args.output_dir
        )
        
        # 显示结果
        print("\n" + "="*60)
        print(f"✨ 成功生成 {len(covers)} 个封面！")
        print("="*60)
        
        for i, cover in enumerate(covers, 1):
            print(f"  {i}. {cover}")
        
        print("\n" + "="*60)
        print("🎉 封面生成完成！")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.exception("详细错误信息:")
        return 1


if __name__ == '__main__':
    exit(main())


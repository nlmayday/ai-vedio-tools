#!/usr/bin/env python3
"""
YouTube视频转微信公众号文章工具
整合视频下载、字幕提取、文章生成的完整流程
"""

import os
import re
import sys
import json
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from wechat_article_generator import WechatArticleGenerator
from subtitle_parser import parse_subtitle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YouTubeToWechatConverter:
    """YouTube视频转微信公众号文章转换器"""
    
    def __init__(self, youtube_url: str, output_dir: str = None):
        """
        初始化转换器
        
        Args:
            youtube_url: YouTube视频URL
            output_dir: 输出目录（默认为 ../output/{video_id}）
        """
        self.youtube_url = youtube_url
        self.video_id = self.extract_video_id(youtube_url)
        
        if not self.video_id:
            raise ValueError(f"无法从URL提取视频ID: {youtube_url}")
        
        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent / 'output' / self.video_id
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 输出目录: {self.output_dir}")
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        从YouTube URL提取视频ID
        
        Args:
            url: YouTube URL
            
        Returns:
            视频ID或None
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download_video_and_subtitles(self) -> Tuple[bool, Optional[Path], Optional[Path]]:
        """
        下载YouTube视频和字幕
        
        Returns:
            (success, video_path, subtitle_path)
        """
        logger.info("=" * 70)
        logger.info("📥 步骤 1/3：下载YouTube视频和字幕")
        logger.info("=" * 70)
        
        # 检查是否已存在
        existing_files = list(self.output_dir.glob(f"*{self.video_id}*"))
        existing_video = None
        existing_subtitle = None
        
        for f in existing_files:
            if f.suffix in ['.mp4', '.webm', '.mkv']:
                existing_video = f
            elif f.suffix in ['.vtt', '.srt'] and ('.en.' in f.name or '.en-' in f.name):
                existing_subtitle = f
        
        if existing_video and existing_subtitle:
            logger.info(f"✅ 视频和字幕已存在，跳过下载")
            logger.info(f"   视频: {existing_video.name}")
            logger.info(f"   字幕: {existing_subtitle.name}")
            return True, existing_video, existing_subtitle
        
        # 构建yt-dlp命令
        cmd = [
            'yt-dlp',
            '--write-subs',          # 下载字幕
            '--write-auto-subs',     # 包含自动生成的字幕
            '--sub-langs', 'en',     # 只下载英文字幕
            '--skip-download',       # 只下载字幕，不下载视频（节省时间）
            '--cookies-from-browser', 'chrome',
            '--output', str(self.output_dir / '%(title)s [%(id)s].%(ext)s'),
            self.youtube_url
        ]
        
        logger.info(f"📥 正在下载字幕: {self.youtube_url}")
        logger.info(f"   命令: {' '.join(cmd)}")
        logger.info("")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"❌ yt-dlp执行失败")
                logger.error(f"错误信息: {result.stderr}")
                return False, None, None
            
            # 查找下载的文件
            new_files = list(self.output_dir.glob(f"*{self.video_id}*"))
            video_path = None
            subtitle_path = None
            
            for f in new_files:
                if f.suffix in ['.mp4', '.webm', '.mkv']:
                    video_path = f
                elif f.suffix in ['.vtt', '.srt'] and ('.en.' in f.name or '.en-' in f.name):
                    subtitle_path = f
            
            if subtitle_path:
                logger.info(f"✅ 字幕下载成功: {subtitle_path.name}")
                return True, video_path, subtitle_path
            else:
                logger.error(f"❌ 未找到下载的字幕文件")
                logger.error(f"   可能原因:")
                logger.error(f"   1. 视频没有英文字幕")
                logger.error(f"   2. yt-dlp配置问题")
                return False, None, None
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 下载超时（10分钟）")
            return False, None, None
        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            return False, None, None
    
    def get_video_info(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取视频信息（标题和描述）
        
        Returns:
            (title, description)
        """
        logger.info("=" * 70)
        logger.info("ℹ️  步骤 2/3：获取视频信息")
        logger.info("=" * 70)
        
        try:
            # 使用yt-dlp获取视频信息
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--skip-download',
                '--cookies-from-browser', 'chrome',
                self.youtube_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                title = info.get('title', 'Unknown Title')
                description = info.get('description', '')
                
                logger.info(f"✅ 视频标题: {title}")
                logger.info(f"✅ 视频描述: {description[:100]}..." if len(description) > 100 else f"✅ 视频描述: {description}")
                
                return title, description
            else:
                logger.warning(f"⚠️  获取视频信息失败，将使用默认值")
                return "Unknown Title", ""
                
        except Exception as e:
            logger.warning(f"⚠️  获取视频信息失败: {e}")
            return "Unknown Title", ""
    
    def generate_article(
        self,
        subtitle_path: Path,
        video_title: str,
        video_description: str,
        word_count: int = 2000,
        style: str = "professional"
    ) -> Dict:
        """
        生成微信公众号文章
        
        Args:
            subtitle_path: 字幕文件路径
            video_title: 视频标题
            video_description: 视频描述
            word_count: 目标字数
            style: 文章风格
            
        Returns:
            文章数据字典
        """
        logger.info("=" * 70)
        logger.info("📝 步骤 3/3：生成微信公众号文章")
        logger.info("=" * 70)
        
        # 解析字幕
        logger.info(f"📖 正在解析字幕: {subtitle_path.name}")
        subtitle_blocks = parse_subtitle(str(subtitle_path))
        logger.info(f"✅ 解析完成，共 {len(subtitle_blocks)} 个字幕块")
        
        # 生成文章
        generator = WechatArticleGenerator()
        article = generator.generate_article(
            video_title=video_title,
            video_description=video_description,
            subtitle_blocks=subtitle_blocks,
            word_count=word_count,
            style=style
        )
        
        # 保存文章
        generator.save_article(article, self.output_dir, self.video_id)
        
        return article
    
    def convert(
        self,
        word_count: int = 2000,
        style: str = "professional",
        skip_download: bool = False
    ) -> bool:
        """
        执行完整的转换流程
        
        Args:
            word_count: 目标字数
            style: 文章风格
            skip_download: 是否跳过下载（假设文件已存在）
            
        Returns:
            是否成功
        """
        logger.info("")
        logger.info("🚀 " + "=" * 66)
        logger.info("🚀 YouTube视频转微信公众号文章工具")
        logger.info("🚀 " + "=" * 66)
        logger.info(f"📺 视频URL: {self.youtube_url}")
        logger.info(f"🆔 视频ID: {self.video_id}")
        logger.info("")
        
        try:
            # 步骤1: 下载视频和字幕
            if not skip_download:
                success, video_path, subtitle_path = self.download_video_and_subtitles()
                if not success or not subtitle_path:
                    logger.error("❌ 下载失败，无法继续")
                    return False
            else:
                # 查找已存在的字幕文件
                subtitle_files = list(self.output_dir.glob(f"*{self.video_id}*.en.*"))
                if not subtitle_files:
                    subtitle_files = list(self.output_dir.glob(f"*{self.video_id}*.vtt"))
                
                if not subtitle_files:
                    logger.error("❌ 未找到字幕文件，请先下载")
                    return False
                
                subtitle_path = subtitle_files[0]
                logger.info(f"✅ 使用已存在的字幕: {subtitle_path.name}")
            
            logger.info("")
            
            # 步骤2: 获取视频信息
            video_title, video_description = self.get_video_info()
            
            logger.info("")
            
            # 步骤3: 生成文章
            article = self.generate_article(
                subtitle_path,
                video_title,
                video_description,
                word_count,
                style
            )
            
            # 打印摘要
            logger.info("")
            logger.info("=" * 70)
            logger.info("✅ 转换完成！")
            logger.info("=" * 70)
            logger.info(f"📝 文章标题: {article['title']}")
            logger.info(f"📊 文章字数: {article['word_count']} 字")
            logger.info(f"⏱️  阅读时间: {article.get('reading_time', '未知')}")
            logger.info(f"📁 输出目录: {self.output_dir}")
            logger.info(f"   - article.md   (Markdown格式)")
            logger.info(f"   - article.json (JSON格式)")
            logger.info(f"   - article.txt  (纯文本格式)")
            logger.info("")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 转换失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='YouTube视频转微信公众号文章工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法
  python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx
  
  # 指定字数和风格
  python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx --word-count 3000 --style casual
  
  # 指定输出目录
  python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx --output ./my_articles
  
  # 跳过下载（使用已有字幕）
  python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx --skip-download
        """
    )
    
    parser.add_argument('url', help='YouTube视频URL')
    parser.add_argument('-o', '--output', help='输出目录（默认: ../output/{video_id}）')
    parser.add_argument('-w', '--word-count', type=int, default=2000, help='目标字数（默认: 2000）')
    parser.add_argument('-s', '--style', choices=['professional', 'casual', 'academic'], 
                       default='professional', help='文章风格（默认: professional）')
    parser.add_argument('--skip-download', action='store_true', help='跳过下载，使用已有文件')
    
    args = parser.parse_args()
    
    # 检查环境变量
    if not os.getenv('DEEPSEEK_API_KEY'):
        logger.error("❌ 请设置环境变量 DEEPSEEK_API_KEY")
        logger.error("   export DEEPSEEK_API_KEY='your-api-key'")
        sys.exit(1)
    
    # 创建转换器并执行
    try:
        converter = YouTubeToWechatConverter(args.url, args.output)
        success = converter.convert(
            word_count=args.word_count,
            style=args.style,
            skip_download=args.skip_download
        )
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

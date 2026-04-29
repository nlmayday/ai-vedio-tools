#!/usr/bin/env python3
"""
YouTube 视频自动处理并上传到 B 站

完整流程：
1. 使用 yt-dlp 下载 YouTube 视频和字幕
2. 检测字幕情况并翻译（如需要）
3. 生成封面和 B 站信息
4. 合并字幕到视频
5. 自动上传到 B 站

使用方法：
    python src/youtube_to_bilibili.py "https://www.youtube.com/watch?v=VIDEO_ID"
    
    或使用快捷脚本：
    ./youtube_to_bilibili.sh "https://www.youtube.com/watch?v=VIDEO_ID"
"""

import os
import sys
import json
import subprocess
import logging
import argparse
import shutil
import yaml
from pathlib import Path
from typing import Optional, Tuple, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class YouTubeToBilibiliProcessor:
    """YouTube 视频自动处理并上传到 B 站"""
    
    def __init__(self, youtube_url: str, work_dir: str = "./data"):
        """
        初始化处理器
        
        Args:
            youtube_url: YouTube 视频链接
            work_dir: 工作目录（下载视频的位置）
        """
        self.youtube_url = youtube_url
        self.work_dir = Path(work_dir).absolute()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置文件
        self.config = self._load_config()
        
        # 提取视频ID
        self.video_id = self._extract_video_id(youtube_url)
        if not self.video_id:
            raise ValueError(f"无法从URL中提取视频ID: {youtube_url}")
        
        logger.info(f"📹 视频ID: {self.video_id}")
        logger.info(f"📁 工作目录: {self.work_dir}")
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent.parent / 'config.yaml'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 已加载配置: {config_path.name}")
            return config
        except Exception as e:
            logger.warning(f"无法加载配置文件，使用默认配置: {e}")
            return {
                'subtitle': {'type': 'soft', 'font_size': 20},
                'translation': {'translator': 'smart'},
                'cover': {'default_schemes': ['modern', 'vibrant', 'elegant', 'fresh']}
            }
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """从YouTube URL中提取视频ID"""
        import re
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download_video(self) -> Tuple[bool, Optional[Path], Optional[Path], Optional[Path]]:
        """
        使用 yt-dlp 下载视频和字幕
        
        Returns:
            (success, video_path, en_subtitle_path, zh_subtitle_path)
        """
        logger.info("=" * 70)
        logger.info("🚀 步骤 1/5：下载 YouTube 视频和字幕")
        logger.info("=" * 70)
        
        # 先检查视频和字幕是否已存在
        all_files = list(self.work_dir.glob("*"))
        existing_video = None
        existing_en_subtitle = None
        existing_zh_subtitle = None
        
        # 检查视频
        for f in all_files:
            if f.is_file() and self.video_id in f.name and f.suffix in ['.mp4', '.webm', '.mkv']:
                existing_video = f
                logger.info(f"✅ 视频已存在: {f.name}")
                logger.info(f"   跳过视频下载")
                break
        
        # 检查字幕
        if existing_video:
            # 查找已存在的字幕
            subtitle_files = [f for f in all_files if f.is_file() and self.video_id in f.name and f.suffix in ['.vtt', '.srt']]
            
            # 查找英文字幕
            for f in subtitle_files:
                if '.en.' in f.name.lower():
                    existing_en_subtitle = f
                    logger.info(f"✅ 英文字幕已存在: {f.name}")
                    logger.info(f"   跳过英文字幕下载")
                    break
            
            # 查找中文字幕
            for f in subtitle_files:
                fname_lower = f.name.lower()
                if '.zh.vtt' in fname_lower or '.zh.srt' in fname_lower:
                    if 'hans' not in fname_lower and 'hant' not in fname_lower:
                        existing_zh_subtitle = f
                        logger.info(f"✅ 中文字幕已存在: {f.name}")
                        logger.info(f"   跳过中文字幕下载")
                        break
            
            # 如果没有通用中文，查找简体中文
            if not existing_zh_subtitle:
                for f in subtitle_files:
                    if 'zh-hans' in f.name.lower():
                        existing_zh_subtitle = f
                        logger.info(f"✅ 中文字幕已存在: {f.name}")
                        logger.info(f"   跳过中文字幕下载")
                        break
        
        # 如果视频和字幕都存在，直接返回
        if existing_video and existing_en_subtitle:
            logger.info("")
            logger.info("✨ 视频和字幕都已存在，跳过下载步骤")
            logger.info("")
            return True, existing_video, existing_en_subtitle, existing_zh_subtitle
        
        # 构建 yt-dlp 命令
        if existing_video:
            # 视频已存在，只下载字幕（英文和中文）
            cmd = [
                'yt-dlp',
                '--write-subs',
                '--write-auto-subs',  # 包含自动生成的字幕
                '--sub-langs', 'en',  # 只下载英文
                '--skip-download',  # 跳过视频下载
                '--cookies-from-browser', 'chrome',
                '--output', str(self.work_dir / '%(title)s [%(id)s].%(ext)s'),
                self.youtube_url
            ]
            logger.info(f"📥 只下载字幕（英文）: {self.youtube_url}")
        else:
            # 视频不存在，下载视频和字幕
            cmd = [
                'yt-dlp',
                '--write-subs',
                '--write-auto-subs',  # 包含自动生成的字幕
                '--sub-langs', 'en',  # 只下载英文
                '--embed-subs',
                '--cookies-from-browser', 'chrome',
                '--output', str(self.work_dir / '%(title)s [%(id)s].%(ext)s'),
                self.youtube_url
            ]
            logger.info(f"📥 正在下载视频和字幕（英文）: {self.youtube_url}")
        
        logger.info(f"   命令: {' '.join(cmd)}")
        logger.info("")
        
        try:
            # 执行下载（设置较长的超时时间，大视频可能需要更长时间）
            # 超时时间：90分钟（5400秒），对于大视频应该足够
            result = subprocess.run(
                cmd,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=5400  # 90分钟超时
            )
            
            if result.returncode != 0:
                # 如果只是下载字幕失败，但视频存在，仍然继续
                if existing_video:
                    logger.warning(f"⚠️  字幕下载失败，但视频已存在，继续处理")
                    logger.warning(f"   错误信息: {result.stderr[:200]}...")
                    video_path = existing_video
                else:
                    logger.error(f"❌ 下载失败！")
                    logger.error(f"   错误信息: {result.stderr}")
                    return False, None, None, None
            else:
                # 查找下载的文件
                if existing_video:
                    # 视频已存在，直接使用
                    video_path = existing_video
                    logger.info(f"✅ 使用已存在的视频: {video_path.name}")
                else:
                    # 视频是新下载的，查找文件
                    # 使用更宽松的匹配：包含video_id的视频文件
                    all_files = list(self.work_dir.glob("*"))
                    video_files = [
                        f for f in all_files 
                        if f.is_file() 
                        and self.video_id in f.name 
                        and f.suffix in ['.mp4', '.webm', '.mkv', '.m4a']
                    ]
                    
                    if not video_files:
                        logger.error(f"❌ 未找到下载的视频文件")
                        logger.error(f"   已搜索包含 '{self.video_id}' 的文件")
                        logger.error(f"   工作目录: {self.work_dir}")
                        # 列出目录中的文件供调试
                        recent_files = sorted(all_files, key=lambda x: x.stat().st_mtime if x.is_file() else 0, reverse=True)[:5]
                        if recent_files:
                            logger.error(f"   最近的文件:")
                            for f in recent_files:
                                if f.is_file():
                                    logger.error(f"     - {f.name}")
                        return False, None, None, None
                    
                    video_path = video_files[0]
                    logger.info(f"✅ 视频下载成功: {video_path.name}")
            
            # 查找字幕文件
            base_name = video_path.stem  # 去掉扩展名
            en_subtitle = None
            zh_subtitle = None
            
            # 查找所有可能的字幕文件（使用video_id匹配）
            all_files = list(self.work_dir.glob("*"))
            all_subtitle_files = [
                f for f in all_files
                if f.is_file() 
                and self.video_id in f.name 
                and f.suffix in ['.vtt', '.srt']
            ]
            
            # 查找英文字幕（优先非自动生成的）
            for f in all_subtitle_files:
                fname_lower = f.name.lower()
                # 匹配 .en.vtt, .en.srt, .en-us.vtt 等
                if '.en.' in fname_lower or '-en.' in fname_lower or '_en.' in fname_lower:
                    # 排除自动生成的（如果有非自动生成的）
                    if 'live' not in fname_lower and 'auto' not in fname_lower:
                        en_subtitle = f
                        logger.info(f"✅ 英文字幕: {f.name}")
                        break
            
            # 如果没找到，尝试查找自动生成的英文字幕
            if not en_subtitle:
                for f in all_subtitle_files:
                    if '.en.' in f.name.lower():
                        en_subtitle = f
                        logger.info(f"✅ 英文字幕（自动生成）: {f.name}")
                        break
            
            # 查找中文字幕（优先 zh 通用中文，其次 zh-Hans 简体中文）
            # 先查找通用中文 .zh.vtt
            for f in all_subtitle_files:
                fname_lower = f.name.lower()
                if '.zh.vtt' in fname_lower or '.zh.srt' in fname_lower:
                    # 确保不是 zh-hans 或其他变体
                    if 'hans' not in fname_lower and 'hant' not in fname_lower and 'cn' not in fname_lower:
                        zh_subtitle = f
                        logger.info(f"✅ 中文字幕（通用）: {f.name}")
                        break
            
            # 如果没找到通用中文，查找简体中文 .zh-Hans.vtt
            if not zh_subtitle:
                for f in all_subtitle_files:
                    fname_lower = f.name.lower()
                    if 'zh-hans' in fname_lower or 'zh_hans' in fname_lower:
                        zh_subtitle = f
                        logger.info(f"✅ 中文字幕（简体）: {f.name}")
                        break
            
            # 如果还没找到，尝试其他中文变体
            if not zh_subtitle:
                for f in all_subtitle_files:
                    fname_lower = f.name.lower()
                    if any(zh in fname_lower for zh in ['.zh-', '_zh.', 'chinese', 'hant', 'zh-cn']):
                        zh_subtitle = f
                        logger.info(f"✅ 中文字幕（其他）: {f.name}")
                        break
            
            if not en_subtitle and not zh_subtitle:
                logger.warning(f"⚠️  未找到任何字幕文件")
                logger.warning(f"   视频已下载到: {video_path}")
                logger.warning(f"   可能的原因:")
                logger.warning(f"   1. YouTube 视频没有字幕")
                logger.warning(f"   2. yt-dlp 没有正确下载字幕")
                logger.warning(f"   3. 字幕是自动生成的，需要手动启用")
            elif not en_subtitle:
                logger.warning(f"⚠️  未找到英文字幕（但找到了其他语言字幕）")
            
            logger.info("")
            return True, video_path, en_subtitle, zh_subtitle
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 下载超时（90分钟）")
            logger.error(f"   视频太大或网络太慢，下载时间超过了90分钟")
            logger.error(f"   建议：")
            logger.error(f"   1. 检查网络连接")
            logger.error(f"   2. 尝试手动使用 yt-dlp 下载")
            logger.error(f"   3. 或稍后重试")
            return False, None, None, None
        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            import traceback
            traceback.print_exc()
            return False, None, None, None
    
    def translate_subtitle(self, subtitle_path: Path) -> Optional[Path]:
        """
        翻译字幕
        
        Args:
            subtitle_path: 英文字幕路径
            
        Returns:
            翻译后的中文字幕路径
        """
        logger.info("=" * 70)
        logger.info("🌐 步骤 2/5：翻译字幕")
        logger.info("=" * 70)
        
        # 确定输出路径
        if subtitle_path.suffix == '.vtt':
            output_path = subtitle_path.parent / subtitle_path.name.replace('.en.vtt', '.zh.vtt')
        else:  # .srt
            output_path = subtitle_path.parent / subtitle_path.name.replace('.en.srt', '.zh.srt')
        
        # 如果已存在，跳过
        if output_path.exists():
            logger.info(f"✅ 中文字幕已存在，跳过翻译: {output_path.name}")
            logger.info("")
            return output_path
        
        # 调用翻译脚本
        translator_script = Path(__file__).parent / 'subtitle_translator_smart.py'
        cmd = [
            'python3',
            str(translator_script),
            '--input', str(subtitle_path),
            '--output', str(output_path)
        ]
        
        logger.info(f"📝 正在翻译: {subtitle_path.name}")
        logger.info(f"   输出: {output_path.name}")
        logger.info("")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,  # 显示翻译进度
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ 翻译失败！")
                return None
            
            if not output_path.exists():
                logger.error(f"❌ 翻译输出文件未生成")
                return None
            
            logger.info(f"✅ 翻译完成: {output_path.name}")
            logger.info("")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ 翻译失败: {e}")
            return None
    
    def generate_cover_and_info(self, video_path: Path) -> Optional[Path]:
        """
        生成封面和 B 站信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            输出目录路径
        """
        logger.info("=" * 70)
        logger.info("🎨 步骤 3/5：生成封面和 B 站信息")
        logger.info("=" * 70)
        
        # 调用封面生成脚本
        cover_script = Path(__file__).parent / 'auto_generate_cover.py'
        # 计算项目根目录的 output 路径
        project_output = Path(__file__).parent.parent / 'output'
        cmd = [
            'python3',
            str(cover_script),
            '--video', str(video_path),
            '--output-dir', str(project_output)
        ]
        
        logger.info(f"🖼️  正在生成封面...")
        logger.info("")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ 封面生成失败！")
                return None
            
            # 找到输出目录
            video_name = video_path.stem
            # 从 src/ 目录往上一层到项目根目录，然后进入 output/
            output_dir = Path(__file__).parent.parent / 'output' / video_name
            
            if not output_dir.exists():
                logger.error(f"❌ 输出目录未生成: {output_dir}")
                return None
            
            logger.info(f"✅ 封面生成完成")
            logger.info(f"   输出目录: {output_dir}")
            logger.info("")
            return output_dir
            
        except Exception as e:
            logger.error(f"❌ 封面生成失败: {e}")
            return None
    
    def merge_subtitles(
        self,
        video_path: Path,
        en_subtitle: Path,
        zh_subtitle: Path,
        output_dir: Path
    ) -> Optional[Path]:
        """
        合并字幕到视频
        
        Args:
            video_path: 视频路径
            en_subtitle: 英文字幕路径
            zh_subtitle: 中文字幕路径
            output_dir: 输出目录
            
        Returns:
            合成后的视频路径
        """
        logger.info("=" * 70)
        logger.info("🎬 步骤 4/5：合并字幕到视频")
        logger.info("=" * 70)
        
        # 从配置读取字幕类型
        subtitle_type = self.config.get('subtitle', {}).get('type', 'soft')
        logger.info(f"📦 字幕类型: {subtitle_type}")
        
        # 输出路径
        output_video = output_dir / f'video_bilingual_{subtitle_type}.mp4'
        
        # 如果已存在，跳过
        if output_video.exists():
            logger.info(f"✅ 视频已存在，跳过合成: {output_video.name}")
            logger.info("")
            return output_video
        
        # 调用字幕合并脚本
        merger_script = Path(__file__).parent / 'video_subtitle_merger.py'
        cmd = [
            'python3',
            str(merger_script),
            '--video', str(video_path),
            '--en-subtitle', str(en_subtitle),
            '--zh-subtitle', str(zh_subtitle),
            '--type', self.config.get('subtitle', {}).get('type', 'soft'),
            '--output', str(output_video)
        ]
        
        logger.info(f"🎞️  正在合成视频...")
        logger.info(f"   视频: {video_path.name}")
        logger.info(f"   英文字幕: {en_subtitle.name}")
        logger.info(f"   中文字幕: {zh_subtitle.name}")
        logger.info(f"   输出: {output_video.name}")
        logger.info("")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ 视频合成失败！")
                return None
            
            if not output_video.exists():
                logger.error(f"❌ 输出视频未生成")
                return None
            
            logger.info(f"✅ 视频合成完成: {output_video.name}")
            logger.info("")
            return output_video
            
        except Exception as e:
            logger.error(f"❌ 视频合成失败: {e}")
            return None
    
    def upload_to_bilibili(self, output_dir: Path) -> bool:
        """
        上传到 B 站
        
        Args:
            output_dir: 输出目录（包含视频、封面、信息）
            
        Returns:
            是否成功
        """
        logger.info("=" * 70)
        logger.info("📤 步骤 5/5：准备上传到 B 站")
        logger.info("=" * 70)
        
        # 调用上传准备脚本
        upload_script = Path(__file__).parent / 'bilibili_auto_upload.py'
        cmd = [
            'python3',
            str(upload_script),
            '--video-dir', str(output_dir)
        ]
        
        logger.info(f"🚀 正在准备上传...")
        logger.info("")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ 上传准备失败！")
                return False
            
            logger.info("")
            logger.info("=" * 70)
            logger.info("✅ 上传准备完成！")
            logger.info("=" * 70)
            logger.info("")
            logger.info("📝 下一步：在 Cursor 中告诉 AI：")
            logger.info("")
            logger.info(f'   "请使用 MCP Playwright 上传视频到B站：{output_dir}"')
            logger.info("")
            logger.info("或者手动执行：")
            logger.info(f"   在浏览器中登录B站，然后让 AI 帮你自动上传")
            logger.info("")
            return True
            
        except Exception as e:
            logger.error(f"❌ 上传准备失败: {e}")
            return False
    
    def process(self, auto_upload: bool = False) -> bool:
        """
        执行完整流程
        
        Args:
            auto_upload: 是否自动上传（需要 MCP Playwright）
            
        Returns:
            是否成功
        """
        logger.info("")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("🎥 YouTube 视频自动处理并上传到 B 站")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"📺 YouTube: {self.youtube_url}")
        logger.info("")
        
        # 步骤 1: 下载视频和字幕
        success, video_path, en_subtitle, zh_subtitle = self.download_video()
        if not success or not video_path:
            logger.error("❌ 下载失败，流程终止")
            logger.error("   请检查 URL 是否正确，或网络连接是否正常")
            return False
        
        # 检查字幕情况
        if not en_subtitle and not zh_subtitle:
            logger.error("")
            logger.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.error("❌ 未找到字幕文件，无法继续处理")
            logger.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.error("")
            logger.error(f"📹 视频已下载: {video_path.name}")
            logger.error(f"📍 位置: {video_path}")
            logger.error("")
            logger.error("💡 解决方法：")
            logger.error("")
            logger.error("方法 1：手动导出 YouTube 字幕")
            logger.error("   1. 打开视频: https://www.youtube.com/watch?v=" + self.video_id)
            logger.error("   2. 点击 \"...\" 菜单 → \"显示字幕文本\"")
            logger.error("   3. 复制字幕内容，保存为 SRT 或 VTT 格式")
            logger.error("   4. 将字幕命名为以下格式之一：")
            logger.error(f"      • {video_path.stem}.en.vtt")
            logger.error(f"      • {video_path.stem}.en.srt")
            logger.error(f"   5. 放到 data 目录: {self.work_dir}")
            logger.error("")
            logger.error("方法 2：使用第三方工具下载字幕")
            logger.error("   # 安装字幕下载工具")
            logger.error("   pip install youtube-transcript-api")
            logger.error("")
            logger.error("   # 下载字幕")
            logger.error(f"   youtube_transcript_api {self.video_id} --format srt > \"{video_path.stem}.en.srt\"")
            logger.error("")
            logger.error("方法 3：使用 yt-dlp 单独下载字幕")
            logger.error(f"   cd data")
            logger.error(f"   yt-dlp --write-auto-subs --skip-download --sub-lang en \"https://www.youtube.com/watch?v={self.video_id}\"")
            logger.error("")
            logger.error("完成后，运行以下命令继续处理：")
            logger.error("   cd vedio-tools")
            logger.error("   ./auto_process.sh")
            logger.error("")
            return False
        elif not en_subtitle:
            logger.error("")
            logger.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.error("❌ 未找到英文字幕")
            logger.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.error("")
            logger.error("需要英文字幕才能翻译成中文。")
            logger.error("请参考上述方法手动导出英文字幕。")
            logger.error("")
            return False
        
        # 步骤 2: 翻译字幕（如果需要）
        if not zh_subtitle:
            logger.info("🌐 未找到中文字幕，使用 DeepSeek 翻译...")
            zh_subtitle = self.translate_subtitle(en_subtitle)
            if not zh_subtitle:
                logger.error("❌ 翻译失败，流程终止")
                return False
        else:
            logger.info(f"✅ 已有中文字幕（来自 YouTube），跳过 DeepSeek 翻译")
            logger.info(f"   节省翻译费用 ✨")
            logger.info("")
        
        # 步骤 3: 生成封面和 B 站信息
        output_dir = self.generate_cover_and_info(video_path)
        if not output_dir:
            logger.error("❌ 封面生成失败，流程终止")
            return False
        
        # 步骤 4: 合并字幕到视频
        output_video = self.merge_subtitles(video_path, en_subtitle, zh_subtitle, output_dir)
        if not output_video:
            logger.error("❌ 视频合成失败，流程终止")
            return False
        
        # 步骤 5: 上传到 B 站
        if auto_upload:
            success = self.upload_to_bilibili(output_dir)
            if not success:
                logger.error("❌ 上传失败")
                return False
        else:
            # 只准备上传，不实际上传
            success = self.upload_to_bilibili(output_dir)
        
        # 完成
        logger.info("")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("✨ 所有步骤完成！")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("")
        logger.info(f"📁 输出目录: {output_dir}")
        logger.info(f"🎬 视频文件: {output_video.name}")
        logger.info("")
        
        # 列出所有生成的文件
        files = sorted(output_dir.glob('*'))
        logger.info("📄 生成的文件：")
        for f in files:
            if f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                logger.info(f"   • {f.name} ({size_mb:.1f} MB)")
        
        logger.info("")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='YouTube 视频自动处理并上传到 B 站',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 处理 YouTube 视频（下载、翻译、生成封面、合成）
  python src/youtube_to_bilibili.py "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # 使用快捷脚本
  ./youtube_to_bilibili.sh "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # 处理并准备上传
  python src/youtube_to_bilibili.py "https://www.youtube.com/watch?v=VIDEO_ID" --prepare-upload

注意：
  1. 需要安装 yt-dlp: pip install yt-dlp
  2. 需要 Chrome 浏览器（用于 cookies）
  3. 需要 DeepSeek API Key（用于翻译）
  4. 下载可能需要较长时间（取决于视频大小）
        """
    )
    
    parser.add_argument(
        'youtube_url',
        help='YouTube 视频链接'
    )
    
    parser.add_argument(
        '--work-dir',
        default='./data',
        help='工作目录（默认：./data）'
    )
    
    parser.add_argument(
        '--prepare-upload',
        action='store_true',
        help='准备上传配置（生成 bilibili_upload_config.json）'
    )
    
    parser.add_argument(
        '--auto-upload',
        action='store_true',
        help='自动上传到 B 站（需要 MCP Playwright）'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建处理器
        processor = YouTubeToBilibiliProcessor(
            youtube_url=args.youtube_url,
            work_dir=args.work_dir
        )
        
        # 执行处理
        success = processor.process(auto_upload=args.auto_upload)
        
        if success:
            logger.info("🎉 处理成功！")
            return 0
        else:
            logger.error("❌ 处理失败")
            return 1
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
        return 130
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


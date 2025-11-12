#!/usr/bin/env python3
"""
视频自动处理系统
自动扫描、处理和备份视频
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频自动处理器"""
    
    def __init__(
        self,
        data_dir: str = None,
        backup_dir: str = None,
        output_dir: str = None,
        state_file: str = ".processing_state.json",
        check_interval: int = None,
        config_file: str = "config.yaml"
    ):
        """
        初始化处理器
        
        Args:
            data_dir: 数据目录
            backup_dir: 备份目录
            output_dir: 输出目录
            state_file: 状态文件路径
            check_interval: 检查间隔（秒）
            config_file: 配置文件路径
        """
        # 加载配置文件
        self.config = self.load_config(config_file)
        
        # 使用配置文件的值，命令行参数优先
        self.data_dir = Path(data_dir or self.config['auto_process']['data_dir'])
        self.backup_dir = Path(backup_dir or self.config['auto_process']['backup_dir'])
        self.output_dir = Path(output_dir or self.config['auto_process']['output_dir'])
        self.state_file = Path(state_file)
        self.check_interval = check_interval or self.config['auto_process']['check_interval']
        
        # 创建目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载状态
        self.state = self.load_state()
    
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        config_path = Path(config_file)
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
            return self.get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 已加载配置: {config_file}")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'subtitle': {'type': 'soft', 'font_size': 20, 'font_name': 'PingFang SC'},
            'translation': {'translator': 'smart', 'target_size': 50, 'min_size': 30, 'max_size': 70},
            'cover': {'default_schemes': ['modern', 'vibrant', 'elegant', 'fresh']},
            'auto_process': {
                'check_interval': 60,
                'data_dir': '../data',
                'backup_dir': '../data/backup',
                'output_dir': '../output',
                'generate_bilibili_subtitles': True,
                'generate_covers': True
            }
        }
    
    def load_state(self) -> Dict:
        """加载处理状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"无法加载状态文件: {e}")
        
        return {
            'processed_videos': {},
            'last_check': None
        }
    
    def save_state(self):
        """保存处理状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def is_video_ready(self, video_path: Path) -> bool:
        """
        检查视频是否下载完成
        
        方法：检查文件是否在过去1分钟内被修改
        """
        try:
            # 获取文件修改时间
            mtime = video_path.stat().st_mtime
            current_time = time.time()
            
            # 如果文件在过去1分钟内被修改，认为还在下载
            if current_time - mtime < 60:
                return False
            
            # 检查文件大小是否合理（>1MB）
            file_size = video_path.stat().st_size
            if file_size < 1024 * 1024:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查视频状态失败: {e}")
            return False
    
    def find_videos(self) -> List[Tuple[Path, Optional[Path], Optional[Path]]]:
        """
        扫描数据目录查找视频
        
        Returns:
            [(video_path, en_subtitle_path, zh_subtitle_path), ...]
        """
        videos = []
        
        # 支持的视频格式
        video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov']
        
        for video_file in self.data_dir.iterdir():
            if not video_file.is_file():
                continue
            
            if video_file.suffix.lower() not in video_extensions:
                continue
            
            # 跳过已处理的视频（但如果 files 为空，说明处理失败，需要重新处理）
            video_key = video_file.name
            if video_key in self.state['processed_videos']:
                video_info = self.state['processed_videos'][video_key]
                if video_info.get('files'):  # 只有成功生成文件才跳过
                    continue
                else:
                    logger.info(f"🔄 视频处理失败过，重新处理: {video_file.name}")
            
            # 检查视频是否下载完成
            if not self.is_video_ready(video_file):
                logger.info(f"⏳ 视频还在下载中，跳过: {video_file.name}")
                continue
            
            # 查找字幕文件
            basename = video_file.stem
            en_subtitle = None
            zh_subtitle = None
            
            # 查找英文字幕（支持 VTT 和 SRT，包括常见的拼写错误）
            for ext in ['.en.vtt', '.en.srt', '.env.srt', '.vtt', '.srt']:
                subtitle_path = self.data_dir / f"{basename}{ext}"
                if subtitle_path.exists():
                    en_subtitle = subtitle_path
                    if '.env.srt' in subtitle_path.name:
                        logger.warning(f"⚠️  检测到非标准命名 .env.srt（应该是 .en.srt）")
                    break
            
            # 查找中文字幕（支持 VTT 和 SRT）
            for ext in ['.zh.vtt', '.zh.srt']:
                subtitle_path = self.data_dir / f"{basename}{ext}"
                if subtitle_path.exists():
                    zh_subtitle = subtitle_path
                    break
            
            videos.append((video_file, en_subtitle, zh_subtitle))
        
        return videos
    
    def translate_subtitle(self, en_subtitle: Path) -> Optional[Path]:
        """
        翻译英文字幕
        
        Args:
            en_subtitle: 英文字幕路径
            
        Returns:
            中文字幕路径
        """
        logger.info(f"📝 翻译字幕: {en_subtitle.name}")
        
        try:
            result = subprocess.run(
                [
                    'python',
                    'src/subtitle_translator_smart.py',
                    '--input', str(en_subtitle)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 生成的中文字幕路径（根据输入格式自动判断）
            if '.en.vtt' in en_subtitle.name:
                zh_subtitle = en_subtitle.parent / en_subtitle.name.replace('.en.vtt', '.zh.vtt')
            elif '.en.srt' in en_subtitle.name:
                zh_subtitle = en_subtitle.parent / en_subtitle.name.replace('.en.srt', '.zh.srt')
            elif en_subtitle.suffix == '.vtt':
                zh_subtitle = en_subtitle.parent / f"{en_subtitle.stem}_zh.vtt"
            else:  # .srt
                zh_subtitle = en_subtitle.parent / f"{en_subtitle.stem}_zh.srt"
            
            if zh_subtitle.exists():
                logger.info(f"✅ 翻译完成: {zh_subtitle.name}")
                return zh_subtitle
            else:
                logger.error("❌ 翻译失败：未生成中文字幕")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 翻译失败: {e.stderr}")
            return None
    
    def merge_subtitles(
        self,
        video_path: Path,
        en_subtitle: Path,
        zh_subtitle: Path,
        video_output_dir: Path
    ) -> Optional[Path]:
        """
        合并字幕到视频
        
        Args:
            video_output_dir: 视频专属输出目录
            
        Returns:
            输出视频路径
        """
        logger.info(f"🎬 合并字幕: {video_path.name}")
        
        try:
            # 输出到 output/视频名/ 目录
            subtitle_type = self.config['subtitle']['type']
            font_size = str(self.config['subtitle']['font_size'])
            output_video = video_output_dir / f"video_bilingual_{subtitle_type}.mp4"
            
            result = subprocess.run(
                [
                    'python',
                    'src/video_subtitle_merger.py',
                    '--video', str(video_path),
                    '--en-subtitle', str(en_subtitle),
                    '--zh-subtitle', str(zh_subtitle),
                    '--type', subtitle_type,
                    '--font-size', font_size,
                    '--output', str(output_video)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            if output_video.exists():
                logger.info(f"✅ 字幕合并完成: {output_video.name}")
                return output_video
            else:
                logger.error("❌ 字幕合并失败")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 字幕合并失败: {e.stderr}")
            return None
    
    def generate_covers(self, video_path: Path, video_output_dir: Path) -> bool:
        """
        生成封面
        
        Args:
            video_path: 视频路径
            video_output_dir: 视频专属输出目录
            
        Returns:
            是否成功
        """
        logger.info(f"🎨 生成封面: {video_path.name}")
        
        try:
            result = subprocess.run(
                [
                    'python',
                    'src/auto_generate_cover.py',
                    '--video', str(video_path),
                    '--output-dir', str(self.output_dir)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✅ 封面生成完成 (output/{video_output_dir.name}/)")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 封面生成失败: {e.stderr}")
            return False
    
    def backup_files(self, video_path: Path, related_files: List[Path]):
        """
        备份所有相关文件
        
        Args:
            video_path: 视频文件
            related_files: 相关文件列表
        """
        logger.info(f"💾 备份文件...")
        
        # 创建备份子目录（按日期）
        date_str = datetime.now().strftime("%Y-%m-%d")
        backup_subdir = self.backup_dir / date_str / video_path.stem
        backup_subdir.mkdir(parents=True, exist_ok=True)
        
        # 备份所有文件
        all_files = [video_path] + related_files
        
        for file_path in all_files:
            if file_path and file_path.exists():
                try:
                    dest = backup_subdir / file_path.name
                    shutil.copy2(file_path, dest)
                    logger.info(f"   ✓ {file_path.name}")
                except Exception as e:
                    logger.error(f"   ✗ 备份失败 {file_path.name}: {e}")
        
        # 备份封面（如果有）
        cover_dir = self.output_dir / video_path.stem
        if cover_dir.exists():
            try:
                cover_backup_dir = backup_subdir / "covers"
                shutil.copytree(cover_dir, cover_backup_dir, dirs_exist_ok=True)
                logger.info(f"   ✓ covers/")
            except Exception as e:
                logger.error(f"   ✗ 备份封面失败: {e}")
        
        logger.info(f"✅ 备份完成: {backup_subdir}")
        
        # 备份后删除 data 目录中的原文件（如果配置启用）
        if self.config['auto_process'].get('delete_after_backup', False):
            logger.info("")
            logger.info(f"🗑️  清理 data 目录中的原文件...")
            
            files_to_delete = []
            
            # 只删除 data 目录下的文件
            for file_path in all_files:
                if file_path and file_path.exists():
                    # 检查文件是否在 data 目录下
                    try:
                        file_path.relative_to(self.data_dir)
                        files_to_delete.append(file_path)
                    except ValueError:
                        # 文件不在 data 目录，不删除
                        continue
            
            # 删除文件
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    logger.info(f"   ✓ 已删除: {file_path.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"   ✗ 删除失败 {file_path.name}: {e}")
            
            if deleted_count > 0:
                logger.info(f"✅ 已清理 {deleted_count} 个文件，节省空间")
            else:
                logger.info(f"ℹ️  没有需要删除的文件")
    
    def process_video(
        self,
        video_path: Path,
        en_subtitle: Optional[Path],
        zh_subtitle: Optional[Path]
    ) -> bool:
        """
        处理单个视频
        
        Returns:
            是否成功
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"🎬 开始处理: {video_path.name}")
        logger.info("=" * 70)
        
        # 创建视频专属输出目录
        video_name = video_path.stem
        video_output_dir = self.output_dir / video_name
        video_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 输出目录: {video_output_dir}")
        logger.info("")
        
        related_files = []
        
        try:
            # 1. 检查字幕
            if not en_subtitle:
                logger.warning(f"⚠️  没有英文字幕，跳过字幕处理")
            else:
                related_files.append(en_subtitle)
                
                # 2. 翻译字幕（如果需要）
                if zh_subtitle:
                    logger.info(f"✓ 已有中文字幕，跳过翻译: {zh_subtitle.name}")
                    related_files.append(zh_subtitle)
                else:
                    logger.info(f"📝 开始翻译字幕...")
                    zh_subtitle = self.translate_subtitle(en_subtitle)
                    
                    if not zh_subtitle:
                        logger.error("❌ 翻译失败，跳过后续步骤")
                        return False
                    
                    related_files.append(zh_subtitle)
                
                # 3. 合并字幕到视频（输出到 output/视频名/）
                logger.info("")
                output_video = self.merge_subtitles(video_path, en_subtitle, zh_subtitle, video_output_dir)
                
                if output_video:
                    related_files.append(output_video)
                    
                    # 生成的 SRT 文件（也在 output/视频名/ 目录）
                    srt_file = video_output_dir / f"{output_video.stem}.srt"
                    if srt_file.exists():
                        related_files.append(srt_file)
            
            # 4. 生成单独的 SRT 文件（适合 B站等平台，输出到 output/视频名/）
            if en_subtitle and zh_subtitle and self.config['auto_process'].get('generate_bilibili_subtitles', True):
                logger.info("")
                logger.info(f"📝 生成B站字幕文件...")
                
                try:
                    # 生成中文 SRT
                    zh_srt = video_output_dir / f"{video_name}_zh.srt"
                    subprocess.run(
                        ['python', 'src/vtt_to_srt.py', '--input', str(zh_subtitle), '--output', str(zh_srt)],
                        capture_output=True,
                        check=True
                    )
                    related_files.append(zh_srt)
                    
                    # 生成英文 SRT
                    en_srt = video_output_dir / f"{video_name}_en.srt"
                    subprocess.run(
                        ['python', 'src/vtt_to_srt.py', '--input', str(en_subtitle), '--output', str(en_srt)],
                        capture_output=True,
                        check=True
                    )
                    related_files.append(en_srt)
                    
                    logger.info(f"✅ B站字幕文件已生成（output/{video_name}/）")
                    
                except Exception as e:
                    logger.warning(f"⚠️  B站字幕生成失败: {e}")
            
            # 5. 生成封面（输出到 output/视频名/）
            if self.config['auto_process'].get('generate_covers', True):
                logger.info("")
                self.generate_covers(video_path, video_output_dir)
            
            # 5. 备份所有文件
            logger.info("")
            self.backup_files(video_path, related_files)
            
            # 6. 更新状态（只有成功生成文件才标记为已处理）
            if related_files:
                self.state['processed_videos'][video_path.name] = {
                    'processed_at': datetime.now().isoformat(),
                    'files': [str(f) for f in related_files]
                }
                self.save_state()
                logger.info(f"✅ 状态已保存（{len(related_files)} 个文件）")
                
                logger.info("")
                logger.info("=" * 70)
                logger.info(f"✅ 处理完成: {video_path.name}")
                logger.info("=" * 70)
                logger.info("")
                
                return True
            else:
                logger.warning(f"⚠️  没有生成任何文件，处理失败")
                
                logger.info("")
                logger.info("=" * 70)
                logger.info(f"❌ 处理失败: {video_path.name}")
                logger.info("=" * 70)
                logger.info("")
                
                return False
            
        except Exception as e:
            logger.error(f"❌ 处理失败: {e}")
            logger.exception("详细错误:")
            return False
    
    def run_once(self) -> int:
        """
        执行一次扫描和处理
        
        Returns:
            处理的视频数量
        """
        logger.info("")
        logger.info("━" * 70)
        logger.info("🔍 扫描视频文件...")
        logger.info(f"   目录: {self.data_dir}")
        logger.info("━" * 70)
        
        videos = self.find_videos()
        
        if not videos:
            logger.info("✓ 没有需要处理的视频")
            return 0
        
        logger.info(f"找到 {len(videos)} 个待处理视频:")
        for video, en_sub, zh_sub in videos:
            status = []
            if en_sub:
                status.append("✓英文字幕")
            if zh_sub:
                status.append("✓中文字幕")
            logger.info(f"  • {video.name} [{', '.join(status) if status else '无字幕'}]")
        
        logger.info("")
        
        # 处理每个视频
        processed_count = 0
        for video, en_sub, zh_sub in videos:
            success = self.process_video(video, en_sub, zh_sub)
            if success:
                processed_count += 1
            
            # 短暂休息，避免过载
            time.sleep(2)
        
        logger.info("")
        logger.info("━" * 70)
        logger.info(f"✨ 本次处理完成，共处理 {processed_count}/{len(videos)} 个视频")
        logger.info("━" * 70)
        logger.info("")
        
        return processed_count
    
    def run_continuous(self):
        """持续监控模式"""
        logger.info("")
        logger.info("🤖 启动视频自动处理系统")
        logger.info(f"   数据目录: {self.data_dir}")
        logger.info(f"   备份目录: {self.backup_dir}")
        logger.info(f"   检查间隔: {self.check_interval} 秒")
        logger.info(f"   按 Ctrl+C 停止")
        logger.info("")
        
        try:
            while True:
                self.run_once()
                
                logger.info(f"⏱️  等待 {self.check_interval} 秒后进行下一次检查...")
                logger.info("")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("")
            logger.info("👋 收到停止信号，正在退出...")
            logger.info("")
    
    def show_status(self):
        """显示处理状态"""
        logger.info("")
        logger.info("📊 处理状态")
        logger.info("=" * 70)
        
        if not self.state['processed_videos']:
            logger.info("   还没有处理过任何视频")
        else:
            logger.info(f"   已处理视频数量: {len(self.state['processed_videos'])}")
            logger.info("")
            logger.info("   已处理的视频:")
            for video_name, info in self.state['processed_videos'].items():
                logger.info(f"   • {video_name}")
                logger.info(f"     处理时间: {info['processed_at']}")
        
        logger.info("")
        logger.info("   待处理视频:")
        videos = self.find_videos()
        if not videos:
            logger.info("   无待处理视频")
        else:
            for video, en_sub, zh_sub in videos:
                status = []
                if en_sub:
                    status.append("✓英文字幕")
                if zh_sub:
                    status.append("✓中文字幕")
                logger.info(f"   • {video.name} [{', '.join(status) if status else '无字幕'}]")
        
        logger.info("=" * 70)
        logger.info("")


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🤖 视频自动处理系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 执行一次扫描和处理
  python auto_process_videos.py

  # 2. 持续监控模式（推荐）
  python auto_process_videos.py --watch

  # 3. 查看处理状态
  python auto_process_videos.py --status

  # 4. 自定义检查间隔（持续模式）
  python auto_process_videos.py --watch --interval 120

  # 5. 指定数据目录
  python auto_process_videos.py --data-dir /path/to/data

💡 工作流程:
  1. 扫描 data 目录中的视频文件
  2. 检查视频是否下载完成（文件未在修改中）
  3. 检查是否已有中文字幕（.zh.vtt）
  4. 如果没有中文字幕，自动翻译
  5. 合并中英文字幕到视频（软字幕）
  6. 生成封面（4种配色）
  7. 备份所有文件到 data/backup/<日期>/<视频名>/
  8. 记录处理状态，避免重复处理

🎯 特点:
  - ✅ 自动检测视频下载完成
  - ✅ 智能跳过已有中文字幕
  - ✅ 自动备份所有相关文件
  - ✅ 避免重复处理
  - ✅ 持续监控新视频
        """
    )
    
    parser.add_argument(
        '--data-dir', '-d',
        default='../data',
        help='数据目录路径（默认: ../data）'
    )
    parser.add_argument(
        '--backup-dir', '-b',
        default='../data/backup',
        help='备份目录路径（默认: ../data/backup）'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='../output',
        help='输出目录路径（默认: ../output）'
    )
    parser.add_argument(
        '--watch', '-w',
        action='store_true',
        help='持续监控模式'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=60,
        help='检查间隔秒数（默认: 60）'
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='显示处理状态'
    )
    
    args = parser.parse_args()
    
    # 检查是否在 vedio-tools 目录
    if not Path('src/subtitle_translator_smart.py').exists():
        logger.error("❌ 请在 vedio-tools 目录下运行此脚本")
        logger.error("   当前目录应该包含 src/ 目录")
        return 1
    
    # 创建处理器
    processor = VideoProcessor(
        data_dir=args.data_dir,
        backup_dir=args.backup_dir,
        output_dir=args.output_dir,
        check_interval=args.interval
    )
    
    # 执行操作
    if args.status:
        processor.show_status()
    elif args.watch:
        processor.run_continuous()
    else:
        processor.run_once()
    
    return 0


if __name__ == '__main__':
    exit(main())


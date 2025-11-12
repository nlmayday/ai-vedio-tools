#!/usr/bin/env python3
"""
视频字幕合并工具
将中英文字幕合并并嵌入到视频中
支持 VTT 和 SRT 格式
"""

import os
import re
import argparse
import subprocess
from pathlib import Path
import logging
from subtitle_parser import parse_subtitle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoSubtitleMerger:
    """视频字幕合并器"""
    
    def __init__(self):
        """初始化"""
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        """检查 ffmpeg 是否安装"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("✅ ffmpeg 已安装")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ ffmpeg 未安装")
            logger.error("请安装 ffmpeg: brew install ffmpeg")
            raise RuntimeError("ffmpeg 未安装")
    
    def parse_subtitle_file(self, subtitle_path: str) -> list:
        """
        解析字幕文件（支持 VTT 和 SRT）
        
        Returns:
            字幕块列表 [{timestamp, start_time, end_time, text}, ...]
        """
        logger.info(f"📖 解析字幕: {subtitle_path}")
        
        # 使用统一解析器
        format_type, blocks = parse_subtitle(subtitle_path)
        
        # 转换为包含 timestamp 的格式（为了兼容性）
        result = []
        for block in blocks:
            timestamp = f"{block['start_time']} --> {block['end_time']}"
            result.append({
                'timestamp': timestamp,
                'start_time': block['start_time'],
                'end_time': block['end_time'],
                'text': block['text']
            })
        
        logger.info(f"✅ 解析完成，共 {len(result)} 个字幕块（格式: {format_type.upper()}）")
        return result
    
    def merge_subtitles(
        self,
        en_blocks: list,
        zh_blocks: list,
        output_srt: str,
        layout: str = 'vertical'
    ):
        """
        合并中英文字幕为 SRT 格式（ffmpeg 更好支持）
        
        Args:
            en_blocks: 英文字幕块
            zh_blocks: 中文字幕块
            output_srt: 输出 SRT 文件路径
            layout: 布局方式 ('vertical' 或 'horizontal')
        """
        logger.info(f"🔄 合并中英文字幕...")
        logger.info(f"   布局方式: {layout}")
        
        # 确保两个字幕数量一致
        min_blocks = min(len(en_blocks), len(zh_blocks))
        if len(en_blocks) != len(zh_blocks):
            logger.warning(f"⚠️  字幕数量不一致: 英文 {len(en_blocks)}, 中文 {len(zh_blocks)}")
            logger.warning(f"   将使用前 {min_blocks} 条")
        
        # 生成 SRT 格式
        srt_content = []
        
        for i in range(min_blocks):
            en_block = en_blocks[i]
            zh_block = zh_blocks[i]
            
            # SRT 序号（从1开始）
            srt_content.append(str(i + 1))
            
            # 时间戳（SRT 格式：00:00:00,000 --> 00:00:00,000）
            start_time = en_block['start_time'].replace('.', ',')
            end_time = en_block['end_time'].replace('.', ',')
            srt_content.append(f"{start_time} --> {end_time}")
            
            # 字幕文本
            if layout == 'vertical':
                # 垂直布局：中文在上，英文在下
                srt_content.append(zh_block['text'])
                srt_content.append(en_block['text'])
            else:
                # 水平布局：并排显示（实际上SRT不支持，会显示两行）
                srt_content.append(f"{zh_block['text']} | {en_block['text']}")
            
            # 空行分隔
            srt_content.append('')
        
        # 保存 SRT 文件
        Path(output_srt).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        
        logger.info(f"✅ 合并字幕已保存: {output_srt}")
        logger.info(f"   共 {min_blocks} 条双语字幕")
    
    def embed_subtitles_soft(
        self,
        video_path: str,
        srt_path: str,
        output_path: str
    ) -> str:
        """
        软字幕：将字幕作为轨道嵌入视频（可开关）
        
        Args:
            video_path: 输入视频路径
            srt_path: SRT 字幕路径
            output_path: 输出视频路径
            
        Returns:
            输出视频路径
        """
        logger.info("📦 嵌入软字幕...")
        logger.info("   (可在播放器中开关字幕)")
        
        # 注意：使用 -map 1:0 而不是 1:s，因为 SRT 文件被识别为流 1:0
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', srt_path,
            '-map', '0:v',  # 映射视频流
            '-map', '0:a',  # 映射音频流  
            '-map', '1:0',  # 映射字幕流（SRT 文件的第一个流）
            '-c:v', 'copy',  # 复制视频流
            '-c:a', 'copy',  # 复制音频流
            '-c:s', 'mov_text',  # 字幕编码为 mov_text（MP4兼容）
            '-metadata:s:s:0', 'language=zh-CN',
            '-metadata:s:s:0', 'title=中英双语',
            '-disposition:s:0', 'default',  # 设置字幕为默认显示
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        logger.info(f"🎬 执行 ffmpeg 命令...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✅ 软字幕嵌入成功: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ ffmpeg 执行失败")
            logger.error(f"   错误: {e.stderr}")
            raise
    
    def embed_subtitles_hard(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        font_size: int = 20,
        font_name: str = 'PingFang SC'
    ) -> str:
        """
        硬字幕：将字幕烧录到视频画面中（无法关闭）
        
        Args:
            video_path: 输入视频路径
            srt_path: SRT 字幕路径
            output_path: 输出视频路径
            font_size: 字体大小
            font_name: 字体名称
            
        Returns:
            输出视频路径
        """
        logger.info("🔥 烧录硬字幕...")
        logger.info("   (字幕将永久显示在视频中)")
        
        # 为了避免路径中的特殊字符（空格、单引号等）导致问题
        # 将 SRT 文件复制到临时路径（无特殊字符）
        import tempfile
        import shutil
        from pathlib import Path
        import os
        
        # 创建临时文件（不自动删除）
        temp_srt_fd, temp_srt_path = tempfile.mkstemp(suffix='.srt', text=True)
        os.close(temp_srt_fd)
        
        # 复制字幕文件到临时路径
        shutil.copy2(srt_path, temp_srt_path)
        logger.info(f"   使用临时字幕文件: {temp_srt_path}")
        
        # 验证临时文件存在
        if not os.path.exists(temp_srt_path):
            raise FileNotFoundError(f"临时字幕文件创建失败: {temp_srt_path}")
        
        try:
            # 简化命令，去掉 force_style，使用默认字体
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'subtitles={temp_srt_path}',
                '-c:a', 'copy',  # 复制音频流
                '-y',
                output_path
            ]
        
            logger.info(f"🎬 执行 ffmpeg 命令...")
            logger.info(f"   字体: {font_name}, 大小: {font_size}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✅ 硬字幕烧录成功: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ ffmpeg 执行失败")
            logger.error(f"   错误: {e.stderr}")
            raise
        finally:
            # 清理临时文件
            import os
            try:
                os.unlink(temp_srt_path)
                logger.info(f"   已清理临时文件")
            except:
                pass
    
    def process_video(
        self,
        video_path: str,
        en_subtitle_path: str,
        zh_subtitle_path: str,
        output_path: str = None,
        subtitle_type: str = 'soft',
        layout: str = 'vertical',
        font_size: int = 20
    ) -> str:
        """
        完整流程：合并字幕并嵌入视频
        
        Args:
            video_path: 视频文件路径
            en_subtitle_path: 英文字幕路径
            zh_subtitle_path: 中文字幕路径
            output_path: 输出视频路径
            subtitle_type: 字幕类型 ('soft' 或 'hard')
            layout: 布局方式 ('vertical' 或 'horizontal')
            font_size: 字体大小（仅硬字幕）
            
        Returns:
            输出视频路径
        """
        logger.info("="*60)
        logger.info("🎬 视频字幕合并工具")
        logger.info("="*60)
        logger.info(f"📹 视频: {video_path}")
        logger.info(f"🇬🇧 英文字幕: {en_subtitle_path}")
        logger.info(f"🇨🇳 中文字幕: {zh_subtitle_path}")
        logger.info(f"📦 字幕类型: {subtitle_type}")
        logger.info("")
        
        # 默认输出路径
        if not output_path:
            video_file = Path(video_path)
            output_name = video_file.stem + f'_bilingual_{subtitle_type}' + video_file.suffix
            output_path = video_file.parent / output_name
        
        # 1. 解析字幕
        en_blocks = self.parse_subtitle_file(en_subtitle_path)
        zh_blocks = self.parse_subtitle_file(zh_subtitle_path)
        
        # 2. 合并字幕为 SRT
        logger.info("")
        temp_srt = Path(output_path).parent / f"{Path(video_path).stem}_bilingual.srt"
        self.merge_subtitles(en_blocks, zh_blocks, str(temp_srt), layout)
        
        # 3. 嵌入字幕
        logger.info("")
        if subtitle_type == 'soft':
            result = self.embed_subtitles_soft(video_path, str(temp_srt), str(output_path))
        else:
            result = self.embed_subtitles_hard(
                video_path,
                str(temp_srt),
                str(output_path),
                font_size=font_size
            )
        
        # 4. 清理临时文件（可选）
        # os.remove(temp_srt)  # 保留 SRT 文件以便后续使用
        
        logger.info("")
        logger.info("="*60)
        logger.info("✨ 处理完成！")
        logger.info("="*60)
        logger.info(f"📁 输出视频: {result}")
        logger.info(f"📄 双语字幕: {temp_srt}")
        logger.info("="*60)
        logger.info("")
        
        return result


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🎬 视频字幕合并工具 - 将中英文字幕嵌入视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 软字幕（推荐，可在播放器中开关）
  python video_subtitle_merger.py \\
    --video video.mp4 \\
    --en-subtitle video.en.vtt \\
    --zh-subtitle video.zh.vtt \\
    --type soft

  # 2. 硬字幕（烧录到画面中）
  python video_subtitle_merger.py \\
    --video video.mp4 \\
    --en-subtitle video.en.vtt \\
    --zh-subtitle video.zh.vtt \\
    --type hard \\
    --font-size 24

  # 3. 指定输出路径
  python video_subtitle_merger.py \\
    --video video.mp4 \\
    --en-subtitle video.en.vtt \\
    --zh-subtitle video.zh.vtt \\
    --output output/video_bilingual.mp4

💡 说明:
  - 软字幕：字幕作为独立轨道，可以在播放器中开关
  - 硬字幕：字幕烧录在画面中，无法关闭，但兼容性更好
  - 中文在上，英文在下的垂直布局
        """
    )
    
    parser.add_argument(
        '--video', '-v',
        required=True,
        help='输入视频文件路径'
    )
    parser.add_argument(
        '--en-subtitle', '-en',
        required=True,
        help='英文字幕文件路径（支持 .vtt 或 .srt）'
    )
    parser.add_argument(
        '--zh-subtitle', '-zh',
        required=True,
        help='中文字幕文件路径（支持 .vtt 或 .srt）'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出视频文件路径（默认自动生成）'
    )
    parser.add_argument(
        '--type', '-t',
        choices=['soft', 'hard'],
        default='soft',
        help='字幕类型：soft（软字幕，可开关）或 hard（硬字幕，烧录）'
    )
    parser.add_argument(
        '--layout', '-l',
        choices=['vertical', 'horizontal'],
        default='vertical',
        help='布局方式（默认: vertical）'
    )
    parser.add_argument(
        '--font-size', '-fs',
        type=int,
        default=20,
        help='字体大小，仅硬字幕有效（默认: 20）'
    )
    
    args = parser.parse_args()
    
    try:
        # 检查输入文件
        for file_path, name in [
            (args.video, '视频文件'),
            (args.en_subtitle, '英文字幕'),
            (args.zh_subtitle, '中文字幕')
        ]:
            if not os.path.exists(file_path):
                print(f"❌ 错误：{name}不存在: {file_path}")
                return 1
        
        # 创建合并器
        merger = VideoSubtitleMerger()
        
        # 处理视频
        output_file = merger.process_video(
            video_path=args.video,
            en_subtitle_path=args.en_subtitle,
            zh_subtitle_path=args.zh_subtitle,
            output_path=args.output,
            subtitle_type=args.type,
            layout=args.layout,
            font_size=args.font_size
        )
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.exception("详细错误信息:")
        return 1


if __name__ == '__main__':
    exit(main())


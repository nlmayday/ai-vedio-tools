#!/usr/bin/env python3
"""
视频封面生成器
支持自动从视频提取关键帧，添加标题和中英双字幕，生成精美封面
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path
import logging
from typing import Optional, Tuple
import os
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """视频封面生成器"""
    
    # 预设的配色方案
    COLOR_SCHEMES = {
        'modern': {
            'gradient_start': (15, 32, 39),      # 深蓝
            'gradient_end': (32, 58, 67),        # 蓝灰
            'title_color': (255, 255, 255),      # 白色
            'title2_color': (64, 224, 208),      # 青色 (与title1区分)
            'subtitle_color': (200, 200, 200),   # 浅灰
            'accent_color': (64, 224, 208),      # 青色
        },
        'vibrant': {
            'gradient_start': (88, 24, 69),      # 深紫
            'gradient_end': (199, 0, 57),        # 红色
            'title_color': (255, 255, 255),
            'title2_color': (255, 215, 0),       # 金色 (与title1区分)
            'subtitle_color': (255, 200, 220),
            'accent_color': (255, 215, 0),       # 金色
        },
        'elegant': {
            'gradient_start': (0, 0, 0),         # 黑色
            'gradient_end': (40, 40, 40),        # 深灰
            'title_color': (255, 215, 0),        # 金色
            'title2_color': (220, 220, 220),     # 浅灰 (与title1区分)
            'subtitle_color': (200, 200, 200),
            'accent_color': (255, 215, 0),
        },
        'fresh': {
            'gradient_start': (0, 102, 204),     # 蓝色
            'gradient_end': (102, 204, 255),     # 浅蓝
            'title_color': (255, 255, 255),
            'title2_color': (255, 215, 0),       # 金色 (与title1区分)
            'subtitle_color': (230, 255, 255),
            'accent_color': (255, 193, 7),       # 橙黄
        }
    }
    
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        color_scheme: str = 'modern'
    ):
        """
        初始化封面生成器
        
        Args:
            width: 封面宽度（像素）
            height: 封面高度（像素）
            color_scheme: 配色方案 ('modern', 'vibrant', 'elegant', 'fresh')
        """
        self.width = width
        self.height = height
        self.color_scheme = self.COLOR_SCHEMES.get(
            color_scheme, 
            self.COLOR_SCHEMES['modern']
        )
        
        # 尝试加载字体
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> dict:
        """加载系统字体"""
        fonts = {}
        
        # macOS 常见中文字体路径
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',              # 苹方
            '/System/Library/Fonts/STHeiti Medium.ttc',         # 黑体
            '/System/Library/Fonts/Supplemental/Arial.ttf',     # Arial
            '/Library/Fonts/Arial Unicode.ttf',
        ]
        
        # 尝试加载不同大小的字体
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    fonts['title'] = ImageFont.truetype(font_path, 120)   # title1 大字体
                    fonts['title2'] = ImageFont.truetype(font_path, 85)   # title2 中等字体 (更小)
                    fonts['subtitle'] = ImageFont.truetype(font_path, 60)
                    fonts['caption'] = ImageFont.truetype(font_path, 40)
                    logger.info(f"✅ 成功加载字体: {font_path}")
                    break
                except Exception as e:
                    logger.warning(f"⚠️  加载字体失败 {font_path}: {e}")
        
        # 如果没有找到字体，使用默认字体
        if not fonts:
            logger.warning("⚠️  未找到系统字体，使用默认字体")
            fonts['title'] = ImageFont.load_default()
            fonts['title2'] = ImageFont.load_default()
            fonts['subtitle'] = ImageFont.load_default()
            fonts['caption'] = ImageFont.load_default()
        
        return fonts
    
    def extract_frame(
        self,
        video_path: str,
        frame_position: float = 0.3
    ) -> Optional[Image.Image]:
        """
        从视频中提取一帧
        
        Args:
            video_path: 视频文件路径
            frame_position: 提取位置（0.0-1.0），0.3表示30%处
            
        Returns:
            PIL Image 对象，失败返回 None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"❌ 无法打开视频文件: {video_path}")
                return None
            
            # 获取视频总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = int(total_frames * frame_position)
            
            # 定位到目标帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error("❌ 无法读取视频帧")
                return None
            
            # 转换 BGR 到 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            logger.info(f"✅ 成功提取视频帧 (位置: {frame_position*100:.0f}%)")
            return Image.fromarray(frame_rgb)
            
        except Exception as e:
            logger.error(f"❌ 提取视频帧失败: {e}")
            return None
    
    def create_gradient_background(self) -> Image.Image:
        """创建渐变背景"""
        gradient = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(gradient)
        
        start_color = self.color_scheme['gradient_start']
        end_color = self.color_scheme['gradient_end']
        
        # 垂直渐变
        for y in range(self.height):
            ratio = y / self.height
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        return gradient

    def load_background_image(self, image_path: str) -> Image.Image:
        """加载背景图片"""
        try:
            background = Image.open(image_path).convert('RGB')
            # 调整图片大小以适应封面尺寸
            background = background.resize((self.width, self.height), Image.Resampling.LANCZOS)

            # 应用与视频帧相同的处理效果
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.85)  # 提高到0.85，接近原始亮度
            enhancer = ImageEnhance.Contrast(background)
            background = enhancer.enhance(1.1)  # 略微增强对比度
            background = background.filter(ImageFilter.GaussianBlur(radius=1.5))  # 降到1.5，非常轻微

            logger.info(f"📸 使用背景图片: {image_path}")
            return background
        except Exception as e:
            logger.error(f"❌ 加载背景图片失败 {image_path}: {e}")
            raise

    def add_text_with_shadow(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int],
        shadow_offset: int = 4
    ):
        """添加带阴影的文字"""
        x, y = position
        
        # 绘制阴影
        shadow_color = (0, 0, 0, 180)
        draw.text(
            (x + shadow_offset, y + shadow_offset),
            text,
            font=font,
            fill=shadow_color
        )
        
        # 绘制文字
        draw.text((x, y), text, font=font, fill=color)
    
    def add_accent_line(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        width: int,
        height: int = 6
    ):
        """添加装饰线条"""
        x, y = position
        color = self.color_scheme['accent_color']
        draw.rectangle(
            [x, y, x + width, y + height],
            fill=color
        )
    
    def generate_thumbnail(
        self,
        video_path: Optional[str] = None,
        title_line1: str = "",
        title_line2: str = "",
        subtitle_cn: str = "",
        subtitle_en: str = "",
        output_path: str = "thumbnail.jpg",
        frame_position: float = 0.3,
        use_video_background: bool = True
    ) -> str:
        """
        生成视频封面
        
        Args:
            video_path: 视频文件路径（可选）
            title_line1: 主标题第一行
            title_line2: 主标题第二行
            subtitle_cn: 中文字幕
            subtitle_en: 英文字幕
            output_path: 输出文件路径
            frame_position: 视频帧提取位置（0.0-1.0）
            use_video_background: 是否使用视频帧作为背景
            
        Returns:
            生成的封面文件路径
        """
        logger.info("🎬 开始生成视频封面...")
        
        # 创建基础画布
        if use_video_background and video_path:
            # 使用视频帧作为背景
            background = self.extract_frame(video_path, frame_position)
            if background:
                # 调整大小
                background = background.resize((self.width, self.height), Image.Resampling.LANCZOS)
                # 基本保持原始亮度，让视频内容清晰可见
                enhancer = ImageEnhance.Brightness(background)
                background = enhancer.enhance(0.85)  # 提高到0.85，接近原始亮度
                enhancer = ImageEnhance.Contrast(background)
                background = enhancer.enhance(1.1)  # 略微增强对比度
                # 极轻微模糊，保持清晰
                background = background.filter(ImageFilter.GaussianBlur(radius=1.5))  # 降到1.5，非常轻微
            else:
                logger.warning("⚠️  视频帧提取失败，使用渐变背景")
                background = self.create_gradient_background()
        else:
            background = self.create_gradient_background()
        
        # 创建半透明遮罩层
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # 添加极轻度遮罩，仅轻微增强文字对比度
        overlay_draw.rectangle(
            [(0, 0), (self.width, self.height)],
            fill=(0, 0, 0, 40)  # 降到40，非常透明，视频内容清晰可见
        )
        
        # 合并背景和遮罩
        background = background.convert('RGBA')
        thumbnail = Image.alpha_composite(background, overlay)
        thumbnail = thumbnail.convert('RGB')
        
        # 在缩略图上绘制
        draw = ImageDraw.Draw(thumbnail)
        
        # 计算布局
        center_x = self.width // 2
        
        # 添加装饰线条（顶部）
        self.add_accent_line(
            draw,
            (center_x - 200, 250),
            400,
            8
        )
        
        # 添加主标题
        y_offset = 320
        if title_line1:
            # 计算文字宽度以居中
            bbox = draw.textbbox((0, 0), title_line1, font=self.fonts['title'])
            text_width = bbox[2] - bbox[0]
            x = center_x - text_width // 2
            
            self.add_text_with_shadow(
                draw,
                title_line1,
                (x, y_offset),
                self.fonts['title'],
                self.color_scheme['title_color'],
                shadow_offset=6
            )
            y_offset += 140
        
        if title_line2:
            bbox = draw.textbbox((0, 0), title_line2, font=self.fonts['title2'])
            text_width = bbox[2] - bbox[0]
            x = center_x - text_width // 2
            
            self.add_text_with_shadow(
                draw,
                title_line2,
                (x, y_offset),
                self.fonts['title2'],
                self.color_scheme.get('title2_color', self.color_scheme['title_color']),
                shadow_offset=5
            )
            y_offset += 130
        
        # 添加装饰线条（中间）
        self.add_accent_line(
            draw,
            (center_x - 150, y_offset),
            300,
            4
        )
        y_offset += 40
        
        # 添加中文字幕
        if subtitle_cn:
            bbox = draw.textbbox((0, 0), subtitle_cn, font=self.fonts['subtitle'])
            text_width = bbox[2] - bbox[0]
            x = center_x - text_width // 2
            
            self.add_text_with_shadow(
                draw,
                subtitle_cn,
                (x, y_offset),
                self.fonts['subtitle'],
                self.color_scheme['subtitle_color'],
                shadow_offset=4
            )
            y_offset += 80
        
        # 添加英文字幕
        if subtitle_en:
            bbox = draw.textbbox((0, 0), subtitle_en, font=self.fonts['caption'])
            text_width = bbox[2] - bbox[0]
            x = center_x - text_width // 2
            
            self.add_text_with_shadow(
                draw,
                subtitle_en,
                (x, y_offset),
                self.fonts['caption'],
                self.color_scheme['subtitle_color'],
                shadow_offset=3
            )
        
        # 添加边框效果
        border_width = 10
        draw.rectangle(
            [border_width, border_width, 
             self.width - border_width, self.height - border_width],
            outline=self.color_scheme['accent_color'],
            width=border_width
        )
        
        # 保存封面
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        thumbnail.save(str(output_path), quality=95, optimize=True)
        logger.info(f"✅ 封面生成成功: {output_path}")
        
        return str(output_path)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🎬 视频封面生成器 - 自动生成精美的视频封面',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 使用视频背景 + 双标题
  python thumbnail_generator.py \\
    --video input.mp4 \\
    --title1 "人工智能" \\
    --title2 "改变未来" \\
    --output cover.jpg
  
  # 2. 中英双字幕
  python thumbnail_generator.py \\
    --video input.mp4 \\
    --title1 "AI Video Tools" \\
    --subtitle-cn "智能视频处理工具" \\
    --subtitle-en "Intelligent Video Processing Tools" \\
    --output cover.jpg
  
  # 3. 使用渐变背景（不用视频）
  python thumbnail_generator.py \\
    --title1 "精彩内容" \\
    --title2 "即将开始" \\
    --scheme vibrant \\
    --no-video-bg \\
    --output cover.jpg

🎨 配色方案:
  - modern: 现代风格（深蓝色）- 适合科技/教育
  - vibrant: 活力风格（紫红色）- 适合娱乐/创意
  - elegant: 优雅风格（黑金色）- 适合高端/艺术
  - fresh: 清新风格（蓝色）- 适合生活/旅行
        """
    )
    
    parser.add_argument(
        '--video', '-v',
        help='视频文件路径'
    )
    parser.add_argument(
        '--background-image', '-bi',
        help='背景图片文件路径（替代视频帧或渐变背景）'
    )
    parser.add_argument(
        '--title1', '-t1',
        default='',
        help='主标题第一行'
    )
    parser.add_argument(
        '--title2', '-t2',
        default='',
        help='主标题第二行'
    )
    parser.add_argument(
        '--subtitle-cn', '-scn',
        default='',
        help='中文字幕'
    )
    parser.add_argument(
        '--subtitle-en', '-sen',
        default='',
        help='英文字幕'
    )
    parser.add_argument(
        '--output', '-o',
        default='../output/thumbnail.jpg',
        help='输出文件路径（默认: ../output/thumbnail.jpg）'
    )
    parser.add_argument(
        '--frame-position', '-fp',
        type=float,
        default=0.3,
        help='视频帧提取位置 0.0-1.0（默认: 0.3，即30%%位置）'
    )
    parser.add_argument(
        '--width', '-w',
        type=int,
        default=1920,
        help='封面宽度（默认: 1920）'
    )
    parser.add_argument(
        '--height', '-ht',
        type=int,
        default=1080,
        help='封面高度（默认: 1080）'
    )
    parser.add_argument(
        '--scheme', '-s',
        choices=['modern', 'vibrant', 'elegant', 'fresh'],
        default='modern',
        help='配色方案（默认: modern）'
    )
    parser.add_argument(
        '--no-video-bg',
        action='store_true',
        help='不使用视频帧作为背景，使用渐变背景'
    )
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = ThumbnailGenerator(
        width=args.width,
        height=args.height,
        color_scheme=args.scheme
    )
    
    # 生成封面
    try:
        output_file = generator.generate_thumbnail(
            video_path=args.video,
            title_line1=args.title1,
            title_line2=args.title2,
            subtitle_cn=args.subtitle_cn,
            subtitle_en=args.subtitle_en,
            output_path=args.output,
            frame_position=args.frame_position,
            use_video_background=not args.no_video_bg
        )
        
        print(f"\n{'='*60}")
        print(f"✨ 封面生成成功！")
        print(f"{'='*60}")
        print(f"📁 输出文件: {output_file}")
        print(f"📐 尺寸: {args.width}x{args.height}")
        print(f"🎨 配色: {args.scheme}")
        if args.video and not args.no_video_bg:
            print(f"🎞️  视频帧位置: {args.frame_position*100:.0f}%")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"❌ 生成封面失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())


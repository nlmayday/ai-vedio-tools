#!/usr/bin/env python3
"""
从图片生成封面
支持使用现有图片作为背景，添加标题和字幕
"""

# import cv2  # Not used in this script
# import numpy as np  # Not used in this script
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path
import logging
from typing import Optional, Tuple
import os
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageToCoverGenerator:
    """从图片生成封面"""

    # 预设的配色方案
    COLOR_SCHEMES = {
        'modern': {
            'gradient_start': (15, 32, 39),      # 深蓝
            'gradient_end': (32, 58, 67),        # 蓝灰
            'title_color': (255, 255, 255),      # 白色
            'subtitle_color': (200, 200, 200),   # 浅灰
            'accent_color': (64, 224, 208),      # 青色
        },
        'vibrant': {
            'gradient_start': (88, 24, 69),      # 深紫
            'gradient_end': (199, 0, 57),        # 红色
            'title_color': (255, 255, 255),
            'subtitle_color': (255, 200, 220),
            'accent_color': (255, 215, 0),       # 金色
        },
        'elegant': {
            'gradient_start': (0, 0, 0),         # 黑色
            'gradient_end': (40, 40, 40),        # 深灰
            'title_color': (255, 215, 0),        # 金色
            'subtitle_color': (200, 200, 200),
            'accent_color': (255, 215, 0),
        },
        'fresh': {
            'gradient_start': (0, 102, 204),     # 蓝色
            'gradient_end': (102, 204, 255),     # 浅蓝
            'title_color': (255, 255, 255),
            'subtitle_color': (230, 255, 255),
            'accent_color': (255, 215, 0),
        },
    }

    def __init__(self, width: int = 1920, height: int = 1080, scheme: str = 'modern'):
        """
        初始化生成器

        Args:
            width: 封面宽度
            height: 封面高度
            scheme: 配色方案
        """
        self.width = width
        self.height = height
        self.color_scheme = self.COLOR_SCHEMES.get(scheme, self.COLOR_SCHEMES['modern'])

        # 尝试加载中文字体
        self.font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # Linux
            'C:/Windows/Fonts/msyh.ttc',  # Windows
            'C:/Windows/Fonts/simhei.ttf',  # Windows 备选
        ]

        self.title_font = None
        self.subtitle_font = None
        self.load_fonts()

    def load_fonts(self):
        """加载字体"""
        font_size_title = int(self.height * 0.08)  # 标题字体大小
        font_size_subtitle = int(self.height * 0.04)  # 字幕字体大小

        # 尝试加载中文字体
        for font_path in self.font_paths:
            if os.path.exists(font_path):
                try:
                    self.title_font = ImageFont.truetype(font_path, font_size_title)
                    self.subtitle_font = ImageFont.truetype(font_path, font_size_subtitle)
                    logger.info(f"✅ 加载字体: {font_path}")
                    return
                except:
                    continue

        # 如果中文字体加载失败，使用默认字体
        logger.warning("⚠️  未找到中文字体，使用默认字体")
        self.title_font = ImageFont.load_default()
        self.subtitle_font = ImageFont.load_default()

    def load_background_image(self, image_path: str) -> Image.Image:
        """加载背景图片"""
        try:
            background = Image.open(image_path).convert('RGB')

            # 计算缩放比例，保持宽高比
            img_ratio = background.width / background.height
            canvas_ratio = self.width / self.height

            if img_ratio > canvas_ratio:
                # 图片更宽，以高度为准
                new_height = self.height
                new_width = int(self.height * img_ratio)
            else:
                # 图片更高，以宽度为准
                new_width = self.width
                new_height = int(self.width / img_ratio)

            # 缩放图片
            background = background.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 如果需要，居中裁剪
            if new_width > self.width:
                left = (new_width - self.width) // 2
                background = background.crop((left, 0, left + self.width, self.height))
            elif new_height > self.height:
                top = (new_height - self.height) // 2
                background = background.crop((0, top, self.width, top + self.height))

            # 应用美化效果
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.9)  # 轻微提亮
            enhancer = ImageEnhance.Contrast(background)
            background = enhancer.enhance(1.05)  # 轻微增强对比度
            background = background.filter(ImageFilter.GaussianBlur(radius=1.0))  # 轻微模糊

            logger.info(f"📸 加载背景图片: {image_path}")
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
        shadow_color: Tuple[int, int, int] = (0, 0, 0),
        shadow_offset: int = 2
    ):
        """添加带阴影的文字"""
        # 绘制阴影
        shadow_position = (position[0] + shadow_offset, position[1] + shadow_offset)
        draw.text(shadow_position, text, font=font, fill=shadow_color)

        # 绘制文字
        draw.text(position, text, font=font, fill=color)

    def create_overlay(self, title1: str, title2: str, subtitle_cn: str, subtitle_en: str) -> Image.Image:
        """创建文字遮罩层"""
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 计算文字位置
        center_x = self.width // 2
        center_y = self.height // 2

        # 主标题第一行
        if title1:
            bbox = draw.textbbox((0, 0), title1, font=self.title_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            title1_y = center_y - text_height * 1.5
            self.add_text_with_shadow(
                draw, title1,
                (center_x - text_width // 2, title1_y),
                self.title_font, self.color_scheme['title_color']
            )

        # 主标题第二行
        if title2:
            bbox = draw.textbbox((0, 0), title2, font=self.title_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            title2_y = center_y - text_height * 0.5
            self.add_text_with_shadow(
                draw, title2,
                (center_x - text_width // 2, title2_y),
                self.title_font, self.color_scheme['title_color']
            )

        # 中文字幕
        if subtitle_cn:
            bbox = draw.textbbox((0, 0), subtitle_cn, font=self.subtitle_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            cn_y = center_y + text_height * 2
            self.add_text_with_shadow(
                draw, subtitle_cn,
                (center_x - text_width // 2, cn_y),
                self.subtitle_font, self.color_scheme['subtitle_color']
            )

        # 英文字幕
        if subtitle_en:
            bbox = draw.textbbox((0, 0), subtitle_en, font=self.subtitle_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            en_y = center_y + text_height * 3.5
            self.add_text_with_shadow(
                draw, subtitle_en,
                (center_x - text_width // 2, en_y),
                self.subtitle_font, self.color_scheme['subtitle_color']
            )

        return overlay

    def generate_cover(
        self,
        image_path: str,
        title1: str = "",
        title2: str = "",
        subtitle_cn: str = "",
        subtitle_en: str = "",
        output_path: str = "cover.jpg"
    ) -> str:
        """
        从图片生成封面

        Args:
            image_path: 背景图片路径
            title1: 主标题第一行
            title2: 主标题第二行
            subtitle_cn: 中文字幕
            subtitle_en: 英文字幕
            output_path: 输出文件路径

        Returns:
            生成的封面文件路径
        """
        logger.info("🎨 开始从图片生成封面...")

        # 检查输入文件
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"背景图片不存在: {image_path}")

        # 加载背景图片
        background = self.load_background_image(image_path)

        # 创建文字遮罩层
        overlay = self.create_overlay(title1, title2, subtitle_cn, subtitle_en)

        # 合并背景和文字
        background = background.convert('RGBA')
        result = Image.alpha_composite(background, overlay)

        # 转换为RGB并保存
        result = result.convert('RGB')

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        result.save(output_path, 'JPEG', quality=95)
        logger.info(f"✅ 封面已生成: {output_path}")

        return output_path


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='🖼️ 从图片生成封面 - 使用现有图片作为背景',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 使用示例:

  # 1. 基本用法
  python image_to_cover.py --image background.jpg --title1 "精彩内容"

  # 2. 双标题
  python image_to_cover.py \\
    --image background.jpg \\
    --title1 "人工智能" \\
    --title2 "改变未来"

  # 3. 中英双字幕
  python image_to_cover.py \\
    --image background.jpg \\
    --title1 "AI Tools" \\
    --subtitle-cn "智能工具集" \\
    --subtitle-en "Intelligent Tool Collection"

  # 4. 指定配色方案
  python image_to_cover.py \\
    --image background.jpg \\
    --title1 "精彩内容" \\
    --scheme vibrant \\
    --output my_cover.jpg

🎨 配色方案:
  - modern: 现代风格（深蓝色）- 适合科技/教育
  - vibrant: 活力风格（紫红色）- 适合娱乐/创意
  - elegant: 优雅风格（黑金色）- 适合高端/艺术
  - fresh: 清新风格（蓝色）- 适合生活/旅行

💡 支持的图片格式: JPG, PNG, BMP, WebP 等
        """
    )

    parser.add_argument(
        '--image', '-i',
        required=True,
        help='背景图片文件路径'
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
        default='cover.jpg',
        help='输出文件路径（默认: cover.jpg）'
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

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🖼️  从图片生成封面")
    print("="*60)

    try:
        # 创建生成器
        generator = ImageToCoverGenerator(
            width=args.width,
            height=args.height,
            scheme=args.scheme
        )

        # 生成封面
        output_path = generator.generate_cover(
            image_path=args.image,
            title1=args.title1,
            title2=args.title2,
            subtitle_cn=args.subtitle_cn,
            subtitle_en=args.subtitle_en,
            output_path=args.output
        )

        print("\n" + "="*60)
        print("✅ 生成完成！")
        print(f"📁 输出文件: {output_path}")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
B站视频自动上传工具

使用 MCP Playwright 自动化上传视频到B站
需要先手动登录B站，脚本会复用浏览器会话

Usage:
    python src/bilibili_uploader.py --video-dir "../output/视频名/"
    
    或使用快捷脚本：
    ./upload_bilibili.sh "../output/视频名/"
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BilibiliUploader:
    """B站视频上传器"""
    
    def __init__(self, video_dir: str):
        """
        初始化上传器
        
        Args:
            video_dir: 视频输出目录（包含视频、封面、cover_texts.json）
        """
        self.video_dir = Path(video_dir).absolute()
        if not self.video_dir.exists():
            raise FileNotFoundError(f"目录不存在: {video_dir}")
        
        # 查找所需文件
        self.video_file = self._find_video_file()
        self.cover_file = self._find_cover_file()
        self.info_file = self.video_dir / "cover_texts.json"
        
        # 加载B站信息
        self.bilibili_info = self._load_bilibili_info()
        
        logger.info(f"📁 工作目录: {self.video_dir}")
        logger.info(f"🎬 视频文件: {self.video_file.name}")
        logger.info(f"🖼️  封面文件: {self.cover_file.name}")
        logger.info(f"📝 标题: {self.bilibili_info['title']}")
        logger.info(f"🏷️  标签: {', '.join(self.bilibili_info['tags'][:3])}...")
    
    def _find_video_file(self) -> Path:
        """查找视频文件（优先软字幕版本）"""
        # 优先级：soft > hard > bilingual > 原视频
        patterns = [
            "*_soft.mp4",
            "*_hard.mp4", 
            "*_bilingual.mp4",
            "*.mp4",
            "*.webm"
        ]
        
        for pattern in patterns:
            files = list(self.video_dir.glob(pattern))
            if files:
                return files[0]
        
        raise FileNotFoundError(f"未找到视频文件: {self.video_dir}")
    
    def _find_cover_file(self) -> Path:
        """查找封面文件（modern 方案）"""
        cover_file = self.video_dir / "cover_modern.png"
        if cover_file.exists():
            return cover_file
        
        # 如果没有 modern，找任意封面
        covers = list(self.video_dir.glob("cover_*.png"))
        if covers:
            logger.warning(f"⚠️  未找到 modern 封面，使用: {covers[0].name}")
            return covers[0]
        
        raise FileNotFoundError(f"未找到封面文件: {self.video_dir}")
    
    def _load_bilibili_info(self) -> Dict:
        """加载B站信息"""
        if not self.info_file.exists():
            raise FileNotFoundError(f"未找到信息文件: {self.info_file}")
        
        with open(self.info_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'title': data.get('bilibili_title', '未命名视频'),
            'tags': data.get('bilibili_tags', []),
            'description': data.get('bilibili_description', '')
        }
    
    def upload(self):
        """
        执行上传流程
        
        注意：这个方法需要通过 MCP Playwright 调用
        请使用 upload_bilibili.sh 脚本来执行
        """
        logger.info("=" * 70)
        logger.info("🚀 开始B站上传流程")
        logger.info("=" * 70)
        
        # 打印上传信息
        logger.info("\n📋 上传信息预览：")
        logger.info(f"   视频: {self.video_file}")
        logger.info(f"   封面: {self.cover_file}")
        logger.info(f"   标题: {self.bilibili_info['title']}")
        logger.info(f"   标签: {', '.join(self.bilibili_info['tags'])}")
        logger.info(f"   简介: {self.bilibili_info['description'][:100]}...")
        logger.info("")
        
        # 生成 MCP Playwright 操作步骤
        steps = self._generate_upload_steps()
        
        logger.info("✅ 上传信息准备完毕")
        logger.info("")
        logger.info("📝 请使用以下步骤手动执行（或通过 upload_bilibili.sh）：")
        logger.info("")
        for i, step in enumerate(steps, 1):
            logger.info(f"{i}. {step}")
        
        return {
            'video': str(self.video_file),
            'cover': str(self.cover_file),
            'info': self.bilibili_info,
            'steps': steps
        }
    
    def _generate_upload_steps(self) -> List[str]:
        """生成上传步骤说明"""
        return [
            "打开 B站创作中心: https://member.bilibili.com/platform/upload/video/frame",
            f"上传视频文件: {self.video_file}",
            "等待视频上传完成（可能需要几分钟）",
            f"填写标题: {self.bilibili_info['title']}",
            "选择类型: 自制（必须选择！）",
            "选择分区: 动画 > 综合",
            "上传封面图",
            f"删除默认标签，添加标签: {', '.join(self.bilibili_info['tags'][:10])}",
            f"填写简介: {len(self.bilibili_info['description'])} 字",
            "活动选择: 选择第二个活动（如果有）",
            "点击「立即投稿」",
            "等待审核通过"
        ]


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='B站视频自动上传工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 上传指定视频
  python src/bilibili_uploader.py --video-dir "../output/视频名/"
  
  # 使用快捷脚本
  ./upload_bilibili.sh "../output/视频名/"

注意:
  1. 需要先手动在浏览器登录B站
  2. 视频目录需要包含: 视频文件、封面图、cover_texts.json
  3. 默认使用 modern 方案的封面
        """
    )
    
    parser.add_argument(
        '--video-dir',
        required=True,
        help='视频输出目录（包含视频、封面、cover_texts.json）'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅预览，不实际上传'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建上传器
        uploader = BilibiliUploader(args.video_dir)
        
        # 执行上传
        result = uploader.upload()
        
        if args.dry_run:
            logger.info("")
            logger.info("🔍 [预览模式] 未执行实际上传")
        else:
            logger.info("")
            logger.info("=" * 70)
            logger.info("✨ 准备完成！请按照上述步骤操作")
            logger.info("   或运行: ./upload_bilibili.sh 使用自动化脚本")
            logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 上传失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())


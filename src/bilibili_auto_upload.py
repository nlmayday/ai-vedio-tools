#!/usr/bin/env python3
"""
B站自动上传 - MCP Playwright 版本

此脚本配合 Cursor AI + MCP Playwright 使用
用户只需提供视频目录，AI 会调用 MCP Playwright 工具完成上传

使用方法：
    在 Cursor 中告诉 AI：
    
    请帮我上传视频到B站：
    - 视频目录：../output/视频名/
    
    或者：
    
    使用 bilibili_auto_upload.py 上传视频到B站
    - 目录：../output/The Future Mark Zuckerberg Is Trying To Build [oX7OduG1YmI]/
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BilibiliUploadConfig:
    """B站上传配置"""
    
    # B站创作中心URL
    UPLOAD_URL = "https://member.bilibili.com/platform/upload/video/frame"
    
    # 等待时间（秒）
    WAIT_PAGE_LOAD = 3
    WAIT_VIDEO_UPLOAD = 2  # 每次检查间隔
    WAIT_AFTER_ACTION = 1
    
    # 分区配置
    CATEGORY = "动画"  # 或根据视频类型选择其他分区
    
    def __init__(self, video_dir: str):
        """初始化配置"""
        self.video_dir = Path(video_dir).absolute()
        
        # 查找文件
        self.video_file = self._find_video_file()
        self.cover_file = self._find_cover_file()
        self.info = self._load_info()
        
        logger.info(f"✅ 配置加载完成")
        logger.info(f"   视频: {self.video_file.name}")
        logger.info(f"   封面: {self.cover_file.name}")
        logger.info(f"   标题: {self.info['title']}")
    
    def _find_video_file(self) -> Path:
        """查找视频文件"""
        patterns = ["*_soft.mp4", "*_hard.mp4", "*_bilingual.mp4", "*.mp4"]
        for pattern in patterns:
            files = list(self.video_dir.glob(pattern))
            if files:
                return files[0]
        raise FileNotFoundError(f"未找到视频: {self.video_dir}")
    
    def _find_cover_file(self) -> Path:
        """查找封面文件（modern 方案，支持 PNG/JPG）"""
        # 优先查找 modern 方案
        for ext in ['.png', '.jpg', '.jpeg']:
            # 尝试 cover_modern.* 格式
            cover = self.video_dir / f"cover_modern{ext}"
            if cover.exists():
                return cover
            # 尝试 modern.* 格式（无 cover_ 前缀）
            cover = self.video_dir / f"modern{ext}"
            if cover.exists():
                return cover
        
        # 如果没有 modern，找任意封面
        for pattern in ["cover_*.png", "cover_*.jpg", "*.png", "*.jpg"]:
            covers = list(self.video_dir.glob(pattern))
            # 过滤出封面文件（包含方案名）
            covers = [c for c in covers if any(s in c.stem.lower() for s in ['modern', 'vibrant', 'elegant', 'fresh'])]
            if covers:
                logger.warning(f"⚠️  未找到 modern 封面，使用: {covers[0].name}")
                return covers[0]
        
        raise FileNotFoundError(f"未找到封面文件: {self.video_dir}")
    
    def _load_info(self) -> Dict:
        """加载B站信息"""
        info_file = self.video_dir / "cover_texts.json"
        if not info_file.exists():
            raise FileNotFoundError(f"未找到信息文件: {info_file}")
        
        with open(info_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'title': data.get('bilibili_title', '未命名视频'),
            'tags': data.get('bilibili_tags', []),
            'description': data.get('bilibili_description', '')
        }
    
    def get_upload_instructions(self) -> str:
        """生成上传指令（供 AI 参考）"""
        return f"""
B站视频上传流程：

1. 打开上传页面
   URL: {self.UPLOAD_URL}
   
2. 上传视频
   文件路径: {self.video_file}
   等待上传完成（显示"上传成功"或进度100%）
   
3. 填写标题
   标题: {self.info['title']}
   
4. 选择类型：自制（必须！）
   点击"自制"单选按钮
   
5. 选择分区
   分区: {self.CATEGORY}
   
6. 上传封面
   封面路径: {self.cover_file}
   
7. 删除默认标签，添加自定义标签
   标签（逗号分隔）: {', '.join(self.info['tags'][:10])}
   
8. 填写简介
   简介内容:
   {self.info['description']}
   
9. 选择活动（如果有）
   选择第二个活动选项
   
10. 提交
    点击"立即投稿"按钮
    等待提交成功
    
11. 验证
    确认视频已提交到审核队列
"""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'video': str(self.video_file),
            'cover': str(self.cover_file),
            'title': self.info['title'],
            'tags': self.info['tags'],
            'description': self.info['description'],
            'category': self.CATEGORY,
            'upload_url': self.UPLOAD_URL
        }


def print_mcp_instructions(config: BilibiliUploadConfig):
    """打印 MCP Playwright 操作指南"""
    print("\n" + "="*70)
    print("🤖 请 AI 使用 MCP Playwright 工具执行以下操作")
    print("="*70)
    print()
    print("📋 上传配置：")
    print(f"   视频: {config.video_file}")
    print(f"   封面: {config.cover_file}")
    print(f"   标题: {config.info['title']}")
    print(f"   标签: {', '.join(config.info['tags'][:5])}...")
    print()
    print("🔧 MCP Playwright 工具调用顺序：")
    print()
    print("1. mcp_playwright_browser_navigate")
    print(f"   → URL: {config.UPLOAD_URL}")
    print()
    print("2. mcp_playwright_browser_snapshot")
    print("   → 获取页面结构，找到上传按钮")
    print()
    print("3. mcp_playwright_browser_file_upload")
    print(f"   → 上传视频: {config.video_file}")
    print()
    print("4. mcp_playwright_browser_wait_for")
    print("   → 等待文字: '上传成功' 或 '转码完成'")
    print()
    print("5. mcp_playwright_browser_type")
    print(f"   → 填写标题: {config.info['title']}")
    print()
    print("6. mcp_playwright_browser_click")
    print("   → 点击'自制'类型（必须！）")
    print()
    print("7. mcp_playwright_browser_select_option")
    print(f"   → 选择分区: {config.CATEGORY}")
    print()
    print("8. mcp_playwright_browser_file_upload")
    print(f"   → 上传封面: {config.cover_file}")
    print()
    print("9. mcp_playwright_browser_fill_form")
    print("   → 添加标签（删除默认，添加自定义）")
    print(f"   → 标签: {', '.join(config.info['tags'][:10])}")
    print()
    print("10. mcp_playwright_browser_evaluate")
    print("    → 填充简介到 .ql-editor 元素")
    print(f"    → 简介: {len(config.info['description'])} 字符")
    print()
    print("11. mcp_playwright_browser_click")
    print("    → 选择活动（第二个选项）")
    print()
    print("12. mcp_playwright_browser_click")
    print("    → 点击'立即投稿'")
    print()
    print("13. mcp_playwright_browser_wait_for")
    print("    → 等待成功提示")
    print()
    print("="*70)
    print("✨ 准备就绪！AI 可以开始执行上传流程")
    print("="*70)
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='B站自动上传工具（MCP Playwright 版）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 准备上传配置
  python src/bilibili_auto_upload.py --video-dir "../output/视频名/"
  
  # 然后在 Cursor 中告诉 AI：
  "请使用 MCP Playwright 按照上述步骤上传视频到B站"

注意：
  1. 需要先在浏览器中登录B站
  2. 确保 MCP Playwright 已在 Cursor 中启用
  3. 让 AI 读取此脚本输出的指令并执行
        """
    )
    
    parser.add_argument(
        '--video-dir',
        required=True,
        help='视频输出目录'
    )
    
    parser.add_argument(
        '--json-output',
        help='输出配置为 JSON 文件'
    )
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config = BilibiliUploadConfig(args.video_dir)
        
        # 打印指令
        print_mcp_instructions(config)
        
        # 输出详细指令
        print("\n📝 详细操作步骤：")
        print(config.get_upload_instructions())
        
        # 保存 JSON 配置
        if args.json_output:
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 配置已保存: {args.json_output}")
        else:
            # 默认保存到视频目录
            json_file = config.video_dir / "bilibili_upload_config.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 配置已保存: {json_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3
"""
微信公众号文章生成器
从视频字幕生成适合公众号发布的图文内容
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from openai import OpenAI
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WechatArticleGenerator:
    """微信公众号文章生成器"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """
        初始化生成器
        
        Args:
            api_key: DeepSeek API Key
            model: 使用的模型名称
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if not self.api_key:
            raise ValueError("请提供 DeepSeek API Key 或设置环境变量 DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model
    
    def parse_subtitle_text(self, subtitle_blocks: List[Dict]) -> str:
        """
        解析字幕块为纯文本
        
        Args:
            subtitle_blocks: 字幕块列表
            
        Returns:
            合并后的文本内容
        """
        texts = []
        for block in subtitle_blocks:
            if 'text' in block and block['text'].strip():
                texts.append(block['text'].strip())
        
        return ' '.join(texts)
    
    def generate_article_prompt(
        self,
        video_title: str,
        video_description: str,
        subtitle_text: str,
        word_count: int = 2000,
        style: str = "professional"
    ) -> str:
        """
        生成文章生成的Prompt
        
        Args:
            video_title: 视频标题
            video_description: 视频描述
            subtitle_text: 字幕文本
            word_count: 目标字数
            style: 文章风格（professional/casual/academic）
            
        Returns:
            完整的prompt
        """
        style_desc = {
            "professional": "专业、客观、有深度",
            "casual": "轻松、有趣、接地气",
            "academic": "学术、严谨、引经据典"
        }
        
        prompt = f"""你是一位专业的内容编辑，擅长将视频内容转换为微信公众号文章。

**任务：**
根据以下YouTube视频的信息和字幕内容，生成一篇适合微信公众号发布的文章。

**视频信息：**
- 标题：{video_title}
- 简介：{video_description if video_description else "无"}

**字幕内容：**
{subtitle_text[:8000]}  # 限制长度避免token超限

**生成要求：**
1. **标题**：
   - 吸引眼球，15-30字
   - 体现核心价值和亮点
   - 可以是疑问句、数字标题或悬念标题
   
2. **摘要**（50-100字）：
   - 概括主要观点
   - 引发阅读兴趣
   
3. **正文结构**：
   - **引言**：介绍视频背景和主题（100-200字）
   - **核心观点**：提炼3-5个要点，每个要点300-500字，包含详细阐述
   - **深度分析**：结合实际案例，延伸思考（300-500字）
   - **总结**：核心要点回顾和启发思考（100-200字）
   
4. **字数要求**：{word_count}字左右（正文部分）

5. **风格**：{style_desc.get(style, style_desc['professional'])}

6. **排版要求**：
   - 使用Markdown格式
   - 使用## 和 ### 标记标题层级
   - 重点内容使用**加粗**
   - 适当使用emoji增强可读性（🎯📌💡✨🤔等）
   - 使用列表和引用块增强可读性
   
7. **互动元素**：
   - 结尾包含思考题
   - 引导留言互动
   
**输出格式（JSON）：**
请严格按照以下JSON格式输出，确保JSON格式正确：

```json
{{
  "title": "文章标题（15-30字）",
  "summary": "文章摘要（50-100字）",
  "content": "Markdown格式的正文内容",
  "key_points": [
    "核心要点1",
    "核心要点2",
    "核心要点3"
  ],
  "tags": ["标签1", "标签2", "标签3"],
  "reading_time": "预估阅读时间（分钟）"
}}
```

请确保：
- content字段包含完整的Markdown格式正文
- 正文包含引言、核心观点、深度分析、总结四个部分
- 使用emoji和格式化增强可读性
- JSON格式正确，所有引号和括号匹配
"""
        return prompt
    
    def call_deepseek(self, prompt: str, temperature: float = 0.7) -> str:
        """
        调用DeepSeek API
        
        Args:
            prompt: 提示词
            temperature: 温度参数
            
        Returns:
            API返回的内容
        """
        try:
            logger.info("🤖 正在调用DeepSeek生成文章...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的内容编辑和写作专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=8000
            )
            
            result = response.choices[0].message.content
            logger.info("✅ 文章生成完成")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ DeepSeek API调用失败: {e}")
            raise
    
    def parse_article_response(self, response: str) -> Dict:
        """
        解析API返回的文章内容
        
        Args:
            response: API返回的文本
            
        Returns:
            解析后的文章字典
        """
        try:
            # 尝试提取JSON部分
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            # 解析JSON
            article_data = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ['title', 'summary', 'content']
            for field in required_fields:
                if field not in article_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            return article_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.error(f"原始响应: {response[:500]}...")
            
            # 降级处理：返回基本结构
            return {
                "title": "文章生成失败",
                "summary": "无法解析文章内容",
                "content": response,
                "key_points": [],
                "tags": [],
                "reading_time": "未知"
            }
    
    def generate_article(
        self,
        video_title: str,
        video_description: str,
        subtitle_blocks: List[Dict],
        word_count: int = 2000,
        style: str = "professional"
    ) -> Dict:
        """
        生成微信公众号文章
        
        Args:
            video_title: 视频标题
            video_description: 视频描述
            subtitle_blocks: 字幕块列表
            word_count: 目标字数
            style: 文章风格
            
        Returns:
            文章数据字典
        """
        logger.info("=" * 70)
        logger.info("📝 开始生成微信公众号文章")
        logger.info("=" * 70)
        
        # 解析字幕文本
        subtitle_text = self.parse_subtitle_text(subtitle_blocks)
        logger.info(f"📖 字幕文本长度: {len(subtitle_text)} 字符")
        
        # 生成prompt
        prompt = self.generate_article_prompt(
            video_title,
            video_description,
            subtitle_text,
            word_count,
            style
        )
        
        # 调用API
        response = self.call_deepseek(prompt)
        
        # 解析结果
        article = self.parse_article_response(response)
        
        # 添加元数据
        article['video_title'] = video_title
        article['video_description'] = video_description
        article['word_count'] = len(article['content'])
        article['generated_at'] = datetime.now().isoformat()
        article['model'] = self.model
        
        logger.info(f"✅ 文章生成成功")
        logger.info(f"   标题: {article['title']}")
        logger.info(f"   字数: {article['word_count']}")
        logger.info(f"   阅读时间: {article.get('reading_time', '未知')}")
        
        return article
    
    def save_article(self, article: Dict, output_dir: Path, video_id: str):
        """
        保存文章到文件
        
        Args:
            article: 文章数据
            output_dir: 输出目录
            video_id: 视频ID
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存Markdown格式
        md_file = output_dir / "article.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {article['title']}\n\n")
            f.write(f"> 📌 {article['summary']}\n\n")
            f.write(f"---\n\n")
            f.write(article['content'])
            f.write(f"\n\n---\n\n")
            f.write(f"**标签：** {' '.join(['#' + tag for tag in article.get('tags', [])])}\n\n")
            f.write(f"**阅读时间：** {article.get('reading_time', '未知')}\n\n")
            f.write(f"**原视频标题：** {article['video_title']}\n\n")
        
        logger.info(f"✅ Markdown文章已保存: {md_file}")
        
        # 保存JSON格式（包含完整元数据）
        json_file = output_dir / "article.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON数据已保存: {json_file}")
        
        # 保存纯文本版本（方便复制）
        txt_file = output_dir / "article.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"{article['title']}\n\n")
            f.write(f"{article['summary']}\n\n")
            f.write(article['content'])
        
        logger.info(f"✅ 纯文本已保存: {txt_file}")


def main():
    """测试函数"""
    # 示例用法
    generator = WechatArticleGenerator()
    
    # 示例字幕块
    subtitle_blocks = [
        {"text": "Hello, welcome to this video about AI."},
        {"text": "Today we're going to discuss the future of artificial intelligence."},
        {"text": "AI is transforming every industry..."}
    ]
    
    article = generator.generate_article(
        video_title="AI的未来：改变世界的技术",
        video_description="探讨人工智能如何改变我们的生活",
        subtitle_blocks=subtitle_blocks,
        word_count=2000,
        style="professional"
    )
    
    print(json.dumps(article, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

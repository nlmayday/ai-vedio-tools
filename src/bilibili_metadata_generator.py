#!/usr/bin/env python3
"""
B站元数据生成器 - 根据字幕内容生成 B 站上传所需的所有元素

用法:
    python src/bilibili_metadata_generator.py \
        --title "视频标题" \
        --subtitle output/725/en_readable.srt \
        --output output/725/bilibili_meta.json

生成的 JSON 包含:
    - bilibili_title: B站标题
    - bilibili_tags: 标签列表
    - bilibili_description: 视频简介
    - cover_title1 / cover_title2: 封面主标题
    - cover_subtitle_cn / cover_subtitle_en: 封面副标题
    - cover_lines: 2-3 句核心摘要（用于 AI 生成封面图）
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的B站视频运营专家和封面设计师。你需要根据视频的字幕内容，精准提炼核心信息，生成上传所需的所有元数据。

具体要求：
1. **bilibili_title**（B站标题）：吸引人且信息量大，20-40字，包含关键词，适合中文互联网传播风格，但不要标题党
2. **bilibili_tags**（标签）：8-10个标签（B站限制最多10个），从不同维度覆盖（内容主题、人物、概念、领域等），热门且精准
3. **bilibili_description**（视频简介）：200-500字，结构化介绍视频内容、核心观点、适合人群。使用换行分段
4. **cover_title1 / cover_title2**（封面主标题两行）：每行2-8字，大字排版适合封面，抓眼球
5. **cover_subtitle_cn**（封面副标题中文）：12-20字，补充说明核心内容
6. **cover_subtitle_en**（封面副标题英文）：对应英文翻译
7. **cover_lines**（封面短句）：3-4条中文短句，每条6-12字，精炼有冲击力，适合放在封面图片上。避免长句，确保在封面上排版不拥挤

请直接返回 JSON 格式，不要有其他说明："""


def _parse_srt_text(srt_path: str) -> str:
    """从 SRT 文件中提取纯文本"""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    texts = []
    for block in content.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 3 and "-->" in lines[1]:
            text = " ".join(lines[2:]).strip()
            texts.append(text)
    return " ".join(texts)


def _extract_json(content: str) -> dict:
    """从 AI 回复中提取 JSON"""
    content = content.strip()
    if content.startswith("```"):
        parts = content.split("```")
        content = parts[1] if len(parts) > 1 else parts[0]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def generate_metadata(
    title: str,
    subtitle_path: str,
    api_key: str = None,
    model: str = "deepseek-chat",
) -> dict:
    """
    根据标题和字幕生成 B 站上传元数据。

    Args:
        title: 视频原始标题
        subtitle_path: 字幕 SRT 文件路径
        api_key: DeepSeek API Key
        model: 模型名称

    Returns:
        包含所有元数据的字典
    """
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请提供 DEEPSEEK_API_KEY 环境变量或通过参数传入")

    # 读取字幕全文
    full_text = _parse_srt_text(subtitle_path)
    if not full_text:
        raise ValueError(f"未能从 {subtitle_path} 中提取到字幕文本")

    # 截取前 4000 字符（足够理解内容，同时控制 token 消耗）
    text_sample = full_text[:4000]
    logger.info(f"字幕总长度: {len(full_text)} 字符, 发送: {len(text_sample)} 字符")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    user_prompt = f"""视频原标题：{title}

字幕内容（节选）：
---
{text_sample}
---

请根据以上字幕内容生成 JSON。"""

    logger.info("调用 DeepSeek API 生成元数据...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content
    result = _extract_json(raw)

    # 验证必要字段
    required = [
        "bilibili_title", "bilibili_tags", "bilibili_description",
        "cover_title1", "cover_title2",
        "cover_subtitle_cn", "cover_subtitle_en",
        "cover_lines",
    ]
    missing = [k for k in required if k not in result]
    if missing:
        logger.warning(f"缺少字段: {missing}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="B站元数据生成器 - 根据字幕内容生成上传所需元素",
    )
    parser.add_argument("--title", "-t", required=True, help="视频原始标题")
    parser.add_argument("--subtitle", "-s", required=True, help="字幕 SRT 文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出 JSON 文件路径")
    parser.add_argument("--api-key", help="DeepSeek API Key（也可用环境变量）")
    args = parser.parse_args()

    if not os.path.exists(args.subtitle):
        print(f"错误：字幕文件不存在: {args.subtitle}")
        return 1

    try:
        meta = generate_metadata(
            title=args.title,
            subtitle_path=args.subtitle,
            api_key=args.api_key,
        )

        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        logger.info(f"元数据已保存到: {args.output}")
        _print_summary(meta)
        return 0

    except Exception as e:
        logger.error(f"生成失败: {e}")
        return 1


def _print_summary(meta: dict):
    """打印摘要"""
    print("\n" + "=" * 60)
    print("B站标题:", meta.get("bilibili_title", "N/A"))
    print("标签:", ", ".join(meta.get("bilibili_tags", [])))
    print("封面标题:", meta.get("cover_title1", ""), "|", meta.get("cover_title2", ""))
    print("封面副标题:", meta.get("cover_subtitle_cn", ""))
    print("封面长句:")
    for line in meta.get("cover_lines", []):
        print(f"  - {line}")
    desc = meta.get("bilibili_description", "")
    print(f"简介: {desc[:100]}..." if len(desc) > 100 else f"简介: {desc}")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())

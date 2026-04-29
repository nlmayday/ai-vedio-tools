#!/usr/bin/env python3
"""
字幕断句器 - 基于标点规则合并 whisper 碎片

核心原则：
1. 在 .!? 处合并为完整句子
2. 两句共用一个片段时，按字数比例拆分该片段的时间，保证不重叠
3. 长句在逗号处递归二分拆分
4. 短行合并到相邻行
"""

import re
from collections import defaultdict
from pathlib import Path

MAX_WORDS = 15
MIN_WORDS = 5


def _parse_srt(srt_path: str) -> list[dict]:
    blocks = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    for block in content.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 3 and "-->" in lines[1]:
            start, end = [t.strip() for t in lines[1].split("-->")]
            text = " ".join(lines[2:]).strip()
            blocks.append({"start_time": start, "end_time": end, "text": text})
    return blocks


def _write_srt(blocks: list[dict], output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, b in enumerate(blocks, 1):
            f.write(f"{i}\n")
            f.write(f"{b['start_time']} --> {b['end_time']}\n")
            f.write(f"{b['text']}\n\n")


def _time_to_seconds(t: str) -> float:
    t = t.replace(",", ".")
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _seconds_to_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _build_char_map(fragments: list[dict]) -> tuple[str, list[int]]:
    full_text = ""
    char_to_frag = []
    for idx, b in enumerate(fragments):
        if full_text and not full_text.endswith(" "):
            full_text += " "
            char_to_frag.append(idx)
        for ch in b["text"]:
            full_text += ch
            char_to_frag.append(idx)
    return full_text, char_to_frag


_SENTENCE_END = re.compile(r'[.!?]+["\']?\s+')
_PAUSE_RE = re.compile(r'(?<!\d)[;,]\s*|(?<!\d):\s+')


def resegment_srt(input_srt: str, output_srt: str) -> str:
    """
    1. 拼接全文 → 按 .!? 切句
    2. 两句共用的片段按字数比例拆分时间，保证不重叠
    3. 长句在逗号处递归二分拆分（再保证子块间不重叠）
    4. 合并过短行
    """
    fragments = _parse_srt(input_srt)
    if not fragments:
        raise ValueError(f"No subtitle blocks found in {input_srt}")

    full_text, char_to_frag = _build_char_map(fragments)

    # ---- 步骤 1: 切句 ----
    raw_sentences = []
    start = 0
    for m in _SENTENCE_END.finditer(full_text):
        end = m.end()
        text = full_text[start:end].strip()
        if text:
            raw_sentences.append({"text": text, "char_start": start, "char_end": end})
        start = end
    if start < len(full_text):
        text = full_text[start:].strip()
        if text:
            raw_sentences.append({"text": text, "char_start": start, "char_end": len(full_text)})

    # ---- 步骤 2: 为每个句子统计每个片段的字符数 ----
    sent_frag_chars = []
    for sent in raw_sentences:
        counts = defaultdict(int)
        for pos in range(sent["char_start"], min(sent["char_end"], len(char_to_frag))):
            counts[char_to_frag[pos]] += 1
        sent_frag_chars.append(counts)

    # ---- 步骤 3: 分配时间戳，解决共用片段 ----
    sentences = []
    prev_end_sec = None  # 上一句的结束时间（秒）

    for i, sent in enumerate(raw_sentences):
        counts = sent_frag_chars[i]
        frags_used = sorted(counts.keys())
        if not frags_used:
            continue
        first_frag = frags_used[0]
        last_frag = frags_used[-1]

        # 起始时间
        if i > 0 and first_frag == sorted(sent_frag_chars[i - 1].keys())[-1]:
            # 与上一句共用一个片段 → 从上一句结束时间开始
            start_sec = prev_end_sec
        else:
            start_sec = _time_to_seconds(fragments[first_frag]["start_time"])

        # 结束时间
        if i + 1 < len(raw_sentences):
            next_frags = sorted(sent_frag_chars[i + 1].keys())
            if next_frags and last_frag == next_frags[0]:
                # 与下一句共用一个片段 → 按字数比例拆分
                shared_frag = last_frag
                my_chars = counts[shared_frag]
                next_chars = sent_frag_chars[i + 1][shared_frag]
                total = my_chars + next_chars
                proportion = my_chars / total if total > 0 else 0.5

                frag_start = _time_to_seconds(fragments[shared_frag]["start_time"])
                frag_end = _time_to_seconds(fragments[shared_frag]["end_time"])
                end_sec = frag_start + proportion * (frag_end - frag_start)
            else:
                end_sec = _time_to_seconds(fragments[last_frag]["end_time"])
        else:
            end_sec = _time_to_seconds(fragments[last_frag]["end_time"])

        # 防止时间为零或负数
        if end_sec <= start_sec:
            end_sec = start_sec + 0.5

        prev_end_sec = end_sec

        sentences.append({
            "text": sent["text"],
            "char_start": sent["char_start"],
            "char_end": sent["char_end"],
            "start_time": _seconds_to_time(start_sec),
            "end_time": _seconds_to_time(end_sec),
            "start_sec": start_sec,
            "end_sec": end_sec,
        })

    # ---- 步骤 4: 拆分长句 ----
    result = []
    for sent in sentences:
        subs = _split_long(sent)
        result.extend(subs)

    # ---- 步骤 5: 合并过短行 ----
    result = _merge_shorts(result)

    _write_srt(result, output_srt)
    print(
        f"Segmented: {len(fragments)} fragments → "
        f"{len(sentences)} sentences → {len(result)} readable lines"
    )
    return output_srt


def _split_long(sentence: dict) -> list[dict]:
    """在逗号处递归二分拆分，子块间按字数比例分配时间"""
    text = sentence["text"]
    words = text.split()
    if len(words) <= MAX_WORDS:
        return [{
            "start_time": sentence["start_time"],
            "end_time": sentence["end_time"],
            "text": text,
        }]

    # 找有效拆分点
    pause_positions = [m.end() for m in _PAUSE_RE.finditer(text)]
    valid = []
    for cp in pause_positions:
        prefix_wc = len(text[:cp].split())
        suffix_wc = len(text[cp:].split())
        if prefix_wc >= MIN_WORDS and suffix_wc >= MIN_WORDS:
            valid.append((cp, prefix_wc))

    if not valid:
        return [{
            "start_time": sentence["start_time"],
            "end_time": sentence["end_time"],
            "text": text,
        }]

    # 最接近中间的拆分点
    half = len(words) / 2
    best_cp = min(valid, key=lambda x: abs(x[1] - half))[0]

    part1 = text[:best_cp].strip()
    part2 = text[best_cp:].strip()
    if not part1 or not part2:
        return [{
            "start_time": sentence["start_time"],
            "end_time": sentence["end_time"],
            "text": text,
        }]

    # 按字数比例拆分时间
    wc1 = len(part1.split())
    wc2 = len(part2.split())
    total_wc = wc1 + wc2
    duration = sentence["end_sec"] - sentence["start_sec"]

    mid_sec = sentence["start_sec"] + duration * (wc1 / total_wc)

    sub1 = {
        "text": part1,
        "start_time": sentence["start_time"],
        "end_time": _seconds_to_time(mid_sec),
        "start_sec": sentence["start_sec"],
        "end_sec": mid_sec,
    }
    sub2 = {
        "text": part2,
        "start_time": _seconds_to_time(mid_sec),
        "end_time": sentence["end_time"],
        "start_sec": mid_sec,
        "end_sec": sentence["end_sec"],
    }

    result = []
    result.extend(_split_long(sub1))
    result.extend(_split_long(sub2))
    return result


def _merge_shorts(blocks: list[dict]) -> list[dict]:
    """将 < MIN_WORDS 词的行合并到相邻行"""
    if len(blocks) <= 1:
        return blocks
    result = []
    for b in blocks:
        wc = len(b["text"].split())
        if result and wc < MIN_WORDS:
            prev = result[-1]
            result[-1] = {
                "start_time": prev["start_time"],
                "end_time": b["end_time"],
                "text": prev["text"] + " " + b["text"],
            }
        else:
            result.append(b)
    return result

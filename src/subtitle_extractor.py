#!/usr/bin/env python3
"""
字幕提取器 - 使用 whisper.cpp 从视频中提取字幕
"""

import subprocess
import tempfile
import os
from pathlib import Path


def find_whisper_binary() -> str:
    """查找 whisper-cli 可执行文件"""
    candidates = [
        Path(__file__).parent.parent.parent / "whisper.cpp" / "build" / "bin" / "whisper-cli",
        Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    raise FileNotFoundError("whisper-cli not found. Build whisper.cpp first.")


def find_whisper_model() -> str:
    """查找 whisper 模型文件（优先 large-v3）"""
    models_dir = Path(__file__).parent.parent.parent / "whisper.cpp" / "models"
    for model in ["ggml-large-v3.bin", "ggml-large-v2.bin", "ggml-medium.bin"]:
        p = models_dir / model
        if p.exists():
            return str(p)
    raise FileNotFoundError(f"No whisper model found in {models_dir}")


def extract_audio(video_path: str, audio_path: str) -> str:
    """从视频中提取 16kHz 单声道 WAV 音频"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn", "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr}")
    return audio_path


def transcribe_audio(audio_path: str, output_srt: str, language: str = "en") -> str:
    """使用 whisper.cpp 将音频转为 SRT 字幕"""
    whisper_bin = find_whisper_binary()
    model_path = find_whisper_model()

    cmd = [
        whisper_bin,
        "-m", model_path,
        "-f", audio_path,
        "-l", language,
        "-osrt",
        "-of", str(Path(output_srt).with_suffix("")),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"Whisper transcription failed: {result.stderr}")

    srt_path = str(Path(output_srt).with_suffix(".srt"))
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"SRT not generated: {srt_path}")
    return srt_path


def extract_subtitles(video_path: str, output_srt: str, language: str = "en",
                      keep_audio: bool = False) -> str:
    """
    从视频中提取字幕（音频 → whisper ASR → SRT）

    Args:
        video_path: 输入视频路径
        output_srt: 输出 SRT 路径
        language: 视频语言代码 (默认 "en")
        keep_audio: 是否保留中间音频文件

    Returns:
        生成的 SRT 文件路径
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    Path(output_srt).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    try:
        extract_audio(video_path, audio_path)
        result = transcribe_audio(audio_path, output_srt, language)
        return result
    finally:
        if not keep_audio and os.path.exists(audio_path):
            os.unlink(audio_path)

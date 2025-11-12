# 📖 使用指南

视频处理工具集完整使用说明。

## 🚀 快速开始

### 环境准备

```bash
# 1. 安装依赖
cd /Users/jarvis/work/tools/ai-vedio/vedio-tools
pip install -r requirements.txt

# 2. 安装 ffmpeg
brew install ffmpeg

# 3. 设置 API Key
export DEEPSEEK_API_KEY="your_api_key"
```

---

## 🤖 自动处理系统（推荐）⭐⭐⭐

**最智能的解决方案，一键完成所有步骤！**

```bash
cd vedio-tools

# 执行一次处理
python src/auto_process_videos.py

# 持续监控模式
python src/auto_process_videos.py --watch

# 查看状态
python src/auto_process_videos.py --status
```

**功能：**
- ✅ 自动扫描 data 目录中的视频
- ✅ 检测视频下载完成
- ✅ 检查是否已有中文字幕，没有则翻译
- ✅ 合并双语字幕到视频
- ✅ 生成封面和B站信息
- ✅ 备份所有文件
- ✅ 所有输出统一到 `output/视频名/` 目录

---

## 📝 字幕翻译

### 超智能翻译（推荐）

```bash
# 智能分段翻译（避免断句，API调用减少60%）
python src/subtitle_translator_smart.py --input ../data/video.en.vtt
```

### 基础翻译

```bash
# 适合小文件（<500条）
python src/subtitle_translator.py --input ../data/video.en.vtt
```

### 续传翻译

```bash
# 支持断点续传（适合500-2000条）
python src/subtitle_translator_resume.py --input ../data/video.en.vtt
```

### 批量翻译

```bash
# 翻译目录下所有字幕
python src/batch_translate_subtitles.py --input-dir ../data
```

---

## 🎬 字幕合并到视频

### 软字幕（快速，需VLC播放）

```bash
python src/video_subtitle_merger.py \
  --video ../data/video.webm \
  --en-subtitle ../data/video.en.vtt \
  --zh-subtitle ../data/video.zh.vtt \
  --type soft \
  --output ../output/video/video_bilingual_soft.mp4
```

### 硬字幕（B站推荐）

**在 data 目录运行（避免路径问题）：**

```bash
cd data

# 1. 复制字幕为简单名字
cp "video_bilingual.srt" "simple.srt"

# 2. 烧录硬字幕
ffmpeg -i "video.webm" \
  -vf "subtitles=simple.srt" \
  -c:a copy \
  "../output/video/video_bilingual_hard.mp4"
```

**注意：** 
- 需要在新终端窗口运行
- 预计15-20分钟
- 字幕会烧录在画面中

---

## 🎨 封面生成

### AI自动生成

```bash
# 自动生成4种配色方案 + B站信息
python src/auto_generate_cover.py --video ../data/video.mp4
```

**输出：**
```
output/video/
├── cover_texts.json    # AI生成的文案（含B站标题、标签、简介）
├── modern.jpg
├── vibrant.jpg
├── elegant.jpg
└── fresh.jpg
```

### 手动指定文案

```bash
python src/thumbnail_generator.py \
  --video ../data/video.mp4 \
  --title1 "标题第一行" \
  --title2 "标题第二行" \
  --subtitle-cn "中文字幕" \
  --subtitle-en "English Subtitle" \
  --scheme modern \
  --output ../output/video/cover.jpg
```

**配色方案：**
- `modern` - 深蓝渐变（科技、商务）
- `vibrant` - 紫红渐变（娱乐、创意）
- `elegant` - 黑金渐变（高端、艺术）
- `fresh` - 蓝色渐变（生活、旅行）

---

## 🔧 工具说明

### 字幕翻译工具

| 工具 | 适用场景 | 命令 |
|------|---------|------|
| smart | 所有场景（推荐）| `python src/subtitle_translator_smart.py` |
| resume | 500-2000条 | `python src/subtitle_translator_resume.py` |
| basic | <500条 | `python src/subtitle_translator.py` |
| batch | 批量处理 | `python src/batch_translate_subtitles.py` |

### 视频处理工具

| 工具 | 功能 | 命令 |
|------|------|------|
| video_subtitle_merger.py | 合并字幕 | `python src/video_subtitle_merger.py` |
| vtt_to_srt.py | 格式转换 | `python src/vtt_to_srt.py` |

### 封面工具

| 工具 | 功能 | 命令 |
|------|------|------|
| auto_generate_cover.py | AI自动生成 | `python src/auto_generate_cover.py` |
| thumbnail_generator.py | 手动生成 | `python src/thumbnail_generator.py` |

### 自动化工具

| 工具 | 功能 | 命令 |
|------|------|------|
| auto_process_videos.py | 自动处理系统 | `python src/auto_process_videos.py` |

---

## ⚙️ 配置文件

所有配置在 `config.yaml` 中：

```yaml
subtitle:
  type: soft          # 字幕类型：soft 或 hard
  font_size: 20       # 字体大小

translation:
  translator: smart   # 翻译器版本
  target_size: 50     # 批次大小

cover:
  default_schemes:    # 默认配色方案
    - modern
    - vibrant
    - elegant
    - fresh

auto_process:
  check_interval: 60  # 检查间隔（秒）
  generate_bilibili_subtitles: true  # 生成B站字幕
  generate_covers: true               # 生成封面
```

---

## 📂 输出结构

所有输出统一到 `output/视频名/` 目录：

```
output/
└── NVIDIA CEO Jensen Huang's Vision for the Future/
    ├── cover_texts.json              # AI生成的文案（含B站信息）
    ├── modern.jpg                    # 封面（4种配色）
    ├── vibrant.jpg
    ├── elegant.jpg
    ├── fresh.jpg
    ├── video_bilingual_soft.mp4      # 带字幕的视频
    ├── video_bilingual_soft.srt      # 双语字幕
    ├── NVIDIA..._zh.srt              # 中文字幕（B站用）
    └── NVIDIA..._en.srt              # 英文字幕（B站用）
```

---

## 💡 常用场景

### 场景1：YouTube视频自动处理

```bash
# 1. 下载视频到 data 目录
cd data
yt-dlp --write-subs --sub-lang en "https://youtube.com/watch?v=VIDEO_ID"

# 2. 启动自动处理
cd ../vedio-tools
python src/auto_process_videos.py --watch
```

### 场景2：B站上传准备

```bash
cd vedio-tools

# 1. 翻译字幕
python src/subtitle_translator_smart.py --input ../data/video.en.vtt

# 2. 生成封面和B站信息
python src/auto_generate_cover.py --video ../data/video.webm

# 3. 生成硬字幕（在 data 目录，新终端窗口）
cd ../data
cp video_bilingual.srt simple.srt
ffmpeg -i video.webm -vf "subtitles=simple.srt" -c:a copy output_hard.mp4
```

**上传到B站：**
- 视频：硬字幕版本
- 封面：从 `output/视频名/` 选一张
- 标题、标签、简介：查看 `output/视频名/cover_texts.json`

### 场景3：只生成封面

```bash
# AI自动生成
python src/auto_generate_cover.py --video ../data/video.mp4

# 手动指定文案
python src/thumbnail_generator.py \
  --video ../data/video.mp4 \
  --title1 "标题" \
  --subtitle-cn "中文" \
  --subtitle-en "English" \
  --scheme vibrant \
  --output ../output/video/custom.jpg
```

---

## ❓ 常见问题

### Q: 软字幕看不到？
**A:** 使用 VLC 播放器
```bash
brew install --cask vlc
open -a VLC output/video/video_bilingual_soft.mp4
```

### Q: 如何调整字幕大小？
**A:** 修改 `config.yaml` 中的 `subtitle.font_size`

### Q: 如何切换软/硬字幕？
**A:** 修改 `config.yaml` 中的 `subtitle.type`

### Q: API调用太多？
**A:** 已使用智能翻译器，自动优化批次大小

### Q: 如何批量处理？
**A:** 使用自动处理系统
```bash
python src/auto_process_videos.py --watch
```

---

## 📊 性能参考

### 30分钟视频（1000条字幕）

| 操作 | 时间 | 成本 |
|------|------|------|
| 翻译字幕 | 10分钟 | ¥0.30 |
| 软字幕合并 | 1-2秒 | ¥0 |
| 硬字幕烧录 | 15分钟 | ¥0 |
| 生成封面 | 30秒 | ¥0.001 |

---

💡 **推荐**：使用 `python src/auto_process_videos.py --watch` 实现全自动处理！

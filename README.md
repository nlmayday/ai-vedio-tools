# Video Tools - 视频处理工具集

🎬 专业的视频处理工具集，包含字幕翻译、视频合成、封面生成等功能。

> 📋 **完整目录结构说明**: 请查看 [STRUCTURE.md](STRUCTURE.md)

## 📁 目录结构

```
vedio-tools/
├── README.md              # 项目说明
├── config.yaml            # 配置文件 ⭐
├── requirements.txt       # 依赖列表
├── scripts/               # 📁 Shell脚本目录
│   ├── auto_process.sh        # 自动处理
│   ├── translate.sh           # 翻译字幕
│   ├── merge_subtitle.sh      # 合并字幕
│   ├── cover.sh               # 生成封面
│   ├── image_to_cover.sh      # 🖼️  从图片生成封面 🆕
│   ├── burn_subtitle.sh       # 烧录硬字幕
│   ├── show_output.sh         # 查看输出
│   ├── prepare_upload.sh      # 准备B站上传
│   ├── youtube_to_bilibili.sh # YouTube到B站全流程 🆕
│   ├── adjust_speed.sh        # 视频分段变速（保留完整） 🆕
│   └── adjust_speed_cut.sh    # 视频分段变速（裁剪模式） 🆕
├── src/                   # 📁 Python源代码
│   ├── auto_process_videos.py        # 自动处理系统
│   ├── subtitle_translator_smart.py  # 智能翻译
│   ├── video_subtitle_merger.py      # 字幕合并
│   ├── auto_generate_cover.py        # AI封面生成
│   ├── image_to_cover.py             # 🖼️  从图片生成封面 🆕
│   ├── bilibili_auto_upload.py       # B站自动上传
│   ├── youtube_to_bilibili.py        # YouTube到B站全流程 🆕
│   ├── speed_adjuster.py             # 视频分段变速 🆕
│   └── ...
├── docs/                  # 📁 文档目录
│   ├── USAGE.md                      # 详细使用指南
│   ├── QUICK_START.md                # 快速开始
│   ├── VIDEO_SPEED_ADJUSTMENT.md     # 视频变速工具文档 🆕
│   ├── SPEED_QUICK_START.md          # 变速工具快速上手 🆕
│   ├── BILIBILI_UPLOAD_GUIDE.md      # B站上传指南
│   └── YOUTUBE_TO_BILIBILI.md        # YouTube到B站指南
├── examples/              # 📁 示例配置
│   └── speed_config_example.json     # 变速配置示例
└── data/                  # 📁 数据输出目录
```

---

## ✨ 核心功能

### � YouTube 视频转微信公众号文章 🆕⭐

**自动将YouTube视频转换为适合微信公众号发布的图文内容！**

- ✨ 自动下载YouTube字幕
- 🤖 使用DeepSeek AI生成专业文章
- 📝 支持多种文章风格（专业/轻松/学术）
- 📊 输出Markdown/JSON/纯文本格式
- 🎯 完美适配公众号排版

```bash
# 快速开始
export DEEPSEEK_API_KEY='your-api-key'
cd src
python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx

# 高级选项
python youtube_to_wechat.py URL --word-count 2500 --style professional
```

**📖 详细文档：** [YouTube转微信公众号文章使用指南](docs/YOUTUBE_TO_WECHAT_GUIDE.md)

---

### �🎯 YouTube 到 B 站全流程 🆕⭐
- **一键处理**：YouTube 下载 → 翻译 → 封面生成 → 合成 → 上传 B 站
- 自动下载视频和字幕（支持所有语言）
- 智能检测字幕情况（有中文跳过翻译）
- 自动生成封面和 B 站信息
- 自动合并双语字幕
- 准备好的上传配置

### 🤖 自动处理系统
- 自动扫描和监控 data 目录
- 智能检测视频下载完成
- 自动翻译字幕（英文→中文）
- 自动合并双语字幕到视频
- 自动生成封面和B站信息
- 自动备份所有文件
- **所有输出统一到 `output/视频名/` 目录**

### 🌐 字幕翻译
- AI智能翻译（DeepSeek）
- 智能分段避免断句
- 支持断点续传
- API调用优化（减少60%）

### 🎬 视频字幕合并
- 软字幕（可开关，1秒完成）
- 硬字幕（烧录到画面，适合B站）
- 中英双语显示（中文在上，英文在下）

### 🎨 封面生成
- AI自动生成文案（含B站标题、标签、简介）
- 4种精美配色方案（modern/vibrant/elegant/fresh）
- 视频帧提取背景
- 中英双语字幕支持

### 🖼️ 从图片生成封面 🆕

- **直接使用图片**：使用任何图片作为封面背景
- **智能文字叠加**：自动添加标题和中英字幕
- **多种配色方案**：4种精美配色风格
- **专业布局**：居中对齐，带阴影效果

```bash
# 使用图片生成封面
./scripts/image_to_cover.sh background.jpg "精彩内容" "即将开始"

# 高级用法（中英双字幕）
./scripts/image_to_cover.sh photo.png "AI工具" "" "智能工具集" "AI Tools"
```

**配色方案：**
- `modern`: 现代风格（深蓝色）
- `vibrant`: 活力风格（紫红色）
- `elegant`: 优雅风格（黑金色）
- `fresh`: 清新风格（蓝色）

### 🎬 视频分段变速 🆕
- 根据 JSON 配置对视频不同片段应用不同播放速度
- 支持加快或减慢任意时间段
- 自动处理音频同步（保持音调）
- 支持任意播放速度（0.5x - 2.0x+）
- **两种模式**：
  - **保留模式**：保留完整视频，只调整指定片段速度
  - **裁剪模式**：只保留配置的片段，删除未配置部分（推荐）
- **裁剪模式增强**：自动生成4种配色封面
- 适用于跳过无关内容、强调重点、节奏调整

### 📤 B站自动上传 🆕
- MCP Playwright 自动化浏览器操作
- 一键上传视频、封面、信息
- 自动选择类型（自制）和分区（动画）
- 支持标签、简介自动填充
- 全程无需手动操作

---

## 🚀 快速开始

### 环境设置

```bash
cd vedio-tools

# 安装依赖
pip install -r requirements.txt

# 设置 API Key
export DEEPSEEK_API_KEY="your_api_key"
```

---

## 💡 快捷脚本（推荐使用）

### 🚀 YouTube 到 B 站（一键完成）⭐⭐⭐⭐⭐

```bash
# 一键处理 YouTube 视频并上传到 B 站
./scripts/youtube_to_bilibili.sh "https://www.youtube.com/watch?v=VIDEO_ID"

# 示例
./scripts/youtube_to_bilibili.sh "https://www.youtube.com/watch?v=0zXSrsKlm5A"
```

**完整流程：**
1. ✅ 使用 yt-dlp 下载视频和字幕
2. ✅ 自动翻译英文字幕到中文
3. ✅ 生成 4 种精美封面和 B 站信息
4. ✅ 合并双语字幕到视频
5. ✅ 准备上传配置

**智能处理：**
- 有英文字幕 → 自动翻译
- 有中英文字幕 → 直接合成
- 无字幕 → 提示手动导出

### 1. 自动处理（最简单）⭐⭐⭐

```bash
./scripts/auto_process.sh
```

选择模式后自动处理所有视频！

### 2. 翻译字幕

```bash
# 单个文件
./scripts/translate.sh ./data/video.en.vtt

# 批量翻译
./scripts/translate.sh --batch ./data
```

### 3. 生成封面

```bash
# 从视频生成封面
./scripts/cover.sh ./data/video.mp4

# 从图片生成封面 🆕
./scripts/image_to_cover.sh background.jpg "精彩内容" "即将开始"
```

### 4. 合并字幕

```bash
./scripts/merge_subtitle.sh \
  ./data/video.webm \
  ./data/video.en.vtt \
  ./data/video.zh.vtt
```

### 5. 烧录硬字幕（B站）

```bash
# 在新终端窗口运行
./scripts/burn_subtitle.sh ./data/video.webm
```

### 6. 查看输出

```bash
# 列出所有输出
./scripts/show_output.sh --list

# 查看特定视频
./scripts/show_output.sh "视频名"
```

### 7. 视频分段变速 🆕

#### 方式1：完整保留模式（adjust_speed.sh）
```bash
# 保留完整视频，只调整指定片段的播放速度
./scripts/adjust_speed.sh input.mp4 examples/speed_config.json output.mp4
```

#### 方式2：裁剪模式（adjust_speed_cut.sh）⭐⭐⭐
```bash
# 一键处理：变速 + 自动生成封面
./scripts/adjust_speed_cut.sh ./input/07.mp4
```

**功能特点：**
- ✅ **自动使用配置文件**：`examples/speed_config_example.json`
- ✅ **自动生成输出路径**：`./output/07/07.mp4`
- ✅ **自动生成封面**：处理完成后自动生成4种配色封面
  - `modern.jpg` - 现代风格
  - `vibrant.jpg` - 活力风格
  - `elegant.jpg` - 优雅风格
  - `fresh.jpg` - 清新风格
- ⚠️ **裁剪模式**：只保留配置的片段，删除未配置的部分
- 自动处理音频同步（保持音调）
- 支持任意播放速度（0.5x - 2.0x 及更大范围）

**输出结构：**
```
output/
└── 07/
    ├── 07.mp4           # 处理后的视频
    ├── modern.jpg       # 封面（4种配色）
    ├── vibrant.jpg
    ├── elegant.jpg
    └── fresh.jpg
```

**配置示例：**
```json
{
    "part": [
        {
            "timestamp": "00:00:50 - 00:01:00",
            "speed": 1.2
        },
        {
            "timestamp": "00:01:00 - 00:01:10",
            "speed": 1.0
        }
    ]
}
```

📖 详细文档：[视频变速工具文档](docs/VIDEO_SPEED_ADJUSTMENT.md)

### 8. B站自动上传 🆕

```bash
# 准备上传（生成配置）
./prepare_upload.sh "../output/视频名/"

# 然后在 Cursor 中告诉 AI：
# "请使用 MCP Playwright 帮我上传这个视频到B站"
```

**功能特性：**
- ✅ 自动读取视频、封面、标题、标签、简介
- ✅ 使用 MCP Playwright 自动化浏览器操作
- ✅ 自动选择"自制"类型和"动画"分区
- ✅ 支持活动选择（第二个）
- ✅ 一键上传，全程自动

**使用步骤：**
1. 运行 `./prepare_upload.sh` 生成配置
2. 在 Cursor 中请求 AI 执行上传
3. AI 会自动调用 MCP Playwright 完成上传
4. 等待审核通过

---

## 🐍 直接使用 Python（高级）

如果需要更多控制，可以直接调用 Python 脚本：

#### 翻译字幕
```bash
python src/subtitle_translator_smart.py --input ../data/video.en.vtt
```

#### 合并字幕
```bash
python src/video_subtitle_merger.py \
  --video ../data/video.webm \
  --en-subtitle ../data/video.en.vtt \
  --zh-subtitle ../data/video.zh.vtt \
  --output ../output/video/video_bilingual_soft.mp4
```

#### 生成封面
```bash
# 从视频生成封面
python src/auto_generate_cover.py --video ../data/video.mp4

# 从图片生成封面 🆕
python src/image_to_cover.py --image background.jpg --title1 "精彩内容"
```

---

## ⚙️ 配置文件

编辑 `config.yaml` 自定义设置：

```yaml
# 字幕设置
subtitle:
  type: soft          # soft（软字幕） 或 hard（硬字幕）
  font_size: 20       # 字体大小

# 翻译设置
translation:
  translator: smart   # 翻译器版本
  target_size: 50     # 批次大小

# 自动处理设置
auto_process:
  check_interval: 60                   # 检查间隔（秒）
  generate_bilibili_subtitles: true    # 生成B站字幕
  generate_covers: true                # 生成封面
```

---

## 📂 输出结构

所有输出统一到 `output/视频名/` 目录：

```
output/
└── NVIDIA CEO Jensen Huang's Vision for the Future/
    ├── cover_texts.json              # AI生成的文案
    │                                  # （含B站标题、标签、简介）
    ├── modern.jpg                    # 封面（4种配色）
    ├── vibrant.jpg
    ├── elegant.jpg
    ├── fresh.jpg
    ├── video_bilingual_soft.mp4      # 带字幕的视频
    ├── video_bilingual_soft.srt      # 双语字幕
    ├── video_zh.srt                  # 中文字幕（B站用）
    └── video_en.srt                  # 英文字幕（B站用）
```

---

## 💡 B站上传流程

1. **生成内容**
```bash
python src/auto_generate_cover.py --video ../data/video.webm
```

2. **查看B站信息**
```bash
cat output/视频名/cover_texts.json
```

会看到：
```json
{
  "title1": "封面标题1",
  "title2": "封面标题2",
  "subtitle_cn": "中文副标题",
  "subtitle_en": "English subtitle",
  "bilibili_title": "B站视频标题",
  "bilibili_tags": ["标签1", "标签2", "标签3"],
  "bilibili_description": "详细简介..."
}
```

3. **上传到B站**
- 视频：硬字幕版本（如有）或原视频
- 封面：从4张中选一张
- 标题：使用 `bilibili_title`
- 标签：使用 `bilibili_tags`
- 简介：使用 `bilibili_description`

---

## 📚 详细文档

查看 [docs/USAGE.md](docs/USAGE.md) 了解更多使用方法。

---

## 📄 许可证

MIT License

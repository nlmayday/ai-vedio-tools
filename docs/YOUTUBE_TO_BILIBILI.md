# YouTube 到 B 站全流程自动化

## 📖 概述

一键处理 YouTube 视频并上传到 B 站，全程自动化。

## 🚀 快速开始

### 基本用法

```bash
cd vedio-tools

# 一键处理 YouTube 视频
./youtube_to_bilibili.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 完整流程

1. ✅ **下载视频和字幕**（yt-dlp，支持所有语言）
2. ✅ **智能翻译字幕**（英文 → 中文，使用 DeepSeek）
3. ✅ **生成封面和 B 站信息**（AI 自动生成标题、标签、简介）
4. ✅ **合并双语字幕**（软字幕，1秒完成）
5. ✅ **准备上传配置**（可直接上传到 B 站）

---

## 📋 前置要求

### 1. 安装 yt-dlp

```bash
pip install yt-dlp
```

### 2. 设置 DeepSeek API Key

```bash
export DEEPSEEK_API_KEY="your_api_key"
```

### 3. Chrome 浏览器

用于下载受限视频（需要登录的视频）

---

## 💡 使用示例

### 示例 1：处理公开视频

```bash
./youtube_to_bilibili.sh "https://www.youtube.com/watch?v=0zXSrsKlm5A"
```

**流程：**
1. 下载视频和英文字幕
2. 翻译字幕到中文
3. 生成 4 种封面（modern/vibrant/elegant/fresh）
4. 生成 B 站标题、标签、简介
5. 合并字幕到视频
6. 输出到 `output/视频名/` 目录

### 示例 2：处理带时间戳的链接

```bash
./youtube_to_bilibili.sh "https://www.youtube.com/watch?v=0zXSrsKlm5A&t=515s"
```

### 示例 3：处理短链接

```bash
./youtube_to_bilibili.sh "https://youtu.be/0zXSrsKlm5A"
```

---

## 🎯 智能处理

### 场景 1：有英文字幕

```
YouTube 视频（有英文字幕）
  ↓
下载视频 + 英文字幕
  ↓
翻译英文字幕 → 中文字幕
  ↓
生成封面和 B 站信息
  ↓
合并双语字幕到视频
  ↓
准备上传
```

### 场景 2：有中英文字幕

```
YouTube 视频（有中英文字幕）
  ↓
下载视频 + 英文字幕 + 中文字幕
  ↓
跳过翻译
  ↓
生成封面和 B 站信息
  ↓
合并双语字幕到视频
  ↓
准备上传
```

### 场景 3：无字幕

```
YouTube 视频（无字幕）
  ↓
下载视频
  ↓
提示：请手动导出字幕
  ↓
退出（等待手动操作）
```

**手动导出字幕后：**
1. 将字幕命名为：`视频名.en.vtt` 或 `视频名.en.srt`
2. 放到 `data/` 目录
3. 运行 `./auto_process.sh` 继续处理

---

## 📂 输出结构

```
output/
└── 视频名/
    ├── video_bilingual_soft.mp4           # 带软字幕的视频
    ├── 视频名_bilingual.srt               # 双语字幕文件
    ├── 视频名_en.srt                      # 英文字幕
    ├── 视频名_zh.srt                      # 中文字幕
    ├── modern.jpg                         # 封面（modern 方案）
    ├── vibrant.jpg                        # 封面（vibrant 方案）
    ├── elegant.jpg                        # 封面（elegant 方案）
    ├── fresh.jpg                          # 封面（fresh 方案）
    ├── cover_texts.json                   # AI 生成的文案
    └── bilibili_upload_config.json        # B 站上传配置
```

---

## 🎬 上传到 B 站

### 方法 1：手动上传（推荐）

1. 打开 B 站创作中心：https://member.bilibili.com/platform/upload/video/frame
2. 上传 `video_bilingual_soft.mp4`
3. 上传封面 `modern.jpg`
4. 复制 `cover_texts.json` 中的信息：
   - `bilibili_title` → 标题
   - `bilibili_tags` → 标签
   - `bilibili_description` → 简介
5. 选择"自制"类型
6. 提交投稿

### 方法 2：自动上传（需要 MCP Playwright）

```bash
# 1. 准备上传配置
./prepare_upload.sh "output/视频名/"

# 2. 在 Cursor 中告诉 AI：
# "请使用 MCP Playwright 帮我上传这个视频到B站"
```

---

## ⚙️ 高级选项

### 自定义工作目录

```bash
python3 src/youtube_to_bilibili.py "URL" --work-dir "/path/to/dir"
```

### 直接准备上传

```bash
python3 src/youtube_to_bilibili.py "URL" --prepare-upload
```

### 自动上传（实验性）

```bash
python3 src/youtube_to_bilibili.py "URL" --auto-upload
```

---

## 🛠️ 故障排查

### 问题 1：下载失败

**错误：** `ERROR: unable to download video data`

**解决方案：**
1. 检查 URL 是否正确
2. 检查网络连接
3. 尝试更新 yt-dlp：`pip install -U yt-dlp`
4. 如果是受限视频，确保 Chrome 已登录 YouTube

### 问题 2：未找到字幕

**提示：** `⚠️  未找到英文字幕，需要手动导出`

**解决方案：**
1. 打开 YouTube 视频页面
2. 点击"..."菜单 → "显示字幕文本"
3. 复制字幕内容
4. 保存为 `视频名.en.vtt` 或 `视频名.en.srt`
5. 放到 `data/` 目录
6. 运行 `./auto_process.sh`

### 问题 3：翻译失败

**错误：** `❌ 翻译失败`

**解决方案：**
1. 检查 DeepSeek API Key 是否正确
2. 检查 API 余额
3. 检查网络连接
4. 查看详细错误信息

### 问题 4：封面生成失败

**错误：** `❌ 封面生成失败`

**解决方案：**
1. 检查视频文件是否完整
2. 检查 DeepSeek API Key
3. 手动运行：`./cover.sh data/视频.mp4`

### 问题 5：视频合成失败

**错误：** `❌ 视频合成失败`

**解决方案：**
1. 检查 ffmpeg 是否已安装：`ffmpeg -version`
2. 检查字幕文件格式是否正确
3. 手动运行合成命令

---

## 💻 命令行选项

```bash
python3 src/youtube_to_bilibili.py --help
```

**参数：**
- `youtube_url`: YouTube 视频链接（必需）
- `--work-dir DIR`: 工作目录（默认：`./data`）
- `--prepare-upload`: 准备上传配置
- `--auto-upload`: 自动上传到 B 站（需要 MCP Playwright）

---

## 📊 性能指标

| 操作 | 时间 | 说明 |
|------|------|------|
| 下载视频（1小时） | 5-10分钟 | 取决于网络速度 |
| 翻译字幕（3000行） | 2-5分钟 | 智能分段翻译 |
| 生成封面 | 10-20秒 | 4种方案 |
| 合并软字幕 | 1-2秒 | 无需转码 |
| **总计** | **约10-20分钟** | 全自动 |

---

## 🎓 最佳实践

### 1. 批量处理

```bash
# 创建视频列表
cat > videos.txt <<EOF
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/watch?v=VIDEO_ID_3
EOF

# 批量处理
while read url; do
    ./youtube_to_bilibili.sh "$url"
done < videos.txt
```

### 2. 定时任务

```bash
# 添加到 crontab
# 每天凌晨2点处理 YouTube 视频
0 2 * * * cd /path/to/vedio-tools && ./youtube_to_bilibili.sh "URL"
```

### 3. 后台运行

```bash
# 后台运行并记录日志
nohup ./youtube_to_bilibili.sh "URL" > youtube_process.log 2>&1 &

# 查看进度
tail -f youtube_process.log
```

---

## 🔗 相关文档

- [USAGE.md](USAGE.md) - 详细使用指南
- [BILIBILI_UPLOAD_GUIDE.md](BILIBILI_UPLOAD_GUIDE.md) - B 站上传指南
- [README.md](../README.md) - 项目概述

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**享受自动化带来的便利！🎉**


# 🚀 快速开始

## ⚡ 最快上手（3步）

```bash
# 1. 设置 API Key
export DEEPSEEK_API_KEY="your_api_key"

# 2. 进入目录
cd vedio-tools

# 3. 启动自动处理
./auto_process.sh
```

选择 **2) 持续监控**，然后把视频放到 `data` 目录，一切自动完成！

---

## 📋 快捷脚本速查

| 脚本 | 功能 | 用法 |
|------|------|------|
| `./auto_process.sh` | 自动处理系统 ⭐⭐⭐ | `./auto_process.sh` |
| `./translate.sh` | 翻译字幕 | `./translate.sh video.en.vtt` |
| `./cover.sh` | 生成封面 | `./cover.sh video.mp4` |
| `./merge_subtitle.sh` | 合并字幕 | `./merge_subtitle.sh video.webm video.en.vtt video.zh.vtt` |
| `./burn_subtitle.sh` | 烧录硬字幕 | `./burn_subtitle.sh video.webm` |
| `./show_output.sh` | 查看输出 | `./show_output.sh --list` |

---

## 🎬 常见场景

### 场景1：处理一个新视频

```bash
# 1. 翻译字幕
./translate.sh ./data/video.en.vtt

# 2. 生成封面和B站信息
./cover.sh ./data/video.webm

# 3. 查看输出
./show_output.sh "video"
```

### 场景2：批量处理多个视频

```bash
# 启动自动处理，选择"持续监控"
./auto_process.sh
```

### 场景3：只生成B站硬字幕

```bash
# 在新终端窗口运行（15-20分钟）
./burn_subtitle.sh ./data/video.webm
```

---

## 📊 进度显示

翻译时会显示：

```
🤖 翻译批次 5/47 (大小: 48, 待翻译: 48)...
   首条: So the question is...
   末条: ...artificial intelligence?
   ✅ 批次完成
   📊 总进度: [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 20% (116/581)
```

---

## 📁 输出位置

所有文件统一在 `output/视频名/` 目录：

```
output/
└── NVIDIA CEO Jensen Huang's Vision for the Future/
    ├── cover_texts.json              # AI生成（含B站信息）
    ├── modern.jpg                    # 封面
    ├── vibrant.jpg
    ├── elegant.jpg
    ├── fresh.jpg
    ├── video_bilingual_soft.mp4      # 带字幕视频
    ├── video_bilingual_soft.srt      # 双语字幕
    ├── video_zh.srt                  # 中文字幕（B站）
    └── video_en.srt                  # 英文字幕（B站）
```

---

## ⚙️ 配置文件

修改 `config.yaml` 自定义设置：

```yaml
subtitle:
  type: soft          # 软字幕（快）或 hard（兼容）
  font_size: 20       # 字体大小

translation:
  translator: smart   # 翻译器版本
  target_size: 50     # 批次大小

auto_process:
  check_interval: 60  # 检查间隔（秒）
```

---

💡 **推荐**：使用 `./auto_process.sh` 全自动处理！


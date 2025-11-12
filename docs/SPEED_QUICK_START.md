# 视频分段变速 - 快速上手指南

## 🚀 5分钟快速上手

### 第一步：准备配置文件

创建一个 JSON 文件（例如 `my_speed.json`），定义要调整速度的片段：

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
        },
        {
            "timestamp": "00:01:10 - 00:01:20",
            "speed": 1.3
        }
    ]
}
```

### 第二步：运行处理

```bash
./adjust_speed.sh 你的视频.mp4 my_speed.json 输出视频.mp4
```

### 第三步：查看结果

完成！视频已经按照您的配置调整好速度了。

---

## 💡 实用场景示例

### 场景1：跳过开场废话

```json
{
    "part": [
        {
            "timestamp": "00:00:00 - 00:01:30",
            "speed": 1.8,
            "comment": "快速跳过开场介绍"
        }
    ]
}
```

### 场景2：重点内容减速

```json
{
    "part": [
        {
            "timestamp": "00:05:20 - 00:06:00",
            "speed": 0.7,
            "comment": "减慢重要讲解部分"
        }
    ]
}
```

### 场景3：混合节奏

```json
{
    "part": [
        {
            "timestamp": "00:00:00 - 00:00:30",
            "speed": 1.0,
            "comment": "开场正常"
        },
        {
            "timestamp": "00:00:30 - 00:02:00",
            "speed": 1.5,
            "comment": "加快铺垫内容"
        },
        {
            "timestamp": "00:02:00 - 00:04:00",
            "speed": 1.0,
            "comment": "核心内容正常"
        },
        {
            "timestamp": "00:04:00 - 00:05:00",
            "speed": 1.8,
            "comment": "快速过渡"
        }
    ]
}
```

---

## 🎯 参数说明

### 时间戳格式

支持三种格式：
- `HH:MM:SS` - 例如：`00:01:30`（1分30秒）
- `MM:SS` - 例如：`1:30`（1分30秒）
- `SS` - 例如：`90`（90秒）

### 速度值

- `1.0` = 正常速度
- `1.5` = 1.5倍速（加快50%）
- `0.8` = 0.8倍速（减慢20%）
- `2.0` = 2倍速（最快推荐值）
- `0.5` = 0.5倍速（最慢推荐值）

**建议范围**：0.5 - 2.0，超出范围可能影响音质。

---

## 🧪 快速测试

运行测试脚本，自动处理一个示例视频：

```bash
./test_speed_adjuster.sh
```

这会：
1. 自动找到一个测试视频
2. 应用示例速度配置
3. 生成输出到 `/tmp/test_speed_adjusted.mp4`

---

## 📝 常见问题

### Q: 未配置的时间段会怎样？

A: 自动保持原速播放，确保视频完整性。

### Q: 可以配置重叠的时间段吗？

A: 不建议。如果时间段重叠，后面的配置会被忽略。

### Q: 音频会变调吗？

A: 不会！工具使用了 `atempo` 滤镜，只改变速度，不改变音调。

### Q: 处理需要多长时间？

A: 大约是视频总时长的 1-2 倍。10分钟视频大约需要 10-20 分钟处理。

### Q: 可以处理多大的视频？

A: 理论上没有限制，但要确保有足够的临时磁盘空间（约为视频大小的 2-3 倍）。

---

## 🔧 高级用法

### 使用 Python 脚本直接调用

```bash
python3 src/speed_adjuster.py input.mp4 config.json output.mp4
```

### 使用 JSON 字符串

```bash
python3 src/speed_adjuster.py input.mp4 '{"part":[{"timestamp":"0:10-0:20","speed":1.5}]}' output.mp4
```

### 处理多个视频

```bash
#!/bin/bash
for video in videos/*.mp4; do
    ./adjust_speed.sh "$video" my_config.json "output/$(basename "$video")"
done
```

---

## 📚 更多资源

- 📖 [完整文档](docs/VIDEO_SPEED_ADJUSTMENT.md)
- 📝 [示例配置](speed_config_example.json)
- 🧪 [测试脚本](test_speed_adjuster.sh)

---

## ❓ 需要帮助？

1. 查看详细文档：`docs/VIDEO_SPEED_ADJUSTMENT.md`
2. 运行测试脚本验证功能：`./test_speed_adjuster.sh`
3. 查看示例配置：`speed_config_example.json`

享受视频编辑的乐趣！🎬✨


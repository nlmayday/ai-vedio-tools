# B站自动上传指南 📤

## 概述

使用 MCP Playwright 自动化上传视频到B站，全程无需手动操作。

## 🚀 快速开始

### 方法一：快捷脚本（推荐）

```bash
# 1. 准备上传
cd vedio-tools
./prepare_upload.sh "../output/视频名/"

# 2. 在 Cursor 中告诉 AI：
#    "请使用 MCP Playwright 帮我上传这个视频到B站"
```

### 方法二：直接使用 Python

```bash
python src/bilibili_auto_upload.py \
  --video-dir "../output/视频名/"
```

---

## 📋 前置要求

### 1. 浏览器登录

在使用自动上传前，需要先在浏览器中登录B站：

1. 打开浏览器
2. 访问 https://www.bilibili.com
3. 登录你的B站账号
4. 保持浏览器会话有效

### 2. MCP Playwright

确保 Cursor 已启用 MCP Playwright：

- 检查 Cursor 设置
- 确认 MCP Playwright 服务正常运行

### 3. 视频输出目录

确保输出目录包含以下文件：

```
output/视频名/
├── video_bilingual_soft.mp4  # 视频文件（或其他格式）
├── modern.jpg                 # 封面图（modern 方案）
└── cover_texts.json           # B站信息（标题、标签、简介）
```

---

## 🎯 使用步骤

### 步骤 1：准备上传配置

```bash
./prepare_upload.sh "../output/Nvidia CEO Jensen Huang Says More Growth Ahead For AI (Full Interview) [pzytyZLD3tU]/"
```

**输出内容：**
- 视频路径
- 封面路径
- 标题、标签、简介
- MCP Playwright 操作步骤
- 生成 `bilibili_upload_config.json`

### 步骤 2：在 Cursor 中请求 AI 上传

复制以下指令到 Cursor：

```
@prepare_upload.sh 的输出
请使用 MCP Playwright 帮我上传这个视频到B站
```

### 步骤 3：AI 自动执行上传

AI 会自动调用 MCP Playwright 工具：

1. ✅ 打开B站创作中心
2. ✅ 上传视频文件
3. ✅ 等待上传完成
4. ✅ 填写标题
5. ✅ 选择类型（自制）
6. ✅ 选择分区（动画）
7. ✅ 上传封面
8. ✅ 添加标签
9. ✅ 填写简介
10. ✅ 选择活动（第二个）
11. ✅ 点击投稿
12. ✅ 等待成功提示

### 步骤 4：等待审核

视频提交后会进入审核队列，通常 1-24 小时内完成审核。

---

## 🔧 配置说明

### cover_texts.json 格式

```json
{
  "bilibili_title": "视频标题（不超过80字符）",
  "bilibili_tags": [
    "标签1",
    "标签2",
    "标签3",
    "标签4",
    "标签5"
  ],
  "bilibili_description": "视频简介（200-1000字）"
}
```

### bilibili_upload_config.json

由 `prepare_upload.sh` 自动生成：

```json
{
  "video": "/path/to/video.mp4",
  "cover": "/path/to/cover.jpg",
  "title": "视频标题",
  "tags": ["标签1", "标签2"],
  "description": "视频简介",
  "category": "动画",
  "upload_url": "https://member.bilibili.com/platform/upload/video/frame"
}
```

---

## 📤 上传规则

### 类型选择

- **必须选择：自制**
- 转载视频无法通过审核

### 分区选择

- 默认：**动画**
- 可在脚本中修改为其他分区：
  - 知识
  - 科技
  - 生活
  - 等

### 标签限制

- 最多 10 个标签
- 标签应与视频内容相关
- 选择热门标签可提高曝光

### 简介要求

- 长度：200-1000 字
- 内容：介绍视频主题、亮点、适合人群
- 避免：敏感词汇、违规内容

---

## 🛠️ 故障排查

### 问题 1：未找到封面文件

**错误：** `FileNotFoundError: 未找到封面文件`

**解决方案：**
```bash
# 检查封面是否存在
ls ../output/视频名/*.jpg
ls ../output/视频名/*.png

# 如果没有，重新生成封面
./cover.sh ./data/视频.mp4
```

### 问题 2：未找到视频文件

**错误：** `FileNotFoundError: 未找到视频`

**解决方案：**
```bash
# 检查视频是否存在
ls ../output/视频名/*.mp4

# 如果没有，重新合并字幕
./merge_subtitle.sh ./data/视频.webm ./data/视频.en.vtt ./data/视频.zh.vtt
```

### 问题 3：未找到 cover_texts.json

**错误：** `FileNotFoundError: 未找到信息文件`

**解决方案：**
```bash
# 重新生成封面和信息
./cover.sh ./data/视频.mp4
```

### 问题 4：MCP Playwright 未响应

**解决方案：**
1. 检查 Cursor 中 MCP Playwright 是否启用
2. 重启 Cursor
3. 检查浏览器是否已登录B站

### 问题 5：上传失败

**可能原因：**
- 视频文件过大（建议 < 2GB）
- 视频格式不支持（建议 MP4）
- 网络连接问题
- B站服务器繁忙

**解决方案：**
```bash
# 检查视频大小
ls -lh ../output/视频名/*.mp4

# 如果过大，可以压缩（可选）
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4
```

---

## 💡 最佳实践

### 1. 批量上传

```bash
# 准备多个视频
for dir in ../output/*/; do
    echo "准备: $dir"
    ./prepare_upload.sh "$dir"
done

# 然后在 Cursor 中逐个请求 AI 上传
```

### 2. 自定义分区

修改 `src/bilibili_auto_upload.py`：

```python
# 第 12 行
CATEGORY = "知识"  # 改为你想要的分区
```

### 3. 优化标题

标题应该：
- 简洁有力（< 80 字符）
- 包含关键词
- 吸引眼球
- 避免标题党

### 4. 选择合适的封面

- 优先使用 modern 方案（简洁专业）
- 确保封面清晰、有吸引力
- 避免模糊或低质量图片

---

## 📊 上传流程图

```
┌─────────────────┐
│ 准备上传配置    │
│ prepare_upload  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 生成配置 JSON   │
│ config.json     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cursor AI 调用  │
│ MCP Playwright  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 打开B站上传页   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 上传视频文件    │
│ (等待完成)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 填写信息        │
│ (标题/标签/简介)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 选择类型/分区   │
│ (自制/动画)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 上传封面        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 提交投稿        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 等待审核        │
│ (1-24小时)      │
└─────────────────┘
```

---

## 🎓 示例

### 完整示例

```bash
# 1. 查看所有可上传的视频
./show_output.sh --list

# 2. 选择一个视频，准备上传
./prepare_upload.sh "../output/Nvidia CEO Jensen Huang Says More Growth Ahead For AI (Full Interview) [pzytyZLD3tU]/"

# 3. 输出示例：
# ✅ 配置加载完成
#    视频: video_bilingual_soft.mp4
#    封面: modern.jpg
#    标题: 英伟达CEO黄仁勋：AI黄金时代才刚刚开始！独家专访揭秘
#
# 📋 上传配置：
#    视频: /path/to/video.mp4
#    封面: /path/to/modern.jpg
#    标题: 英伟达CEO黄仁勋：AI黄金时代才刚刚开始！独家专访揭秘
#    标签: 人工智能, 英伟达, 黄仁勋, AI技术, 科技前沿
#
# 🔧 MCP Playwright 工具调用顺序：
# ...

# 4. 在 Cursor 中告诉 AI：
#    "请使用 MCP Playwright 帮我上传这个视频到B站"

# 5. AI 自动执行上传流程...

# 6. 上传成功！等待审核...
```

---

## 📚 相关文档

- [USAGE.md](USAGE.md) - 完整使用指南
- [README.md](../README.md) - 项目概述
- [B站上传规则](https://www.bilibili.com/blackboard/help.html#/?id=%E6%8A%95%E7%A8%BF%E8%A7%84%E8%8C%83)

---

## 🤝 支持

如有问题，请检查：

1. ✅ 是否已登录B站
2. ✅ MCP Playwright 是否正常
3. ✅ 视频、封面、信息文件是否完整
4. ✅ 网络连接是否正常

---

**享受自动化上传的便利！🎉**


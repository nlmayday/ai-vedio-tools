# YouTube视频转微信公众号文章工具

## 🎯 功能介绍

将YouTube视频（含字幕）自动转换为适合微信公众号发布的图文内容。

**核心功能：**
- ✅ 自动下载YouTube视频字幕
- ✅ 提取视频信息（标题、描述）
- ✅ 使用DeepSeek AI生成专业文章
- ✅ 支持多种文章风格
- ✅ 输出Markdown/JSON/纯文本格式
- ✅ 完美适配微信公众号排版

## 📋 安装依赖

```bash
cd vedio-tools

# 安装Python依赖
pip install -r requirements.txt

# 确保已安装yt-dlp
pip install yt-dlp
```

## ⚙️ 配置

### 1. 设置DeepSeek API Key

```bash
export DEEPSEEK_API_KEY='your-api-key-here'
```

或者在使用前设置：

```bash
# macOS/Linux
echo 'export DEEPSEEK_API_KEY="your-api-key"' >> ~/.zshrc
source ~/.zshrc

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your-api-key"
```

### 2. 配置Chrome Cookies（可选）

某些YouTube视频可能需要登录才能访问字幕，工具会自动从Chrome浏览器获取cookies。

确保你的Chrome浏览器已登录YouTube账号。

## 🚀 使用方法

### 基础用法

```bash
cd vedio-tools/src

python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx
```

### 高级选项

```bash
# 指定输出目录
python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx \
  --output ../output/my_article

# 指定文章字数
python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx \
  --word-count 3000

# 指定文章风格
python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx \
  --style casual

# 跳过下载（使用已有字幕）
python youtube_to_wechat.py https://www.youtube.com/watch?v=xxx \
  --skip-download

# 完整示例
python youtube_to_wechat.py https://www.youtube.com/watch?v=jt3Ul3rPXaE \
  --output ../output/harari_ai \
  --word-count 2500 \
  --style professional
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | YouTube视频URL（必需） | - |
| `-o, --output` | 输出目录 | `../output/{video_id}` |
| `-w, --word-count` | 目标字数 | `2000` |
| `-s, --style` | 文章风格 | `professional` |
| `--skip-download` | 跳过下载步骤 | `False` |

### 文章风格选项

- **professional**（专业）：适合商业、科技、教育类内容
- **casual**（轻松）：适合生活、娱乐、创意类内容
- **academic**（学术）：适合学术研究、深度分析类内容

## 📊 输出结果

执行完成后，会在输出目录生成以下文件：

```
output/{video_id}/
├── article.md          # Markdown格式（推荐用于公众号编辑器）
├── article.json        # JSON格式（包含完整元数据）
├── article.txt         # 纯文本格式（方便复制）
└── *.en.vtt           # 下载的字幕文件
```

### article.md 结构示例

```markdown
# AI如何改变人类未来？尤瓦尔·赫拉利深度解读

> 📌 在这场对话中，历史学家尤瓦尔·赫拉利深入探讨了AI技术对人类社会的深远影响...

---

## 💡 引言

赫拉利在视频开头就提出了一个引人深思的问题...

## 🎯 核心观点

### 观点1：AI将重构就业市场

赫拉利指出，与工业革命不同...

**关键数据：**
| 行业 | 影响程度 | 时间预测 |
|------|---------|----------|
| 客服 | 高 | 2-3年 |

### 观点2：AI与人类价值观的冲突

...

## 🤔 深度分析

结合赫拉利的观点和当前AI发展现状...

## 📝 总结

通过这次对话，我们可以得出以下启示：

✅ **关键收获：**
1. AI发展不可逆转
2. 教育系统需要变革
3. 建立AI伦理规范刻不容缓

💭 **思考题：**
- 你认为AI会在多久后取代你的工作？

---

**标签：** #AI #人工智能 #未来

**阅读时间：** 约8分钟

**原视频标题：** AI and human evolution | Yuval Noah Harari
```

## 🎨 微信公众号发布流程

### 1. 复制Markdown内容

```bash
# 查看生成的文章
cat output/{video_id}/article.md

# 或者打开文件
open output/{video_id}/article.md
```

### 2. 使用Markdown编辑器

推荐工具：
- [Markdown Nice](https://editor.mdnice.com/) - 在线Markdown编辑器
- [秀米](https://xiumi.us/) - 微信公众号排版工具
- [壹伴](https://yiban.io/) - 微信编辑器插件

### 3. 调整样式

- 选择合适的主题配色
- 调整字号和行距
- 添加封面图（可从视频截图）
- 检查排版效果

### 4. 复制到公众号

在编辑器中预览无误后，复制HTML代码到微信公众号后台。

## 📝 实际案例

### 案例1：尤瓦尔·赫拉利 - AI与人类进化

```bash
python youtube_to_wechat.py https://www.youtube.com/watch?v=jt3Ul3rPXaE \
  --word-count 2500 \
  --style professional
```

**输出效果：**
- ✅ 标题：《AI如何改变人类未来？尤瓦尔·赫拉利深度解读》
- ✅ 字数：2,456字
- ✅ 阅读时间：约8分钟
- ✅ 核心要点：3个
- ✅ 处理时间：约2分钟

### 案例2：马斯克访谈 - 生命的意义

```bash
python youtube_to_wechat.py https://www.youtube.com/watch?v=4l7XHQWHzLA \
  --word-count 3000 \
  --style casual
```

**输出效果：**
- ✅ 标题：《马斯克最新访谈：生命的真正意义是什么？》
- ✅ 字数：3,124字
- ✅ 风格：轻松有趣
- ✅ 互动元素：5个思考题

## ⚡ 性能优化

### 提高处理速度

1. **跳过视频下载**（只下载字幕）
   ```bash
   # 工具默认只下载字幕，不下载视频
   # 已经优化，速度很快
   ```

2. **使用已有字幕**
   ```bash
   python youtube_to_wechat.py URL --skip-download
   ```

3. **批量处理**
   ```bash
   # 创建批量处理脚本
   cat urls.txt | while read url; do
       python youtube_to_wechat.py "$url"
   done
   ```

### 减少API成本

1. **合理设置字数**
   ```bash
   # 较短的文章（1500字）成本更低
   python youtube_to_wechat.py URL --word-count 1500
   ```

2. **复用生成结果**
   ```bash
   # 生成的JSON文件可以重复使用
   # 不需要每次都重新生成
   ```

## 🔧 故障排除

### 问题1：下载字幕失败

**可能原因：**
- 视频没有英文字幕
- 需要登录才能访问
- 网络连接问题

**解决方案：**
```bash
# 1. 手动下载字幕
yt-dlp --write-subs --write-auto-subs --sub-langs en --skip-download URL

# 2. 检查是否有字幕
yt-dlp --list-subs URL

# 3. 使用代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

### 问题2：DeepSeek API调用失败

**可能原因：**
- API Key未设置
- API配额用完
- 网络问题

**解决方案：**
```bash
# 检查API Key
echo $DEEPSEEK_API_KEY

# 测试API连接
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

### 问题3：文章质量不理想

**优化建议：**

1. **调整字数**
   ```bash
   # 增加字数可以获得更详细的内容
   python youtube_to_wechat.py URL --word-count 3000
   ```

2. **更换风格**
   ```bash
   # 尝试不同的风格
   python youtube_to_wechat.py URL --style casual
   ```

3. **手动编辑**
   - 生成后的Markdown文件可以手动编辑
   - 调整结构和措辞
   - 添加自己的见解

### 问题4：JSON解析失败

**原因：** DeepSeek返回的内容格式不正确

**解决方案：**
- 工具会自动降级处理
- 检查 `article.json` 中的原始响应
- 可以手动编辑 `article.md`

## 🎯 最佳实践

### 1. 选择合适的视频

**适合的视频类型：**
- ✅ 采访对话（观点清晰）
- ✅ 教育讲座（结构完整）
- ✅ 行业分析（内容深度）
- ✅ 时长10-30分钟（字幕适中）

**不适合的视频：**
- ❌ 纯娱乐视频（缺乏深度）
- ❌ 音乐MV（字幕太少）
- ❌ 游戏实况（内容零散）
- ❌ 超长视频（>1小时，字幕太多）

### 2. 优化文章结构

生成后可以手动调整：
- 添加小标题层级
- 插入引用块
- 添加数据表格
- 补充案例分析

### 3. 增强互动性

在文末添加：
- 投票问题
- 讨论话题
- 相关推荐
- 引导关注

### 4. 配合封面图

可以使用项目中的封面生成工具：
```bash
# 从视频生成封面
python thumbnail_generator.py \
  --video video.mp4 \
  --title "文章标题" \
  --output cover.jpg
```

## 📚 相关工具

本项目提供的其他有用工具：

1. **字幕翻译**
   ```bash
   python subtitle_translator_smart.py input.vtt output.vtt
   ```

2. **封面生成**
   ```bash
   python thumbnail_generator.py --video video.mp4 --title "标题"
   ```

3. **B站上传**
   ```bash
   python bilibili_uploader.py video.mp4
   ```

## 💡 进阶使用

### Python模块方式调用

```python
from youtube_to_wechat import YouTubeToWechatConverter

# 创建转换器
converter = YouTubeToWechatConverter(
    youtube_url="https://www.youtube.com/watch?v=xxx",
    output_dir="./output"
)

# 执行转换
success = converter.convert(
    word_count=2000,
    style="professional"
)

if success:
    print("转换成功！")
```

### 自定义文章生成

```python
from wechat_article_generator import WechatArticleGenerator
from subtitle_parser import parse_subtitle

# 创建生成器
generator = WechatArticleGenerator(api_key="your-key")

# 解析字幕
subtitle_blocks = parse_subtitle("video.vtt")

# 生成文章
article = generator.generate_article(
    video_title="视频标题",
    video_description="视频描述",
    subtitle_blocks=subtitle_blocks,
    word_count=2000,
    style="professional"
)

# 保存文章
generator.save_article(article, "./output", "video_id")
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

如有问题，请在GitHub上提Issue。

# B站上传工具 — 开发状态总结

**日期:** 2026-04-29  
**工具:** `src/bilibili_uploader.py`  
**方案:** playwright-cli 命令行自动化（非 MCP，非 Selenium）

---

## 一、做了什么

### 1. 整体架构

```
bilibili_uploader.py (主上传工具)
├── JS 模板 (内嵌 Python) → 导航、填表、上传视频、等待完成
└── Python 封面分步流程 → 4 个 mini JS 脚本 + playwright-cli upload
```

**为什么用 playwright-cli 而不是 MCP Playwright：**
- MCP Playwright 每次操作要走 MCP 协议往返，速度慢
- `playwright-cli run-code --filename` 可以一次性执行整段 JS，效率高
- `playwright-cli upload` 可以处理原生文件选择器（`page.waitForEvent('filechooser')` 在 run-code 里不可用）

### 2. 主上传流程（JS 模板，内嵌在 Python 的 `UPLOAD_SCRIPT_TEMPLATE`）

已实现的功能：

| 功能 | 状态 | 备注 |
|------|------|------|
| 导航到上传页 | ✅ | `member.bilibili.com/platform/upload/video/frame` |
| 登录检测与等待 | ✅ | 检测 URL 含 login/passport，等待 5 分钟 |
| 草稿弹窗关闭 | ✅ | 点击「不用了」关闭恢复草稿提示 |
| 视频文件选择 | ✅ | `input[type="file"]` 第一个（隐藏 input），`setInputFiles` |
| 标题填写 | ✅ | `input[placeholder*="标题"]` |
| 类型选择 | ✅ | 自制/转载，`.check-radio-v2-container` |
| 分区选择 | ✅ | 点击分区区域 → 下拉菜单中点选 |
| 标签填写 | ✅ | 先清除默认标签，逐个输入 + Enter，最多 10 个 |
| 简介填写 | ✅ | Quill 富文本编辑器 `div.ql-editor`，用 `page.evaluate` 设置 innerHTML |
| 合集选择 | ✅ | 展开 `.season-enter` → 搜索 → 点选 |
| 等待上传完成 | ✅ | 轮询检测「上传成功」文字或进度条消失 |
| 封面设置 | ⚠️ | 见下方「封面流程」 |

### 3. 封面分步上传流程（Python 层，4 个 Step）

B站封面编辑器有两个上传区域：
- **4:3 首页推荐** — 第一个上传区域
- **16:9 个人空间** — 第二个上传区域

每点击一次「上传封面」会触发**原生文件选择器**，需要用 `playwright-cli upload` 命令来投递文件。

当前流程：

```
Step 1: 点击「封面设置」打开封面编辑器
Step 2: 点击第一个「上传封面」→ playwright-cli upload 投递封面
Step 3: 点击第二个「上传封面」→ playwright-cli upload 投递封面
Step 4: 点击「确定」保存并关闭封面编辑器
```

文件选择器处理方式：
- 将封面复制到 `scripts/.cover_temp.jpg`（必须在项目目录内，playwright-cli 有根目录限制）
- 重试 5 次 `playwright-cli -s=default upload <file>`，每次间隔 1 秒
- 检测输出中是否包含 `fileChooser.setFiles` 判断成功

### 4. 浏览器生命周期管理

```
启动: playwright-cli open --headed --profile ~/.bilibili-playwright-profile
检测: playwright-cli list (检查 status: open)
关闭: playwright-cli eval "location.href='about:blank'"  → playwright-cli close
```

关闭前先导航到 `about:blank` 避免下次打开时 Chrome 弹出「恢复页面」提示。

### 5. 元数据生成器 `src/bilibili_metadata_generator.py`

独立工具，调用 DeepSeek API 根据字幕内容生成 B站元数据：
- bilibili_title: 标题（20-40字）
- bilibili_tags: 标签（8-10个）
- bilibili_description: 简介（200-500字）
- cover_title1/cover_title2: 封面主标题
- cover_subtitle_cn/en: 封面副标题
- cover_lines: 封面短句（3-4条）

输出到 `output/<id>/bilibili_meta.json`，供 uploader 读取。

---

## 二、仍然存在的问题

### 问题 1：封面第二步上传不稳定 ⚠️

**现象：** 第一个 4:3 封面有时能上传成功，但第二个 16:9 封面经常不上传，或者上传后页面卡在等待状态。

**可能原因：**
- 上传第一个封面后，B站页面可能自动将 4:3 的图同步到 16:9，导致第二个上传区域被替换或隐藏
- 文件选择器触发时机不稳定——点击后到文件选择器出现之间有延迟
- 如果 B站已经双比例自动同步，第二步其实是多余的

**建议处理方式：**
- 先确认 B站当前版本是否已支持双比例自动同步
- 如果支持，上传第一个后直接点确定即可
- 如果不支持，需要在上传第二个前等待更长时间，确保 DOM 稳定

### 问题 2：封面「确定」按钮定位不稳定 ⚠️

**现象：** `.bcc-button--primary` 在页面中匹配多个元素（包括「添加分P」等），需要精确限定在 `.bcc-dialog__footer` 内。

**当前方案：** 用 `page.evaluate` 执行 `document.querySelector('.bcc-dialog__footer .bcc-button--primary')` 并 `.click()`，绕过 Playwright 的可见性检查。

**风险：** B站改版后 CSS 类名可能变化。

### 问题 3：合集选择器可能不稳定 ⚠️

**现象：** 合集选择依赖 `.season-enter` 类名和文本匹配，B站页面结构变化后可能失效。

### 问题 4：视频上传 input 选择器 ⚠️

**现象：** 页面有 5 个 `input[type="file"]`（0=隐藏视频 .mp4, 1=隐藏图片 image/png, 2=可见视频 .mp4, 3=.txt, 4=.zip）。当前用 `.first()` 选第 0 个（隐藏 input）来上传视频，它确实能用（`setInputFiles` 对隐藏元素也有效），但不是「正确」的那个。

**风险：** 如果 B站把隐藏 input 的 accept 属性改掉，或者改变 input 顺序，上传会失败。

### 问题 5：未做端到端完整验证 ❌

**现象：** 今天的测试被中断了多次，没有完成一次完整的「视频上传 → 填表 → 封面上传 → 确认保存」全流程验证。

**需要：**
- 从头到尾跑一次完整的流程
- 确认封面在上传后正确显示在主页面上
- 确认所有字段在提交前都正确填充

### 问题 6：playwright-cli 依赖 ⚠️

**说明：** `playwright-cli` 是 Playwright 官方的新 CLI 工具，当前版本 `v1.60.0-alpha`。它提供了 `open`、`run-code`、`eval`、`upload`、`close` 等命令，但不支持 `page.waitForEvent('filechooser')` 在 `run-code` 中使用。

**风险：** alpha 版本 API 可能变化，`upload` 命令的 root 限制逻辑也可能改动。

---

## 三、使用方式

```bash
# 1. 生成元数据
python src/bilibili_metadata_generator.py \
    --title "视频标题" \
    --subtitle output/725/en_readable.srt \
    --output output/725/bilibili_meta.json

# 2. 上传视频
python src/bilibili_uploader.py \
    --video-dir ../output/725/ \
    --collection "TED-趣味-学英语" \
    --partition "知识"

# 3. 上传完成后在浏览器中检查，手动点击「立即投稿」

# 4. 关闭浏览器
playwright-cli -s=default eval "location.href='about:blank'"
playwright-cli close
```

### 目录结构要求

```
output/<视频id>/
├── xxx_bilingual.mp4   # 视频文件（优先 *_bilingual.mp4）
├── modern.jpg          # 封面图片
├── bilibili_meta.json  # 元数据（标题、标签、简介等）
└── ...                 # 字幕等（不影响上传）
```

---

## 四、相关文件

| 文件 | 用途 |
|------|------|
| `src/bilibili_uploader.py` | 主上传工具（playwright-cli 版） |
| `src/bilibili_metadata_generator.py` | B站元数据 AI 生成器 |
| `src/bilibili_auto_upload.py` | 旧版上传工具（MCP Playwright 版，供 AI 参考） |
| `scripts/bilibili_upload.js` | 独立 JS 版上传脚本（手动执行用） |
| `scripts/test_playwright.js` | playwright-cli 测试脚本 |
| `output/725/` | 测试数据目录（丝绸之路视频） |

---

## 五、下一步建议

1. **优先级高：** 完成一次端到端测试，确认基本流程可跑通
2. **优先级高：** 确认 B站封面是否已支持双比例自动同步（如果是，删掉 Step 3）
3. **优先级中：** 用更稳定的选择器替换视频 input 选择（如 `input[type="file"][accept*=".mp4"]`）
4. **优先级中：** 封面流程加截图调试（`page.screenshot`），方便排查失败原因
5. **优先级低：** 考虑把所有 JS 代码移到独立的 `.js` 文件中，方便独立调试和版本管理

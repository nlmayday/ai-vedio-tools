#!/usr/bin/env python3
"""
B站视频自动上传工具 - 使用 playwright-cli 自动化上传 (优化版)
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROFILE_DIR = Path.home() / ".bilibili-playwright-profile"
BILIBILI_UPLOAD_URL = "https://member.bilibili.com/platform/upload/video/frame"

# ── 脚本 1：基础上传与置顶 ──
PHASE1_TEMPLATE = r"""async (page) => {
  const info = {{INFO_JSON}};
  
  page.on('dialog', async d => { await d.accept().catch(() => {}); });
  await page.evaluate(() => { window.onbeforeunload = null; });

  console.log('Navigating to B站 upload page...');
  await page.goto('https://member.bilibili.com/platform/upload/video/frame', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  // 登录检测
  if (page.url().includes('login') || page.url().includes('passport')) {
    console.log('⚠️  需要登录！等待 1 分钟...');
    await page.waitForTimeout(60000);
  }

  // 关闭草稿弹窗
  try {
    const dismissBtn = page.locator('text=不用了').first();
    if (await dismissBtn.count() > 0) { await dismissBtn.click(); await page.waitForTimeout(1000); }
  } catch {}

  console.log('📤 Uploading video...');
  const fileInput = page.locator('input[type="file"][accept*="video"], input[type="file"][accept*=".mp4"]').first();
  await fileInput.setInputFiles(info.video);
  await page.waitForTimeout(3000);

  console.log('📝 Filling title...');
  const titleInput = page.locator('input[placeholder*="标题"]').first();
  if (await titleInput.count() > 0) {
    await titleInput.fill('');
    await titleInput.fill(info.title);
  }

  // 强力置顶
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    document.querySelectorAll('*').forEach(el => {
      if (el.scrollHeight > el.clientHeight) el.scrollTop = 0;
    });
  });
  
  return 'phase1_done';
}"""

# ── 脚本 2：填写其余信息 ──
PHASE2_TEMPLATE = r"""async (page) => {
  const info = {{INFO_JSON}};
  const tags = info.tags.slice(0, 10);

  console.log('📝 Filling metadata...');
  
  // 分区
  if (info.partition) {
    try {
      const pArea = page.locator('.video-human-type [cursor="pointer"], [class*="human-type"] [class*="select"]').first();
      if (await pArea.count() > 0) {
        await pArea.click();
        await page.waitForTimeout(1000);
        await page.locator(`text="${info.partition}"`).first().click();
      }
    } catch {}
  }

  // 标签
  try {
    const closeBtns = page.locator('[class*="tag"] [class*="close"], .tag-item .remove');
    const count = await closeBtns.count();
    for (let i = 0; i < count; i++) { await closeBtns.nth(0).click(); await page.waitForTimeout(200); }
    const tagInput = page.locator('input[placeholder*="标签"]').first();
    for (const tag of tags) {
      await tagInput.fill(tag);
      await tagInput.press('Enter');
      await page.waitForTimeout(300);
    }
  } catch {}

  // 简介
  try {
    await page.evaluate((desc) => {
      const el = document.querySelector('.ql-editor');
      if (el) { el.innerHTML = desc.replace(/\n/g, '<br>'); el.classList.remove('ql-blank'); }
    }, info.description);
  } catch {}

  // 合集（列表型下拉：先有「请选择合集」「+ 创建合集」，再在浮层内点目标名称）
  if (info.collection) {
    const colName = info.collection;
    try {
      await page.evaluate(() => { window.scrollTo(0, document.documentElement.scrollHeight); });
      await page.waitForTimeout(400);

      const h3Season = page.locator('h3').filter({ hasText: /^加入合集$/ }).first();
      let already = 0;
      if (await h3Season.count() > 0) {
        await h3Season.scrollIntoViewIfNeeded();
        const block = h3Season.locator('..').locator('..');
        const content = block.locator(':scope > div').nth(1);
        already = await content.getByText(colName, { exact: true }).count();
      }
      if (already > 0) {
        console.log('合集已是目标: ' + colName);
      } else {
        const legacy = page.locator('.season-enter').first();
        const triggerBox = page.getByText('请选择合集', { exact: true }).first();

        if (await triggerBox.count() > 0) {
          await triggerBox.scrollIntoViewIfNeeded();
          await triggerBox.click();
        } else if (await legacy.count() > 0) {
          await legacy.scrollIntoViewIfNeeded();
          await legacy.click();
        } else if (await h3Season.count() > 0) {
          const block = h3Season.locator('..').locator('..');
          const content = block.locator(':scope > div').nth(1);
          const row = content.locator('[cursor="pointer"]').first();
          if (await row.count() > 0) await row.click();
          else await page.locator('text=选择合集').first().click().catch(() => {});
        }
        await page.waitForTimeout(700);

        // 合集下拉面版：带「创建合集」的 bcc 浮层里点准确全名（避免点到页面别处同名节点）
        const listPanel = page
          .locator('.bcc-popover, [class*="bcc-popover"], [class*="bcc-select-dropdown"]')
          .filter({ hasText: '创建合集' })
          .last();
        let picked = false;
        if (await listPanel.count() > 0) {
          const searchInPanel = listPanel.locator('input[type="text"], input:not([type="checkbox"])').first();
          if (await searchInPanel.count() > 0) {
            await searchInPanel.fill(colName);
            await page.waitForTimeout(500);
          }
          const opt = listPanel.getByText(colName, { exact: true }).first();
          if (await opt.count() > 0) {
            await opt.scrollIntoViewIfNeeded();
            await opt.click({ timeout: 8000 });
            picked = true;
          }
        }
        if (!picked) {
          picked = await page.evaluate((name) => {
            const visible = el => !!(el && el.offsetParent !== null && el.getClientRects().length);
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const pops = Array.from(
              document.querySelectorAll('.bcc-popover, [class*="bcc-popover"], [class*="bcc-select-dropdown"], [role="listbox"]'),
            ).filter(visible);
            const roots = pops.filter(el => norm(el.innerText).includes('创建合集'));
            const searchRoot = roots.length ? roots[roots.length - 1] : document.body;
            const cand = Array.from(searchRoot.querySelectorAll('div, li, span, a, p'))
              .filter(visible)
              .find(el => norm(el.textContent) === name || norm(el.innerText) === name);
            if (!cand) return false;
            const clickEl = cand.closest('[cursor="pointer"], [role="option"], li') || cand;
            clickEl.scrollIntoView({ block: 'center' });
            clickEl.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
            if (typeof clickEl.click === 'function') clickEl.click();
            return true;
          }, colName);
        }
        if (!picked) {
          const fallback = page.getByText(colName, { exact: true }).last();
          if (await fallback.count() > 0) {
            await fallback.scrollIntoViewIfNeeded();
            await fallback.click({ timeout: 5000 });
          }
        }
        await page.waitForTimeout(400);
        await page.keyboard.press('Escape').catch(() => {});
      }
    } catch (e) {
      console.log('合集选择失败:', e.message);
    }
  }

  console.log('⏳ Waiting for upload status...');
  for (let i = 0; i < 60; i++) {
    const done = await page.locator('text=上传成功|text=已上传|text=视频预览|text=上传完成').count();
    if (done > 0) break;
    await page.waitForTimeout(5000);
  }

  return 'phase2_done';
}"""

COVER_OPEN_TEMPLATE = r"""async (page) => {
  await page.evaluate(() => {
    window.onbeforeunload = null;
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(500);

  const fixedEntry = page.locator('.cover-main .edit-text, .cover-item .edit-text').first();
  if (await fixedEntry.count() > 0) {
    console.log('Cover entry selector: .cover-main .edit-text, .cover-item .edit-text');
    await fixedEntry.scrollIntoViewIfNeeded();
    await fixedEntry.click();
    await page.waitForTimeout(2000);
  } else {
    console.log('Cover entry fixed selector not found, using text fallback');
    const targetInfo = await page.evaluate(() => {
    const visible = el => !!(el && el.offsetParent !== null);
    const text = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    const clickableScore = el => {
      const tag = el.tagName.toLowerCase();
      const cls = el.className ? String(el.className) : '';
      let score = 0;
      if (['button', 'a'].includes(tag)) score += 10;
      if (el.getAttribute('role') === 'button') score += 8;
      if (/button|btn|cover|bcc/i.test(cls)) score += 5;
      return score;
    };
    const candidates = Array.from(document.querySelectorAll('button, a, [role="button"], div, span'))
      .filter(visible)
      .filter(el => /封面设置|设置封面|编辑封面|更改封面/.test(text(el)))
      .sort((a, b) => {
        const scoreDiff = clickableScore(b) - clickableScore(a);
        if (scoreDiff !== 0) return scoreDiff;
        return text(a).length - text(b).length;
      });
    if (!candidates.length) {
      return { ok: false, reason: '找不到可见的「设置封面/封面设置」入口' };
    }
    const target = candidates[0];
    target.scrollIntoView({ block: 'center', inline: 'center' });
    const box = target.getBoundingClientRect();
    return {
      ok: true,
      candidates: candidates.slice(0, 5).map(text),
      x: box.left + box.width / 2,
      y: box.top + box.height / 2,
    };
    });

    if (!targetInfo.ok) throw new Error(targetInfo.reason);
    console.log('Cover entry candidates:', targetInfo.candidates.join(' | '));
    await page.mouse.click(targetInfo.x, targetInfo.y);
    await page.waitForTimeout(2000);
  }

  const uploadButtons = await page.locator('text=上传封面').count();
  const dialogHints =
    await page.locator('text=首页推荐封面').count() +
    await page.locator('text=个人空间封面').count() +
    await page.locator('text=封面裁剪').count() +
    await page.locator('text=完成').count();
  console.log(`Cover dialog hints=${dialogHints}, uploadButtons=${uploadButtons}`);
  if (uploadButtons === 0 && dialogHints === 0) {
    throw new Error('已点击封面入口，但未检测到封面弹窗或上传按钮');
  }

  return 'cover_opened';
}"""

COVER_UPLOAD_TEMPLATE = r"""async (page) => {
  const label = {{LABEL_JSON}};
  const uploadIndex = {{UPLOAD_INDEX}};
  const cover = {{COVER_JSON}};

  const fileInputSel = 'input[type="file"][accept*="image"], input[type="file"][accept*=".jpg"], input[type="file"][accept*=".jpeg"], input[type="file"][accept*=".png"]';
  const coverDialog = page.locator('.bcc-dialog, [class*="bcc-dialog"], [role="dialog"]').filter({ hasText: '封面制作' }).first();
  let imageInputs = coverDialog.locator(fileInputSel);
  let imageInputCount = await imageInputs.count();
  if (imageInputCount === 0) {
    imageInputs = page.locator(fileInputSel);
    imageInputCount = await imageInputs.count();
  }
  console.log(`Image file inputs: ${imageInputCount}, uploadIndex=${uploadIndex} (scoped to 封面制作 when possible)`);
  if (imageInputCount > 0 && uploadIndex < imageInputCount) {
    await imageInputs.nth(uploadIndex).setInputFiles(cover);
    await page.waitForTimeout(1500);
    console.log('__BILI_COVER_UPLOAD__=direct');
    return 'cover_direct_input_uploaded';
  }
  if (imageInputCount > 0 && uploadIndex >= imageInputCount) {
    console.log(`Direct file input skip: need index ${uploadIndex} but only ${imageInputCount} inputs — fall back to click 上传`);
  }

  const result = await page.evaluate(({ label, uploadIndex }) => {
    const visible = el => !!(el && el.offsetParent !== null);
    const text = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    const fileInputs = Array.from(document.querySelectorAll('input[type="file"]'))
      .map((el, index) => ({ index, accept: el.getAttribute('accept') || '', visible: visible(el) }));
    const shortTexts = Array.from(document.querySelectorAll('button, a, [role="button"], div, span'))
      .filter(visible)
      .map(text)
      .filter(t => t && t.length <= 30)
      .slice(0, 120);
    let labelFound = false;
    if (label) {
      const labelEl = Array.from(document.querySelectorAll('*'))
        .filter(visible)
        .find(el => text(el).includes(label));
      if (labelEl) {
        labelEl.scrollIntoView({ block: 'center', inline: 'center' });
        labelEl.click();
        labelFound = true;
      }
    }
    const uploadButtons = Array.from(document.querySelectorAll('button, a, [role="button"], div, span'))
      .filter(visible)
      .filter(el => /上传封面|上传图片|重新上传|本地上传|选择图片|添加图片|点击上传/.test(text(el)))
      .sort((a, b) => text(a).length - text(b).length);
    if (!uploadButtons.length) {
      return { ok: false, reason: '找不到封面上传按钮', labelFound, uploadButtons: 0, fileInputs, shortTexts };
    }
    const target = uploadButtons[Math.min(uploadIndex, uploadButtons.length - 1)];
    target.scrollIntoView({ block: 'center', inline: 'center' });
    const box = target.getBoundingClientRect();
    return {
      ok: true,
      labelFound,
      uploadButtons: uploadButtons.length,
      x: box.left + box.width / 2,
      y: box.top + box.height / 2,
    };
  }, { label, uploadIndex });

  console.log(`Cover labelFound=${result.labelFound}, uploadButtons=${result.uploadButtons}`);
  if (result.fileInputs) console.log('File inputs:', JSON.stringify(result.fileInputs));
  if (result.shortTexts) console.log('Visible short texts:', result.shortTexts.join(' | '));
  if (!result.ok) throw new Error(result.reason);
  await page.mouse.click(result.x, result.y);
  await page.waitForTimeout(1000);
  console.log('__BILI_COVER_UPLOAD__=chooser');
  return 'cover_filechooser_opened';
}"""

COVER_SAVE_TEMPLATE = r"""async (page) => {
  await page.evaluate(() => { window.onbeforeunload = null; });

  async function coverModalOpen() {
    const hints = ['封面制作', '首页推荐封面（4:3）', '双比例同步改动'];
    for (const h of hints) {
      const loc = page.getByText(h, { exact: false }).first();
      if (await loc.isVisible().catch(() => false)) return true;
    }
    return false;
  }

  async function clickFinishInEvaluate() {
    return page.evaluate(() => {
      const visible = el => !!(el && el.offsetParent !== null);
      const text = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      const fire = el => {
        el.scrollIntoView({ block: 'center', inline: 'center' });
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
        el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        if (typeof el.click === 'function') el.click();
      };
      const dialogs = Array.from(document.querySelectorAll('.bcc-dialog, [class*="bcc-dialog"], [class*="bcc-modal"], [role="dialog"]'))
        .filter(visible)
        .filter(el => /封面制作|首页推荐封面|个人空间封面/.test(text(el)));
      const root = dialogs[0] || document.body;
      const footers = [
        root.querySelector('.bcc-dialog__footer'),
        root.querySelector('.bcc-modal__footer'),
        root.querySelector('.cover-footer'),
      ].filter(Boolean);
      const searchRoots = footers.length ? footers : [root];
      for (const fr of searchRoots) {
        const nodes = Array.from(fr.querySelectorAll('.bcc-button--primary, button[class*="primary"], button, [cursor="pointer"]')).filter(visible);
        const target = nodes.find(el => /^完成$/.test(text(el))) ||
          nodes.find(el => /完成|确定|保存/.test(text(el)) && !/取消|返回/.test(text(el)));
        if (target) {
          fire(target);
          return { ok: true, via: 'footer', label: text(target) };
        }
      }
      const scoped = Array.from(root.querySelectorAll('button, .bcc-button, [role="button"], [cursor="pointer"], a, div, span'))
        .filter(visible)
        .filter(el => /^完成$/.test(text(el)))
        .filter(el => !/取消|返回/.test(text(el)));
      if (scoped.length) {
        fire(scoped[scoped.length - 1]);
        return { ok: true, via: 'dialog-完成', label: text(scoped[scoped.length - 1]) };
      }
      return { ok: false };
    });
  }

  /** 与日志里已验证有效的路径一致：优先 Playwright 点 footer「完成」，失败再 DOM 兜底 */
  async function clickFinishPlaywright() {
    const dialog = page.locator('.bcc-dialog, [class*="bcc-dialog"]').filter({ hasText: '封面制作' }).first();
    const inDialog = dialog.locator('.bcc-dialog__footer, .bcc-modal__footer, .cover-footer').first();
    const primary = inDialog.locator('.bcc-button--primary, button[class*="primary"]').filter({ hasText: /完成|确定|保存/ }).first();
    if (await primary.count() > 0) {
      await primary.scrollIntoViewIfNeeded();
      await primary.click({ timeout: 12000 });
      return true;
    }
    const exact = inDialog.getByText('完成', { exact: true }).first();
    if (await exact.count() > 0) {
      await exact.scrollIntoViewIfNeeded();
      await exact.click({ timeout: 12000 });
      return true;
    }
    const footerDone = page.locator('.bcc-dialog__footer, .bcc-modal__footer').last().getByText('完成', { exact: true }).first();
    if (await footerDone.count() > 0) {
      await footerDone.scrollIntoViewIfNeeded();
      await footerDone.click({ timeout: 12000, force: true });
      return true;
    }
    const cursorDone = page.locator('[cursor="pointer"]').filter({ hasText: /^完成$/ }).last();
    if (await cursorDone.count() > 0) {
      await cursorDone.scrollIntoViewIfNeeded();
      await cursorDone.click({ timeout: 12000, force: true });
      return true;
    }
    return false;
  }

  async function drainSyncDialogs() {
    for (let i = 0; i < 3; i++) {
      const sync = page.getByText('确认同步', { exact: true }).first();
      if (!(await sync.isVisible().catch(() => false))) break;
      await sync.click({ timeout: 8000 });
      await page.waitForTimeout(500);
    }
  }

  if (!(await coverModalOpen())) {
    console.log('Cover modal not visible, skip');
    return 'cover_saved';
  }

  let ok = await clickFinishPlaywright().catch(() => false);
  if (!ok) {
    const ev = await clickFinishInEvaluate();
    if (!ev.ok) console.log('evaluate 未完成点击:', JSON.stringify(ev));
  }
  await page.waitForTimeout(500);
  await drainSyncDialogs();

  if (await coverModalOpen()) {
    console.log('封面弹窗仍在，再执行一次完成（仅一次补救）');
    ok = await clickFinishPlaywright().catch(() => false);
    if (!ok) await clickFinishInEvaluate();
    await page.waitForTimeout(500);
    await drainSyncDialogs();
  }

  if (await coverModalOpen()) {
    const snap = await page.evaluate(() => {
      const visible = el => !!(el && el.offsetParent !== null);
      const text = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      return Array.from(document.querySelectorAll('.bcc-dialog__footer button, .bcc-dialog__footer [cursor="pointer"], .bcc-dialog__footer .bcc-button'))
        .filter(visible).map(text).slice(0, 20);
    });
    throw new Error(`封面弹窗仍未关闭，footer 可见文案: ${snap.join(' | ')}`);
  }

  return 'cover_saved';
}"""

def _close_browser():
    logger.info("🧹 正在强制清理并关闭浏览器...")
    try:
        subprocess.run(["playwright-cli", "-s=default", "dialog-accept"], capture_output=True)
        # 强制关闭所有标签页
        subprocess.run(["playwright-cli", "-s=default", "run-code", "async (page) => { window.onbeforeunload = null; }"], capture_output=True)
        subprocess.run(["playwright-cli", "-s=default", "tab-close"], capture_output=True)
        subprocess.run(["playwright-cli", "close"], capture_output=True)
        subprocess.run(["playwright-cli", "kill-all"], capture_output=True)
    except: pass

def _start_browser():
    result = subprocess.run(["playwright-cli", "list"], capture_output=True, text=True)
    if "default" in result.stdout and "status: open" in result.stdout:
        return

    subprocess.Popen(
        ["playwright-cli", "open", BILIBILI_UPLOAD_URL, "--headed", "--profile", str(PROFILE_DIR)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(5)

def _playwright_cli_result_value(stdout: str | None) -> str | None:
    """解析 playwright-cli run-code 输出里的 ### Result，不要用子串匹配（stdout 含整段脚本源码）。"""
    if not stdout:
        return None
    m = re.search(r'### Result\s*\n"([^"]*)"', stdout)
    return m.group(1) if m else None


def _cover_step_need_cli_upload(stdout: str | None) -> bool:
    return _playwright_cli_result_value(stdout) == "cover_filechooser_opened"


def _try_clear_stale_file_chooser(cover_file: Path) -> None:
    """若仍悬停原生文件选择器，用 upload 关掉；无选择器时 CLI 会报错，属正常情况。"""
    r = subprocess.run(
        ["playwright-cli", "-s=default", "upload", str(cover_file)],
        capture_output=True,
        text=True,
    )
    out = f"{r.stdout}\n{r.stderr}"
    if "can only be used when there is related modal state" in out:
        return
    if r.returncode == 0 and "fileChooser" in out:
        logger.info("   已用 upload 清除可能残留的文件选择器")
        time.sleep(0.4)


def _find_files(video_dir: Path) -> dict:
    video = list(video_dir.glob("*_bilingual.mp4")) or list(video_dir.glob("*.mp4"))
    cover = list(video_dir.glob("modern.jpg")) or list(video_dir.glob("*.jpg"))
    meta_file = video_dir / "bilibili_meta.json"
    with open(meta_file, encoding="utf-8") as f: data = json.load(f)
    return {
        "video": str(video[0].resolve()),
        "cover": str(cover[0].resolve()),
        "title": data.get("bilibili_title", ""),
        "tags": data.get("bilibili_tags", []),
        "description": data.get("bilibili_description", ""),
        "source": data.get("bilibili_source", "转载"),
    }

def _run_js(name, code, scripts_dir):
    p = scripts_dir / name
    p.write_text(code, encoding="utf-8")
    subprocess.run(["playwright-cli", "-s=default", "dialog-accept"], capture_output=True)
    res = subprocess.run(["playwright-cli", "-s=default", "run-code", "--filename", str(p)], capture_output=True, text=True)
    p.unlink(missing_ok=True)
    if res.returncode != 0:
        logger.error("JS 阶段失败: %s", name)
        if res.stdout:
            logger.error("stdout:\n%s", res.stdout.strip())
        if res.stderr:
            logger.error("stderr:\n%s", res.stderr.strip())
    return res

def _run_js_checked(name, code, scripts_dir):
    res = _run_js(name, code, scripts_dir)
    if res.returncode != 0 or "### Error" in res.stdout:
        if res.returncode == 0:
            logger.error("JS 阶段输出错误: %s", name)
            logger.error("stdout:\n%s", res.stdout.strip())
        raise RuntimeError(f"{name} 执行失败")
    if res.stdout:
        logger.info(res.stdout.strip())
    return res

def _upload_cover_file(cover_file: Path, attempts: int = 5):
    last = None
    for attempt in range(1, attempts + 1):
        logger.info("   playwright-cli upload 封面，第 %s/%s 次...", attempt, attempts)
        last = subprocess.run(
            ["playwright-cli", "-s=default", "upload", str(cover_file)],
            capture_output=True,
            text=True,
        )
        output = f"{last.stdout}\n{last.stderr}"
        if last.returncode == 0 and (
            "fileChooser.setFiles" in output
            or "setInputFiles" in output
            or "file chooser" in output.lower()
        ):
            logger.info("   封面文件已投递（已处理文件选择器）")
            return
        if output.strip():
            logger.warning("   upload 输出:\n%s", output.strip())
        time.sleep(1)

    raise RuntimeError(f"封面文件投递失败: {last.stderr.strip() if last else 'unknown'}")

def _do_upload(video_dir: str, collection: str, partition: str, auto_close: bool, no_open: bool):
    video_dir = Path(video_dir).resolve()
    info = _find_files(video_dir)
    info.update({"collection": collection, "partition": partition})
    
    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    info_json = json.dumps(info, ensure_ascii=False)

    try:
        if no_open:
            logger.info("使用已有 playwright-cli default session，不执行 open")
        else:
            _start_browser()
        
        # Phase 1: 上传视频并置顶
        logger.info("🎬 Phase 1: 上传视频并置顶...")
        _run_js_checked(".p1.js", PHASE1_TEMPLATE.replace("{{INFO_JSON}}", info_json), scripts_dir)

        # Step 1: 打开封面编辑器
        logger.info("🎨 Step 1: 打开封面编辑器...")
        _run_js_checked(".c1.js", COVER_OPEN_TEMPLATE, scripts_dir)

        cover_temp = scripts_dir / ".cover.jpg"
        shutil.copy(info["cover"], cover_temp)

        # Step 2: 4:3
        logger.info("🎨 Step 2: 上传 4:3 封面...")
        c2_res = _run_js_checked(
            ".c2.js",
            COVER_UPLOAD_TEMPLATE
            .replace("{{LABEL_JSON}}", json.dumps("首页推荐封面", ensure_ascii=False))
            .replace("{{UPLOAD_INDEX}}", "0")
            .replace("{{COVER_JSON}}", json.dumps(str(cover_temp), ensure_ascii=False)),
            scripts_dir,
        )
        if _cover_step_need_cli_upload(c2_res.stdout):
            _upload_cover_file(cover_temp)
        time.sleep(2)

        # Step 3: 16:9
        logger.info("🎨 Step 3: 上传 16:9 封面...")
        c3_res = _run_js_checked(
            ".c3.js",
            COVER_UPLOAD_TEMPLATE
            .replace("{{LABEL_JSON}}", json.dumps("个人空间封面", ensure_ascii=False))
            .replace("{{UPLOAD_INDEX}}", "1")
            .replace("{{COVER_JSON}}", json.dumps(str(cover_temp), ensure_ascii=False)),
            scripts_dir,
        )
        if _cover_step_need_cli_upload(c3_res.stdout):
            _upload_cover_file(cover_temp)
        time.sleep(2)

        _try_clear_stale_file_chooser(cover_temp)

        # Step 4: 完成封面
        logger.info("🎨 Step 4: 保存封面...")
        _run_js_checked(".c4.js", COVER_SAVE_TEMPLATE, scripts_dir)
        cover_temp.unlink(missing_ok=True)

        # Phase 2: 填写其余信息
        logger.info("🎬 Phase 2: 填写其余信息...")
        _run_js_checked(".p2.js", PHASE2_TEMPLATE.replace("{{INFO_JSON}}", info_json), scripts_dir)

    finally:
        if "cover_temp" in locals():
            cover_temp.unlink(missing_ok=True)
        if auto_close: _close_browser()

    print("\n✅ 流程结束，请检查后点击立即投稿。")
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-dir", "-d", required=True)
    parser.add_argument("--collection", "-c", default="TED-趣味-学英语")
    parser.add_argument("--partition", "-p", default="知识")
    parser.add_argument("--auto-close", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="不启动浏览器，直接使用已打开的 playwright-cli default session")
    args = parser.parse_args()
    return _do_upload(args.video_dir, args.collection, args.partition, args.auto_close, args.no_open)

if __name__ == "__main__":
    sys.exit(main())

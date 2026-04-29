async (page) => {
  const info = {"video": "/Users/jarvis/work/tools/ai-vedio/output/725/725_bilingual.mp4", "cover": "/Users/jarvis/work/tools/ai-vedio/output/725/modern.jpg", "title": "丝绸之路：人类历史上第一个全球互联网，2000年前如何连接世界", "tags": ["丝绸之路", "历史", "文明交流", "世界贸易", "古代科技", "文化传播", "东西方交流", "全球化", "张骞", "波斯御道", "蒙古帝国", "佛教传播", "火药", "海上丝绸之路"], "description": "你有没有想过，在互联网诞生之前，世界是如何连接的？\n\n答案是：一条绵延5000英里的古老路网——丝绸之路。它不仅是商品交换的通道，更是人类历史上第一个“全球网络”，连接了从长安到罗马的文明。\n\n本视频带你穿越2000年，揭示丝绸之路如何通过游牧民族、帝王远征和贸易商旅，将丝绸、玻璃、佛教、火药甚至思想传遍欧亚大陆。\n\n适合人群：历史爱好者、对全球化起源感兴趣的人、喜欢冷知识的小伙伴。\n\n核心看点：\n- 丝绸之路并非一条路，而是一个动态网络\n- 游牧民族如何成为最早的“信息传递者”\n- 波斯御道：古代版“高速公路”\n- 张骞出使西域：打通东西方的关键一步\n- 蒙古帝国为何保护而非破坏贸易路线\n- 丝绸之路如何催生了佛教东传、伊斯兰扩张和火药革命", "source": "转载", "collection": "TED-趣味-学英语", "partition": "知识"};
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
}
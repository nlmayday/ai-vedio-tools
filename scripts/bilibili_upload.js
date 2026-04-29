async (page) => {
  const fs = require('fs');
  const path = require('path');

  const INFO_FILE = process.env.BILIBILI_UPLOAD_INFO ||
    path.join(__dirname, '..', 'output', '.bilibili_upload_info.json');

  const info = JSON.parse(fs.readFileSync(INFO_FILE, 'utf-8'));
  console.log(`Title: ${info.title}`);
  console.log(`Video: ${info.video}`);
  console.log(`Cover: ${info.cover}`);
  console.log(`Tags: ${info.tags.length} tags`);

  // ── 导航到上传页 ──
  console.log('Navigating to B站 upload page...');
  await page.goto('https://member.bilibili.com/platform/upload/video/frame', {
    waitUntil: 'domcontentloaded',
  });
  await page.waitForTimeout(2000);

  // 检查是否需要登录
  if (page.url().includes('login') || page.url().includes('passport')) {
    console.log('⚠️  需要登录！请在浏览器中登录...');
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(5000);
      if (!page.url().includes('login') && !page.url().includes('passport')) {
        console.log('登录成功，继续...');
        await page.goto('https://member.bilibili.com/platform/upload/video/frame', {
          waitUntil: 'domcontentloaded',
        });
        await page.waitForTimeout(2000);
        break;
      }
    }
  }

  // ── 上传视频 ──
  console.log('📤 Uploading video...');
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(info.video);
  console.log('   Video file selected, waiting for upload...');

  // ── 等待上传完成 ──
  console.log('⏳ Waiting for upload & processing...');
  try {
    await page.waitForSelector(
      'text=上传成功|text=视频预览|.video-preview|.upload-success',
      { timeout: 600_000 }
    );
    console.log('✅ Upload complete');
  } catch {
    console.log('⚠️  Upload wait timed out — proceeding anyway');
  }
  await page.waitForTimeout(2000);

  // ── 填标题 ──
  try {
    const titleSelectors = [
      'input[placeholder*="标题"]',
      '[class*="title"] input',
    ];
    let titleInput = null;
    for (const sel of titleSelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) { titleInput = el; break; }
    }
    if (titleInput) {
      await titleInput.click();
      await titleInput.fill('');
      await titleInput.fill(info.title);
      console.log(`   标题已填写: ${info.title.substring(0, 50)}...`);
    }
  } catch (e) {
    console.log(`   标题填写失败: ${e.message}`);
  }
  await page.waitForTimeout(500);

  // ── 填标签 ──
  try {
    const closeBtns = page.locator(
      '[class*="tag"] .close, [class*="tag"] [class*="close"], .tag-item .remove, [class*="tag"] [class*="icon-close"]'
    );
    const count = await closeBtns.count();
    for (let i = 0; i < count; i++) {
      try {
        await closeBtns.nth(0).click();
        await page.waitForTimeout(200);
      } catch { break; }
    }

    const tagSelectors = [
      'input[placeholder*="标签"]',
      '[class*="tag"] input',
    ];
    let tagInput = null;
    for (const sel of tagSelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) { tagInput = el; break; }
    }
    if (tagInput) {
      for (const tag of info.tags) {
        await tagInput.click();
        await tagInput.fill(tag);
        await page.waitForTimeout(300);
        await tagInput.press('Enter');
        await page.waitForTimeout(300);
      }
      console.log(`   标签已填写: ${info.tags.length} 个`);
    }
  } catch (e) {
    console.log(`   标签填写失败: ${e.message}`);
  }

  // ── 填简介 ──
  try {
    const descSelectors = [
      'textarea[placeholder*="简介"]',
      '[class*="desc"] textarea',
      'textarea',
    ];
    let descInput = null;
    for (const sel of descSelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) { descInput = el; break; }
    }
    if (descInput) {
      await descInput.click();
      await descInput.fill('');
      await descInput.fill(info.description);
      console.log(`   简介已填写: ${info.description.length} 字`);
    }
  } catch (e) {
    console.log(`   简介填写失败: ${e.message}`);
  }
  await page.waitForTimeout(500);

  // ── 上传封面 ──
  try {
    const fileInputs = page.locator('input[type="file"]');
    const inputCount = await fileInputs.count();
    if (inputCount >= 2) {
      await fileInputs.nth(1).setInputFiles(info.cover);
    } else if (inputCount >= 1) {
      await fileInputs.nth(0).setInputFiles(info.cover);
    }
    console.log('   封面已上传');
  } catch (e) {
    console.log(`   封面上传失败: ${e.message}`);
  }

  console.log('\n' + '='.repeat(60));
  console.log('📝 请检查信息后手动点击「立即投稿」按钮');
  console.log('='.repeat(60));
  console.log(`   标题: ${info.title}`);
  console.log(`   标签: ${info.tags.slice(0, 5).join(', ')}...`);
  console.log(`   封面: ${info.cover}`);
  console.log('='.repeat(60));
  console.log('浏览器保持打开中，检查无误后手动提交。');

  return 'upload_ready';
}

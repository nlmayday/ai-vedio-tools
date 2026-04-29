async (page) => {
  const info = {"video": "/Users/jarvis/work/tools/ai-vedio/output/725/725_bilingual.mp4", "cover": "/Users/jarvis/work/tools/ai-vedio/output/725/modern.jpg", "title": "丝绸之路：人类历史上第一个全球互联网，2000年前如何连接世界", "tags": ["丝绸之路", "历史", "文明交流", "世界贸易", "古代科技", "文化传播", "东西方交流", "全球化", "张骞", "波斯御道", "蒙古帝国", "佛教传播", "火药", "海上丝绸之路"], "description": "你有没有想过，在互联网诞生之前，世界是如何连接的？\n\n答案是：一条绵延5000英里的古老路网——丝绸之路。它不仅是商品交换的通道，更是人类历史上第一个“全球网络”，连接了从长安到罗马的文明。\n\n本视频带你穿越2000年，揭示丝绸之路如何通过游牧民族、帝王远征和贸易商旅，将丝绸、玻璃、佛教、火药甚至思想传遍欧亚大陆。\n\n适合人群：历史爱好者、对全球化起源感兴趣的人、喜欢冷知识的小伙伴。\n\n核心看点：\n- 丝绸之路并非一条路，而是一个动态网络\n- 游牧民族如何成为最早的“信息传递者”\n- 波斯御道：古代版“高速公路”\n- 张骞出使西域：打通东西方的关键一步\n- 蒙古帝国为何保护而非破坏贸易路线\n- 丝绸之路如何催生了佛教东传、伊斯兰扩张和火药革命", "source": "转载", "collection": "TED-趣味-学英语", "partition": "知识"};
  const tags = info.tags.slice(0, 10);  // B站限制最多10个标签

  // 自动接受所有对话框 (处理 beforeunload 等)
  page.on('dialog', async dialog => {
    console.log(`   [Dialog] ${dialog.type()}: ${dialog.message()}`);
    await dialog.accept().catch(() => {});
  });

  // 强力禁用 beforeunload 弹窗
  await page.evaluate(() => {
    window.onbeforeunload = null;
    window.addEventListener('beforeunload', (e) => {
      e.stopImmediatePropagation();
    }, true);
  });

  console.log(`Title: ${info.title}`);
  console.log(`Video: ${info.video}`);
  console.log(`Cover: ${info.cover}`);
  console.log(`Tags (max 10): ${tags.length}`);
  if (info.collection) {
    console.log(`Collection: ${info.collection}`);
  }

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

  // 处理「本地浏览器存在未提交视频」草稿弹窗
  try {
    const dismissBtn = page.locator('text=不用了').first();
    if (await dismissBtn.count() > 0) {
      await dismissBtn.click({ timeout: 3000 });
      console.log('   已关闭草稿弹窗');
      await page.waitForTimeout(1000);
    }
  } catch {}

  // ── 上传视频 ──
  console.log('📤 Uploading video...');
  // 更加精确的选择器：优先选择 accept 中包含 video 或 mp4 的 input
  let fileInput = page.locator('input[type="file"][accept*="video"], input[type="file"][accept*=".mp4"]').first();
  if (await fileInput.count() === 0) {
    fileInput = page.locator('input[type="file"]').first();
  }
  await fileInput.setInputFiles(info.video);
  console.log('   Video file selected');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'scripts/debug_after_upload.png' });

  // ── 填标题 ──
  try {
    const titleInput = page.locator('input[placeholder*="标题"]').first();
    if (await titleInput.count() > 0) {
      await titleInput.click();
      await titleInput.fill('');
      await titleInput.fill(info.title);
      console.log(`   标题已填写: ${info.title.substring(0, 50)}...`);
    }
  } catch (e) {
    console.log(`   标题填写失败: ${e.message}`);
  }
  await page.waitForTimeout(500);

  // ── 选类型（自制/转载） ──
  try {
    const sourceType = info.source || '转载';
    // B站用 .check-radio-v2-container 包含 span.check-radio-v2-name
    const radio = page.locator('.check-radio-v2-container').filter({ hasText: sourceType }).first();
    if (await radio.count() > 0) {
      await radio.click();
      console.log(`   类型已选择: ${sourceType}`);
      await page.waitForTimeout(500);
    }
  } catch (e) {
    console.log(`   类型选择失败: ${e.message}`);
  }
  await page.waitForTimeout(500);

  // ── 选分区 ──
  if (info.partition) {
    console.log(`   开始选择分区: ${info.partition}...`);
    try {
      // 点击分区选择器
      const partitionArea = page.locator('.video-human-type [cursor="pointer"], [class*="human-type"] [class*="select"]').first();
      if (await partitionArea.count() > 0) {
        await partitionArea.click({ timeout: 3000 });
        await page.waitForTimeout(1000);
        // 在下拉菜单中点选分区
        const partitionOption = page.locator(`text="${info.partition}"`).first();
        if (await partitionOption.count() > 0) {
          await partitionOption.click({ timeout: 3000 });
          await page.waitForTimeout(500);
          console.log(`   分区已选择: ${info.partition}`);
        } else {
          console.log(`   ⚠️ 未找到分区选项: ${info.partition}`);
        }
      }
    } catch (e) {
      console.log(`   分区选择失败: ${e.message}`);
    }
  }
  await page.screenshot({ path: 'scripts/debug_after_meta.png' });

  // ── 填标签（B站最多10个） ──
  try {
    // 清掉默认标签
    const closeBtns = page.locator(
      '[class*="tag"] .close, [class*="tag"] [class*="close"], .tag-item .remove, [class*="tag"] [class*="icon-close"]'
    );
    const closeCount = await closeBtns.count();
    for (let i = 0; i < closeCount; i++) {
      try {
        await closeBtns.nth(0).click();
        await page.waitForTimeout(200);
      } catch { break; }
    }

    const tagInput = page.locator('input[placeholder*="标签"]').first();
    if (await tagInput.count() > 0) {
      for (const tag of tags) {
        await tagInput.click({ timeout: 3000 });
        await tagInput.fill(tag, { timeout: 3000 });
        await page.waitForTimeout(300);
        await tagInput.press('Enter');
        await page.waitForTimeout(300);
      }
      console.log(`   标签已填写: ${tags.length} 个`);
    }
  } catch (e) {
    console.log(`   标签填写失败: ${e.message}`);
  }

  // ── 填简介（B站使用 Quill 富文本编辑器 div.ql-editor） ──
  console.log('   开始填写简介...');
  try {
    const editor = page.locator('.ql-editor').first();
    if (await editor.count() > 0) {
      await editor.click({ timeout: 3000 });
      await page.waitForTimeout(300);
      // Quill 编辑器是 contenteditable div，需要用 evaluate 设置内容
      await page.evaluate((desc) => {
        const el = document.querySelector('.ql-editor');
        if (el) {
          el.innerHTML = desc.replace(/\n/g, '<br>');
          el.classList.remove('ql-blank');
        }
      }, info.description);
      console.log(`   简介已填写: ${info.description.length} 字`);
    } else {
      console.log('   未找到简介编辑器');
    }
  } catch (e) {
    console.log(`   简介填写失败: ${e.message}`);
  }
  await page.waitForTimeout(500);

  // ── 选合集 ──
  if (info.collection) {
    console.log('   开始选择合集...');
    try {
      // 点击 "请选择合集" 区域展开下拉
      const seasonEnter = page.locator('.season-enter').first();
      if (await seasonEnter.count() > 0) {
        await seasonEnter.click({ timeout: 3000 });
        await page.waitForTimeout(800);
        // 下拉展开后搜索合集
        const searchInput = page.locator('[class*="season"] input, [class*="select"] input[type="text"]').first();
        if (await searchInput.count() > 0) {
          await searchInput.fill(info.collection, { timeout: 3000 });
          await page.waitForTimeout(800);
        }
        // 点击匹配的合集选项
        const option = page.locator(`text="${info.collection}"`).last();
        if (await option.count() > 0) {
          await option.click({ timeout: 3000 });
          await page.waitForTimeout(500);
          console.log(`   合集已选择: ${info.collection}`);
        } else {
          console.log('   未找到匹配的合集选项');
        }
      } else {
        console.log('   未找到合集选择器');
      }
    } catch (e) {
      console.log(`   合集选择失败: ${e.message}`);
    }
  }

  // ── 上传封面（由 Python 层分步处理，此处跳过）──

  // ── 等待视频上传完成 ──
  console.log('⏳ 等待视频上传完成（最多10分钟）...');
  let uploadStarted = false;
  for (let i = 0; i < 120; i++) {
    await page.waitForTimeout(5000);
    try {
      const hasDone = await page.locator('text=上传成功|text=已上传|text=视频预览|text=上传完成').count();
      const hasProgress = await page.locator('[class*="progress"], [class*="uploading"]').count();
      
      // 实时日志
      if (hasDone > 0) {
        console.log(`   [Status] 检测到完成标志 (${i*5}s)`);
      } else if (hasProgress > 0) {
        console.log(`   [Status] 上传中... (${i*5}s)`);
      } else {
        console.log(`   [Status] 等待中... (${i*5}s)`);
      }

      if (hasProgress > 0) {
        uploadStarted = true;
      }
      
      // 检查封面按钮是否已经提前出现
      const coverBtn = page.locator('text=封面设置').first();
      if (await coverBtn.count() > 0 && await coverBtn.isVisible()) {
        console.log('✅ 发现封面设置按钮，上传流程应已稳定');
        break;
      }

      if (hasDone > 0) {
        console.log('✅ 视频上传已完成 (标志检测)');
        break;
      }
      if (uploadStarted && hasProgress === 0) {
        console.log('✅ 视频上传已完成 (进度条消失)');
        break;
      }
    } catch (e) {
      console.log(`   [Error] 轮询异常: ${e.message}`);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('📝 请检查信息后手动点击「立即投稿」按钮');
  console.log('='.repeat(60));
  console.log(`   标题: ${info.title}`);
  console.log(`   标签: ${tags.slice(0, 5).join(', ')}...`);
  console.log(`   封面: ${info.cover}`);
  console.log('='.repeat(60));
  console.log('浏览器保持打开中，检查无误后手动提交。');

  return 'upload_ready';
}
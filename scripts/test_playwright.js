async (page) => {
  await page.goto('https://www.baidu.com');
  console.log('Title:', await page.title());
  return 'success';
}

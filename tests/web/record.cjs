// Requires a healthy local demo and `npx playwright install chromium ffmpeg`.
const { chromium } = require('playwright');
const fs = require('node:fs');

async function main() {
  fs.mkdirSync('.tools/demo-video', { recursive: true });
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROME_EXECUTABLE ? { executablePath: process.env.CHROME_EXECUTABLE } : {}) });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 },
    recordVideo: { dir: '.tools/demo-video', size: { width: 1280, height: 900 } } });
  const page = await context.newPage(), video = page.video();
  try {
    await page.goto(process.env.WEB_URL || 'http://localhost:8686');
    await page.getByText('Trợ lý sẵn sàng', { exact: true }).waitFor({ timeout: 70000 });
    await page.waitForTimeout(1600);
    for (const [message, expected] of [
      ['điểm chuẩn ngành Công nghệ thông tin năm 2026', 'UTHUIT05A'],
      ['Em có 8 điểm Toán, 8 điểm Hóa và 9 điểm Anh', 'D07'],
      ['học phí của trường', 'KHÔNG áp dụng chung'],
    ]) {
      if (await page.locator('.message-row').count()) { await page.locator('#new-session').click(); await page.waitForTimeout(700); }
      await page.locator('#message').pressSequentially(message, { delay: 35 });
      await page.waitForTimeout(500); await page.locator('#message').press('Enter');
      await page.locator('.message-row.assistant').filter({ hasText: expected }).last().waitFor({ timeout: 65000 });
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      await page.waitForTimeout(3000);
    }
  } finally { await context.close(); }
  await video.saveAs('docs/assets/demo.webm');
  await browser.close();
  console.log('Saved docs/assets/demo.webm');
}
main().catch((error) => { console.error(error); process.exitCode = 1; });

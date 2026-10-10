// Run from the repository root with the gateway running at WEB_URL.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const mock = process.argv.includes('--mock');
const url = process.env.WEB_URL || 'http://localhost:8686';
const output = 'results/web-ui';
fs.mkdirSync(output, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROME_EXECUTABLE ? { executablePath: process.env.CHROME_EXECUTABLE } : {}) });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage(), errors = [], senders = [], checks = [];
  page.on('pageerror', (error) => errors.push(error.message));
  context.on('request', (request) => {
    if (new URL(request.url()).pathname === '/api/chat') senders.push(request.postDataJSON().sender);
  });
  function pass(name) { checks.push(name); console.log('PASS', name); }
  if (mock) {
    await context.route('**/api/health', (route) => route.fulfill({ json: { ready: true } }));
    await context.route('**/api/chat', (route) => {
      const message = route.request().postDataJSON().message;
      let text = 'Công nghệ thông tin — giới thiệu đang kiểm chứng.\nNguồn: https://tuyensinh.ut.edu.vn/';
      if (message.includes('điểm chuẩn')) text = 'Năm 2026, UTHUIT05A: 720 điểm xét tuyển kết hợp. Không phải thang 30.\nNguồn: https://tuyensinh.ut.edu.vn/';
      else if (message.includes('8 điểm Toán')) text = 'Tổng điểm:\n- D07: 25/30\nĐiểm chỉ để tham khảo.';
      else if (message.includes('học phí')) text = 'Học phí chương trình cụ thể: KHÔNG áp dụng chung.\nNguồn: https://tuyensinh.ut.edu.vn/';
      return route.fulfill({ json: { messages: [{ text }] } });
    });
  }
  try {
    await page.goto(url);
    await page.waitForFunction(() => document.querySelector('#major').options.length === 68);
    await page.getByText('Trợ lý sẵn sàng', { exact: true }).waitFor({ timeout: 70000 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: `${output}/desktop.png`, fullPage: true });
    pass('desktop and verified catalog');

    async function reset() { await page.locator('#new-session').click(); }
    async function ask(text, expected) {
      await page.locator('#message').fill(text); await page.locator('#message').press('Enter');
      await page.locator('.message-row.assistant').filter({ hasText: expected }).last().waitFor({ timeout: 65000 });
      await page.waitForFunction(() => !document.querySelector('#send').disabled);
      assert.equal(await page.locator('.error-card').count(), 0);
    }
    await page.getByRole('button', { name: 'Khám phá ngành học' }).click();
    assert.equal(await page.locator('#message').inputValue(), 'UTH đào tạo những ngành gì');
    await ask('UTH đào tạo những ngành gì', 'Công nghệ thông tin'); pass('task 1: catalog');
    await reset(); await page.locator('#major').selectOption('Công nghệ thông tin');
    await page.locator('#major-intro').click(); await ask(await page.locator('#message').inputValue(), 'Công nghệ thông tin'); pass('task 2: selected major');
    await reset(); await page.locator('#major').selectOption('Công nghệ thông tin'); await page.locator('#major-cutoff').click();
    await ask(await page.locator('#message').inputValue(), 'UTHUIT05A');
    assert.ok(await page.locator('.source-links a').count() > 0); pass('task 3: year, program and sources');
    await page.screenshot({ path: `${output}/cutoff.png`, fullPage: true });
    await reset(); await ask('Em có 8 điểm Toán, 8 điểm Hóa và 9 điểm Anh', 'D07');
    assert.ok(await page.locator('table.score-table').count() > 0); pass('task 4: score table');
    await reset(); await ask('học phí của trường', 'KHÔNG áp dụng chung'); pass('task 5: tuition scope');
    await page.getByRole('button', { name: 'Hữu ích', exact: true }).first().click();
    await page.getByText('Đã ghi nhận phản hồi. Cảm ơn bạn!').first().waitFor(); pass('feedback');

    // Exercise failure and retry at the browser boundary, preserving history.
    const before = await page.locator('.message-row.user').count();
    await page.route('**/api/chat', (route) => route.fulfill({ status: 503, json: { error: 'Unavailable' } }));
    await page.locator('#message').fill('UTH đào tạo những ngành gì'); await page.locator('#message').press('Enter');
    await page.getByRole('button', { name: 'Thử gửi lại' }).waitFor();
    assert.equal(await page.locator('.message-row.user').count(), before + 1);
    await page.unroute('**/api/chat');
    await page.getByRole('button', { name: 'Thử gửi lại' }).click();
    await page.waitForFunction(() => !document.querySelector('#send').disabled);
    assert.equal(await page.locator('.error-card').count(), 0);
    assert.equal(await page.locator('.message-row.user').count(), before + 1); pass('failure preserves history and retry avoids duplicate UI');

    await page.evaluate(async () => {
      const { renderAnswer, safeLink } = await import('/render.js');
      const element = document.createElement('div');
      renderAnswer(element, '<img src=x onerror=alert(1)> **Tên ngành** [x](javascript:alert) https://tuyensinh.ut.edu.vn/');
      if (element.querySelector('img,script') || safeLink('javascript:alert(1)') || safeLink('data:text/html,x')) throw new Error('Unsafe renderer');
      if (!element.querySelector('strong') || element.querySelector('a').rel !== 'noopener noreferrer') throw new Error('Broken safe Markdown');
    }); pass('safe limited Markdown');
    await reset(); await page.locator('#message').fill('dòng 1'); await page.locator('#message').press('Shift+Enter');
    assert.ok((await page.locator('#message').inputValue()).includes('\n')); pass('keyboard newline');
    await ask('học phí của trường', 'KHÔNG áp dụng chung');
    const firstSender = senders.at(-1); await reset(); await ask('UTH đào tạo những ngành gì', 'Công nghệ thông tin');
    assert.notEqual(senders.at(-1), firstSender); pass('reset isolates sender');
    const second = await context.newPage(); await second.goto(url);
    await second.locator('#message').fill('UTH đào tạo những ngành gì'); await second.locator('#message').press('Enter');
    await second.locator('.message-row.assistant').filter({ hasText: 'Công nghệ thông tin' }).waitFor({ timeout: 65000 });
    assert.notEqual(senders.at(-1), senders.at(-2)); pass('separate tabs isolate sender'); await second.close();

    await page.setViewportSize({ width: 390, height: 844 }); await reset();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.ok(await page.locator('#message').isVisible());
    await page.screenshot({ path: `${output}/mobile.png`, fullPage: true });
    await ask('Em có 8 điểm Toán, 8 điểm Hóa và 9 điểm Anh', 'D07');
    await page.screenshot({ path: `${output}/mobile-score.png`, fullPage: true }); pass('mobile 390px and score table');
    assert.deepEqual(errors, []);
    fs.writeFileSync(`${output}/report.json`, JSON.stringify({ mode: mock ? 'mock' : 'real-rasa', checks, page_errors: errors }, null, 2));
  } finally { await context.close(); await browser.close(); }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });

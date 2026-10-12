const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve');
const server = http.createServer((req, res) => {
  const f = path.join(root, path.basename(req.url.split('?')[0]));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.json') ? 'application/json' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8765, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [label, url] of [['served', 'http://localhost:8765/umbrella_bars_from_data.html'], ['from disk', 'file://' + root + '/umbrella_bars_from_data.html']]) {
    const page = await browser.newPage({ viewport: { width: 1040, height: 600 } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(url); await page.waitForTimeout(600);
    console.log(label, JSON.stringify(await page.evaluate(() => ({
      rects: document.querySelectorAll('#chart g[fill] rect').length,
      values: [...document.querySelectorAll('.value')].map(e => e.textContent).join(' '),
      order: [...document.querySelectorAll('.axis')].slice(1).map(e => e.textContent).join(''),
      message: document.querySelector('#message').textContent,
    }))), 'errors', JSON.stringify(errors).slice(0, 160));
    if (label === 'served') await page.screenshot({ path: 'umbrella_from_data.png' });
    await page.close();
  }
  await browser.close(); server.close();
})();

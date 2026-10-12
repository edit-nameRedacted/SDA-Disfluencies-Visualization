// screenshots with the real web fonts loaded, at a wide desktop size and a phone size
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve4');
const server = http.createServer((req, res) => {
  const f = path.join(root, path.basename(req.url.split('?')[0]));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8771, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [name, w, h] of [['wide', 1920, 1000], ['phone', 390, 800]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://localhost:8771/switchboard_viz.html'); await page.waitForTimeout(1500);
    const fonts = await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight).join(', '); });
    console.log(name, 'fonts loaded:', fonts || 'none');
    await page.screenshot({ path: `f-${name}-1-opening.png` });
    await page.mouse.click(w / 2, h * 0.44); await page.waitForTimeout(700);
    await page.screenshot({ path: `f-${name}-2-moving.png` });
    await page.waitForTimeout(2600);
    await page.screenshot({ path: `f-${name}-3-umbrellas.png` });
    const bar = await page.evaluate(() => { const b = document.querySelectorAll('.bar')[3].querySelector('.seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1200);
    await page.screenshot({ path: `f-${name}-4-focus.png` });
    console.log(name, 'errors', JSON.stringify(errors));
    await page.close();
  }
  await browser.close(); server.close();
})();

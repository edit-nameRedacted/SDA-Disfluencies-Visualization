// focus-state screenshots at several window sizes, for several bars
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve4');
const pageName = process.argv[2] || 'switchboard_viz.html';
const server = http.createServer((req, res) => {
  const f = path.join(root, path.normalize(decodeURIComponent(req.url.split('?')[0])).replace(/^([/\\]|\.\.)+/, ''));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : f.endsWith('.json') ? 'application/json' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8772, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [name, w, h, bars] of [['wide', 1920, 1000, [3, 9, 0]], ['laptop', 1280, 720, [6]], ['tablet', 800, 1000, [0, 9]], ['phone', 390, 800, [3, 0, 9]]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://localhost:8772/' + pageName); await page.waitForTimeout(1500);
    await page.evaluate(() => document.fonts.ready);
    await page.mouse.click(w / 2, h * 0.44); await page.waitForTimeout(3400);
    for (const i of bars) {
      const bar = await page.evaluate(i => { const b = document.querySelectorAll('.bar')[i].querySelector('.seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, i);
      await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1300);
      await page.screenshot({ path: `s-${name}-bar${i}.png` });
      const info = await page.evaluate(() => { const g = document.querySelector('.bar.is-focused'); const out = [...g.querySelectorAll('.detail text')].map(t => { const r = t.getBoundingClientRect(); return [t.textContent, Math.round(r.left), Math.round(r.right), Math.round(r.top)]; }); return out.filter(r => r[1] < 0 || r[2] > innerWidth); });
      console.log(name, i, 'labels outside window:', JSON.stringify(info));
      await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
    }
    console.log(name, 'errors', JSON.stringify(errors));
    await page.close();
  }
  await browser.close(); server.close();
})();

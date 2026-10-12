const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve(process.argv[2] || '../serve4'); const pageName = process.argv[3] || 'switchboard_viz.html'; const tag = process.argv[4] || 'v';
const server = http.createServer((req, res) => {
  const f = path.join(root, path.basename(req.url.split('?')[0]));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8770, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [name, w, h] of [['desk', 1280, 800], ['phone', 390, 800]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1.5 });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    await page.route('https://fonts.googleapis.com/**', r => r.abort());
    const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error' && !/fonts|ERR_FAILED/.test(m.text())) errors.push(m.text()); });
    await page.goto('http://localhost:8770/' + pageName); await page.waitForTimeout(600);
    const st = () => page.evaluate(() => ({ state, busy, bodyBlack: document.body.classList.contains('black'), tf: document.querySelector('#world').getAttribute('transform').slice(0, 60), hud: document.querySelector('#hud-line').textContent.slice(0, 70) }));
    await page.screenshot({ path: `${tag}-${name}-1-opening.png` });
    console.log(name, 'opening', JSON.stringify(await st()), 'label:', await page.evaluate(() => [...document.querySelectorAll('.receiver text')].map(t => t.textContent).join(' | ')));
    await page.mouse.click(w / 2, h * 0.46); await page.waitForTimeout(3200);
    await page.screenshot({ path: `${tag}-${name}-2-umbrellas.png` });
    console.log(name, 'umbrellas', JSON.stringify(await st()), 'order:', await page.evaluate(() => [...document.querySelectorAll('.name')].map(t => t.textContent).join(', ')));
    const bar = await page.evaluate(() => { const b = document.querySelectorAll('.bar')[9].querySelector('.seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1200);
    await page.screenshot({ path: `${tag}-${name}-3-focus.png` });
    console.log(name, 'focus', JSON.stringify(await st()));
    const seg = await page.evaluate(() => { const b = document.querySelector('.bar.is-focused .seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(seg.x, seg.y); await page.waitForTimeout(700);
    await page.screenshot({ path: `${tag}-${name}-4-midzoom.png` });
    await page.waitForTimeout(1200);
    await page.screenshot({ path: `${tag}-${name}-5-black.png` });
    console.log(name, 'black', JSON.stringify(await st()), await page.evaluate(() => document.querySelector('#next').innerText.replace(/\n/g, ' | ')));
    await page.mouse.click(40, h - 40); await page.waitForTimeout(1700);
    console.log(name, 'back', JSON.stringify(await st()));
    await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1000);
    await page.mouse.click(8, h / 2); await page.waitForTimeout(1000);
    console.log(name, 'focus then away', JSON.stringify(await st()));
    await page.screenshot({ path: `${tag}-${name}-6-back.png` });
    console.log(name, 'errors', JSON.stringify(errors));
    await page.close();
  }
  await browser.close(); server.close();
})();

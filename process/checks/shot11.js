// the bracket cue and the info panel, on the white and the black screen
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve4'); const pageName = process.argv[2] || 'art.html';
const server = http.createServer((req, res) => {
  const f = path.join(root, path.normalize(decodeURIComponent(req.url.split('?')[0])).replace(/^([/\\]|\.\.)+/, ''));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : f.endsWith('.json') ? 'application/json' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8774, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [name, w, h, barIndex] of [['wide', 1920, 1000, 6], ['laptop', 1280, 720, 6], ['phone', 390, 800, 6]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    const st = () => page.evaluate(() => `${state} | info ${document.querySelector('#info').hidden ? 'closed' : 'open'}`);
    await page.goto('http://localhost:8774/' + pageName); await page.waitForTimeout(1500); await page.evaluate(() => document.fonts.ready);
    await page.mouse.click(w / 2, h * 0.44); await page.waitForTimeout(3400);
    const bar = await page.evaluate(i => { const b = document.querySelectorAll('.bar')[i].querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, barIndex);
    await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1300); await page.screenshot({ path: `i-${name}-1-focus.png` });
    const off = await page.evaluate(() => [...document.querySelectorAll('.bar.is-focused .detail text, .bar.is-focused .cue path')].map(t => { const r = t.getBoundingClientRect(); return [t.textContent.slice(0, 24), Math.round(r.left), Math.round(r.right)]; }).filter(r => r[1] < 0 || r[2] > innerWidth));
    console.log(name, 'umbrella focus, outside window:', JSON.stringify(off));
    await page.click('#info-button'); await page.waitForTimeout(200);
    await page.evaluate(() => document.querySelectorAll('#info details')[1].open = true); await page.waitForTimeout(100);
    await page.screenshot({ path: `i-${name}-2-info.png` }); console.log(name, await st());
    await page.evaluate(() => { document.querySelectorAll('#info details').forEach(d => d.open = false); document.querySelectorAll('#info details')[7].open = true; document.querySelector('#info').scrollTop = 9999; }); await page.screenshot({ path: `i-${name}-3-info-umbrellas.png` });
    if (w > 600) { await page.mouse.click(40, h - 40); await page.waitForTimeout(300); console.log(name, 'after click outside:', await st()); } else { await page.click('#info-button'); }
    await page.click('#info-button'); await page.keyboard.press('Escape'); await page.waitForTimeout(200); console.log(name, 'after escape:', await st());
    const bar2 = await page.evaluate(() => { const b = document.querySelector('.bar.is-focused').querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(bar2.x, bar2.y); await page.waitForTimeout(3300);
    const c = await page.evaluate(() => { const b = document.querySelectorAll('.wbar')[12].querySelector('.seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(c.x, c.y); await page.waitForTimeout(1300); await page.screenshot({ path: `i-${name}-4-call.png` });
    await page.click('#info-button'); await page.evaluate(() => { document.querySelectorAll('#info details').forEach(d => d.open = false); document.querySelectorAll('#info details')[2].open = true; document.querySelector('#info').scrollTop = 0; }); await page.waitForTimeout(150);
    await page.screenshot({ path: `i-${name}-5-info-black.png` }); console.log(name, await st());
    console.log(name, 'errors', JSON.stringify(errors));
    await page.close();
  }
  await browser.close(); server.close();
})();

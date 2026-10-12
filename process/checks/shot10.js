// walk through the waveform screen: overview, focus, zoom to white, and all the way back
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve4'); const pageName = process.argv[2] || 'switchboard_viz.html'; const tag = process.argv[3] || 'v';
const server = http.createServer((req, res) => {
  const f = path.join(root, path.normalize(decodeURIComponent(req.url.split('?')[0])).replace(/^([/\\]|\.\.)+/, ''));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : f.endsWith('.json') ? 'application/json' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8773, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [name, w, h, barIndex] of [['wide', 1920, 1000, 3], ['laptop', 1280, 720, 6], ['phone', 390, 800, 4]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    const st = () => page.evaluate(() => `${state}${busy ? ' (busy)' : ''} | ${document.querySelector('#hud h1').textContent} | ${document.querySelector('#hud-line').textContent.slice(0, 90)}`);
    const shot = n => page.screenshot({ path: `${tag}-${name}-${n}.png` });
    await page.goto('http://localhost:8773/' + pageName); await page.waitForTimeout(1500);
    await page.evaluate(() => document.fonts.ready);
    await page.mouse.click(w / 2, h * 0.44); await page.waitForTimeout(3400);
    const bar = await page.evaluate(i => { const b = document.querySelectorAll('.bar')[i].querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, barIndex);
    await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1200);
    const bar2 = await page.evaluate(() => { const b = document.querySelector('.bar.is-focused').querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(bar2.x, bar2.y); await page.waitForTimeout(900); await shot('1-diving');
    await page.waitForTimeout(700); await shot('2-growing');
    await page.waitForTimeout(1600); await shot('3-wave'); console.log(name, 'wave:', await st());
    const info = await page.evaluate(() => ({ calls: document.querySelectorAll('.wbar').length, topics: [...document.querySelectorAll('.topic')].map(t => t.textContent + (t.style.opacity === '1' ? '' : ' (hidden)')).join(', ') }));
    console.log(name, JSON.stringify(info));
    const callAt = i => page.evaluate(i => { const b = document.querySelectorAll('.wbar')[i].querySelector('.seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, i);
    let c = await callAt(20); await page.mouse.move(c.x, c.y); await page.waitForTimeout(200); console.log(name, 'hover:', await st());
    if (name !== 'phone') { await page.mouse.wheel(0, -600); await page.waitForTimeout(500); await shot('4-scrolled'); console.log(name, 'scrolled k:', await page.evaluate(() => zoomT.k.toFixed(2)));
      await page.keyboard.press('Escape'); await page.waitForTimeout(900); console.log(name, 'after escape k:', await page.evaluate(() => zoomT.k.toFixed(2)), await st()); }
    c = await callAt(20); await page.mouse.click(c.x, c.y); await page.waitForTimeout(1100); await shot('5-focus'); console.log(name, 'focus:', await st());
    const lines = await page.evaluate(() => [...document.querySelectorAll('#lines p')].map(t => { const r = t.getBoundingClientRect(); return { text: t.innerText.replace(/\s+/g, ' '), right: Math.round(r.right), top: Math.round(r.top), bottom: Math.round(r.bottom) }; }));
    console.log(name, 'lines:'); lines.forEach(l => console.log('    ', l.text));
    console.log(name, 'lines outside window:', JSON.stringify(lines.filter(l => l.right > w || l.bottom > h || l.top < 0)), 'overlaps:', lines.slice().sort((a, b) => a.top - b.top).filter((l, i, all) => i && l.top < all[i - 1].bottom).length);
    c = await page.evaluate(() => { const b = document.querySelector('.wbar.is-focused .seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(c.x, c.y); await page.waitForTimeout(800); await shot('6-to-white');
    await page.waitForTimeout(1000); await shot('7-call'); console.log(name, 'call:', await st(), '|', await page.evaluate(() => document.querySelector('#call').innerText.replace(/\n+/g, ' | ')));
    await page.mouse.click(w / 2, h / 2); await page.waitForTimeout(1500); console.log(name, 'back to focus:', await st());
    await page.mouse.click(w - 6, h - 6); await page.waitForTimeout(1100); console.log(name, 'back to wave:', await st(), 'k', await page.evaluate(() => zoomT.k.toFixed(2)));
    await page.mouse.click(w - 6, h - 6); await page.waitForTimeout(1700); await shot('8-umbrellas'); console.log(name, 'back to umbrellas:', await st());
    // resize while on the waveform, then leave
    await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1000);
    const b3 = await page.evaluate(() => { const b = document.querySelector('.bar.is-focused').querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
    await page.mouse.click(b3.x, b3.y); await page.waitForTimeout(3200);
    await page.setViewportSize({ width: w - 100, height: h - 60 }); await page.waitForTimeout(600); console.log(name, 'resized on wave:', await st());
    await page.keyboard.press('Escape'); await page.waitForTimeout(800); await shot('9-after-resize'); console.log(name, 'left after resize:', await st());
    console.log(name, 'errors', JSON.stringify(errors));
    await page.close();
  }
  await browser.close(); server.close();
})();

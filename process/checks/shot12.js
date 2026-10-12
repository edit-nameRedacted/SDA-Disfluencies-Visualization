// the single-call screen: open a call, point at utterances, go back; also a call whose file is missing
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve4'); const pageName = process.argv[2] || 'art.html';
const server = http.createServer((req, res) => {
  const f = path.join(root, path.normalize(decodeURIComponent(req.url.split('?')[0])).replace(/^([/\\]|\.\.)+/, ''));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : f.endsWith('.json') ? 'application/json' : 'text/html' }); res.end(fs.readFileSync(f));
});
(async () => {
  await new Promise(r => server.listen(8775, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  for (const [name, w, h, barIndex, callIndex] of [['wide', 1920, 1000, 3, 20], ['laptop', 1280, 720, 6, 26], ['phone', 390, 800, 4, 20]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    const st = () => page.evaluate(() => `${state}${busy ? ' (busy)' : ''} | ${document.querySelector('#hud h1').textContent} | ${document.querySelector('#hud-line').textContent.slice(0, 60)}`);
    const openWave = async () => {
      const bar = await page.evaluate(i => { const b = document.querySelectorAll('.bar')[i].querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, barIndex);
      await page.mouse.click(bar.x, bar.y); await page.waitForTimeout(1300);
      const bar2 = await page.evaluate(() => { const b = document.querySelector('.bar.is-focused').querySelectorAll('.seg')[1].getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
      await page.mouse.click(bar2.x, bar2.y); await page.waitForTimeout(3300);
    };
    const openCall = async i => {
      let c = await page.evaluate(i => { const b = document.querySelectorAll('.wbar')[i].querySelector('.seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, i);
      await page.mouse.click(c.x, c.y); await page.waitForTimeout(1200);
      c = await page.evaluate(() => { const b = document.querySelector('.wbar.is-focused .seg').getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; });
      await page.mouse.click(c.x, c.y); await page.waitForTimeout(1500);
    };
    await page.goto('http://localhost:8775/' + pageName); await page.waitForTimeout(1500); await page.evaluate(() => document.fonts.ready);
    await page.mouse.click(w / 2, h * 0.44); await page.waitForTimeout(3400);
    await openWave(); await openCall(callIndex);
    await page.screenshot({ path: `c-${name}-1-growing.png` }); await page.waitForTimeout(1500);
    await page.screenshot({ path: `c-${name}-2-call.png` }); console.log(name, 'call:', await st());
    const info = await page.evaluate(() => { const r = [...document.querySelectorAll('.piece')].map(p => p.getBoundingClientRect()); return { pieces: r.length, cords: document.querySelectorAll('.wait').length, maxBottom: Math.round(Math.max(...r.map(b => b.bottom))), maxRight: Math.round(Math.max(...r.map(b => b.right))), minTop: Math.round(Math.min(...r.map(b => b.top))), hudBottom: Math.round(document.querySelector('#hud').getBoundingClientRect().bottom), words: waveFocused.words, calls: waveFocused.conversation_no }; });
    console.log(name, JSON.stringify(info));
    // point at a few utterances of different types
    for (const cls of ['t1', 't4', 't2']) {
      const b = await page.evaluate(cls => { const all = [...document.querySelectorAll('.piece.' + cls)]; const p = all[Math.floor(all.length / 2)]; if (!p) return null; const r = p.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }, cls);
      if (!b) continue;
      await page.mouse.move(b.x, b.y); await page.waitForTimeout(250);
      const say = await page.evaluate(() => { const s = document.querySelector('#say'); const r = s.getBoundingClientRect(); return { hidden: s.hidden, text: s.innerText.replace(/\s+/g, ' ').slice(0, 150), inside: r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight }; });
      console.log(name, cls, JSON.stringify(say));
      if (cls === 't1') await page.screenshot({ path: `c-${name}-3-bubble.png` });
    }
    await page.mouse.move(5, h - 5); await page.waitForTimeout(200);
    await page.setViewportSize({ width: w - 120, height: h - 80 }); await page.waitForTimeout(500); console.log(name, 'resized:', await st(), await page.evaluate(() => document.querySelectorAll('.piece').length));
    await page.mouse.click(w - 130, h - 90); await page.waitForTimeout(1500); console.log(name, 'back after resize:', await st());
    await page.setViewportSize({ width: w, height: h }); await page.waitForTimeout(600);
    await openCall(callIndex + 3); await page.waitForTimeout(1200); console.log(name, 'second call:', await st());
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500); console.log(name, 'escape:', await st(), '| lines shown:', await page.evaluate(() => document.querySelector('#lines').classList.contains('shown')));
    // a call whose file is missing
    await page.route('**/conversations/*.json', r => r.fulfill({ status: 404, body: '' }));
    await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
    await openCall(2); await page.waitForTimeout(800);
    console.log(name, 'missing file:', await st(), '| note:', await page.evaluate(() => document.querySelector('#call-note').hidden ? '(hidden)' : document.querySelector('#call-note').textContent.slice(0, 80)));
    if (name === 'wide') await page.screenshot({ path: `c-${name}-4-missing.png` });
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500); console.log(name, 'back:', await st());
    console.log(name, 'errors', JSON.stringify(errors));
    await page.close();
  }
  await browser.close(); server.close();
})();

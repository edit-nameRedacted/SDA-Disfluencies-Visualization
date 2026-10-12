const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const root = path.resolve('../serve3');
const server = http.createServer((req, res) => {
  const f = path.join(root, path.basename(req.url.split('?')[0]));
  if (!fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': f.endsWith('.csv') ? 'text/csv' : 'text/html' }); res.end(fs.readFileSync(f));
});
const read = page => page.evaluate(() => ({
  rects: document.querySelectorAll('#chart g[fill] rect').length,
  values: [...document.querySelectorAll('.value')].map(e => e.textContent).join(' '),
  order: [...document.querySelectorAll('.axis')].slice(1).map(e => e.textContent).join(''),
  loaderHidden: document.querySelector('#loader').hidden, note: document.querySelector('#note').textContent,
  title: (document.querySelector('#chart g[fill] rect title') || {}).textContent,
}));
(async () => {
  await new Promise(r => server.listen(8767, r));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const d3src = fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8');
  const open = async url => { const page = await browser.newPage({ viewport: { width: 1040, height: 620 } });
    await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: d3src }));
    page.errors = []; page.on('pageerror', e => page.errors.push(e.message));
    await page.goto(url); await page.waitForTimeout(500); return page; };
  let p = await open('http://localhost:8767/umbrella_bars_d3.html');
  console.log('served', JSON.stringify(await read(p)), p.errors); await p.close();
  p = await open('file://' + root + '/umbrella_bars_d3.html');
  console.log('disk before pick', JSON.stringify(await read(p)));
  await p.screenshot({ path: 'd3-disk-before.png' });
  await p.setInputFiles('#picker', root + '/conversations.csv'); await p.waitForTimeout(400);
  console.log('disk after pick', JSON.stringify(await read(p)), p.errors);
  await p.screenshot({ path: 'd3-disk-after.png' }); await p.close();
  await browser.close(); server.close();
})();

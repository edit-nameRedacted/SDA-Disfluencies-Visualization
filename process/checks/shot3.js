const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const html = fs.readFileSync('/mnt/user-data/outputs/umbrella_bars.html', 'utf8')
    .replace('<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>', () => '<script>' + fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8') + '</script>');
  fs.writeFileSync('harness3.html', html);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1040, height: 600 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + process.cwd() + '/harness3.html'); await page.waitForTimeout(300);
  console.log(JSON.stringify(await page.evaluate(() => ({
    rects: document.querySelectorAll('#chart g[fill] rect').length,
    values: [...document.querySelectorAll('.value')].map(e => e.textContent).join(' '),
    order: [...document.querySelectorAll('.axis')][1].textContent,
    yticks: [...document.querySelectorAll('.axis')][0].textContent,
    title: document.querySelector('#chart g[fill] rect title').textContent,
  }))));
  console.log('errors', JSON.stringify(errors));
  await page.screenshot({ path: 'umbrella.png' });
  await browser.close();
})();

const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const page_html = fs.readFileSync('../artifact/conversation-barcodes.html', 'utf8')
    .replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>',
             () => '<script>' + fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8') + '</script>');
  const html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>' + page_html + '</body></html>';
  fs.writeFileSync('harness.html', html);
  const browser = await chromium.launch({ executablePath: fs.existsSync('/opt/pw-browsers/chromium') && fs.statSync('/opt/pw-browsers/chromium').isFile() ? '/opt/pw-browsers/chromium' : undefined });
  const errors = [];
  for (const [name, w, h, scheme] of [['desktop-light', 1180, 1000, 'light'], ['phone-dark', 400, 900, 'dark']]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: scheme, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error') errors.push(name + ': ' + m.text()); });
    page.on('pageerror', e => errors.push(name + ': ' + e.message));
    await page.goto('file://' + process.cwd() + '/harness.html');
    await page.waitForTimeout(400);
    if (errors.length) console.log('early errors', errors);
    const info = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      rects: document.querySelectorAll('svg.strip g.cells rect').length,
      shares: [...document.querySelectorAll('.row.call .share')].map(e => e.textContent).join(' '),
      stripW: document.querySelector('svg.strip').getBoundingClientRect().width,
    }));
    console.log(name, JSON.stringify(info));
    const strip = page.locator('svg.strip').nth(2);
    const box = await strip.boundingBox();
    await page.mouse.move(box.x + box.width * 0.42, box.y + box.height / 2);
    await page.waitForTimeout(100);
    console.log(name, 'tip:', (await page.locator('#tip').innerText()).replace(/\n/g, ' | '));
    await page.screenshot({ path: name + '.png', fullPage: true });
    if (name === 'desktop-light') {
      await page.mouse.move(5, 5);
      await page.locator('label:has(#mode-words)').click();
      await page.waitForTimeout(900);
      await page.locator('summary').click();
      console.log('words shares', await page.evaluate(() => [...document.querySelectorAll('.row.call .share')].map(e => e.textContent).join(' ')));
      console.log('table foot', await page.locator('tfoot').innerText());
      await page.screenshot({ path: 'desktop-light-words.png', fullPage: true });
    }
    await ctx.close();
  }
  console.log('errors', JSON.stringify(errors));
  await browser.close();
})();

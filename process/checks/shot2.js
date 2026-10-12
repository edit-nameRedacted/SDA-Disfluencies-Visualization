const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const page_html = fs.readFileSync('../artifact/conversations-by-topic.html', 'utf8')
    .replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>',
             () => '<script>' + fs.readFileSync('node_modules/d3/dist/d3.min.js', 'utf8') + '</script>');
  const html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>' + page_html + '</body></html>';
  fs.writeFileSync('harness2.html', html);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const errors = [];
  for (const [name, w, h, scheme] of [['t-desktop-light', 1180, 1000, 'light'], ['t-phone-dark', 400, 900, 'dark']]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: scheme, deviceScaleFactor: 1.5 });
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error') errors.push(name + ': ' + m.text()); });
    page.on('pageerror', e => errors.push(name + ': ' + e.message));
    await page.goto('file://' + process.cwd() + '/harness2.html');
    await page.waitForTimeout(500);
    if (errors.length) console.log('early errors', errors);
    console.log(name, JSON.stringify(await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      tiles: document.querySelectorAll('.tile').length, sections: document.querySelectorAll('.umb').length,
      bars: document.querySelectorAll('.tile svg > g:last-of-type > g').length,
      height: document.documentElement.scrollHeight,
      widest: Math.max(...[...document.querySelectorAll('.tile')].map(e => e.getBoundingClientRect().right)) ,
    }))));
    if (name === 't-desktop-light') {
      console.log('table:\n' + await page.evaluate(() => [...document.querySelectorAll('#numbers tr.umb-row')].map(r => [...r.children].map(c => c.textContent).join(' | ')).join('\n')));
      const slot = page.locator('#ov .slot').nth(1); const b = await slot.boundingBox();
      await page.mouse.move(b.x + b.width / 2, b.y + b.height * 0.6); await page.waitForTimeout(80);
      console.log('ov tip:', (await page.locator('#tip').innerText()).replace(/\n/g, ' | '));
      await page.screenshot({ path: 't-ov-hover.png', clip: { x: 0, y: 0, width: 1180, height: 760 } });
    }
    const tile = page.locator('.tile:not(.avg) svg').nth(3); await tile.scrollIntoViewIfNeeded();
    const tb = await tile.boundingBox();
    await page.mouse.move(tb.x + 11, tb.y + tb.height - 20); await page.waitForTimeout(80);
    console.log(name, 'tile tip:', (await page.locator('#tip').innerText()).replace(/\n/g, ' | '));
    await page.screenshot({ path: name + '-hover.png' });
    await page.mouse.move(2, 2);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: name + '.png', fullPage: true });
    await ctx.close();
  }
  console.log('errors', JSON.stringify(errors));
  await browser.close();
})();

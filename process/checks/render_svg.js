const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const svg = fs.readFileSync(process.argv[2], 'utf8').replace(/<\?xml[^>]*\?>/, '');
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 900, height: 420 } });
  // show it as drawn (small) and turned on its side, on the page's paper colour
  await page.setContent(`<body style="margin:0;background:#f8f7f3;display:flex;gap:40px;align-items:center;padding:20px">
    <div style="width:120px">${svg}</div>
    <div style="width:640px;height:230px;position:relative"><div style="position:absolute;left:205px;top:-205px;width:230px;transform:rotate(90deg)">${svg}</div></div></body>`);
  await page.screenshot({ path: process.argv[3] });
  await browser.close();
})();

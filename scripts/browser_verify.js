const { chromium } = require(require('path').resolve(__dirname, '../frontend/node_modules/playwright'));
const fs = require('fs');
const path = require('path');

const screenshotsDir = path.resolve(__dirname, '../results/browser_screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

async function run() {
  console.log('='.repeat(60));
  console.log('Launching Playwright Chromium via Node.js...');
  console.log('='.repeat(60));

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  const consoleMsgs = [];
  const pageErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      consoleMsgs.push(`[${msg.type()}] ${msg.text()}`);
    }
  });

  page.on('pageerror', (err) => {
    pageErrors.push(err.message || String(err));
  });

  // 1. Landing Page / Login
  console.log('Navigating to http://127.0.0.1:5173...');
  await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, '00_login_landing.png') });
  console.log('Captured 00_login_landing.png');

  // If login page is displayed, click "Continue as Guest"
  const guestBtn = page.locator("button:has-text('Continue as Guest')");
  if (await guestBtn.count() > 0) {
    console.log('Found login screen, clicking "Continue as Guest"...');
    await guestBtn.first().click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(screenshotsDir, '01_landing_hero.png') });
    console.log('Captured 01_landing_hero.png');
  }

  // 2. Check Hero pitch
  const heroCount = await page.locator("text=Three AI cleaners propose").count();
  console.log(`Hero pitch visible: ${heroCount > 0}`);

  const allButtons = await page.locator('button').allTextContents();
  console.log('Buttons on dashboard:', allButtons.map(b => b.trim()).filter(Boolean));

  // 3. Switch to Upload Tab
  console.log('Switching to Upload Tab...');
  const uploadTab = page.locator("button:has-text('Upload')").first();
  await uploadTab.click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotsDir, '02_upload_tab.png') });
  console.log('Captured 02_upload_tab.png');

  const uploadButtons = await page.locator('button').allTextContents();
  console.log('Buttons on Upload tab:', uploadButtons.map(b => b.trim()).filter(Boolean));

  // 4. Test Clean Sample Button
  const cleanBtn = page.locator("button:has-text('Try a clean file')");
  if (await cleanBtn.count() > 0) {
    console.log('Clicking "Try a clean file" sample button...');
    await cleanBtn.first().click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotsDir, '03_clean_sample_profile.png') });
    console.log('Captured 03_clean_sample_profile.png');
  }

  // 5. Click Run ConsensusGate
  const runGateBtn = page.locator("button:has-text('Run ConsensusGate')");
  if (await runGateBtn.count() > 0) {
    console.log('Clicking Run ConsensusGate...');
    await runGateBtn.first().click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotsDir, '04_swarm_command_center.png') });
    console.log('Captured 04_swarm_command_center.png');
  }

  // 6. Test Sales Data 3 Sample Button (Clean 822 rows)
  const uploadTab2 = page.locator("button:has-text('Upload')");
  if (await uploadTab2.count() > 0) {
    await uploadTab2.first().click();
    await page.waitForTimeout(1000);
    const salesBtn = page.locator("button:has-text('Try Sales Data 3')");
    if (await salesBtn.count() > 0) {
      console.log('Clicking "Try Sales Data 3" sample button...');
      await salesBtn.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(screenshotsDir, '05_sales_sample_profile.png') });
      console.log('Captured 05_sales_sample_profile.png');

      const runGateBtn3 = page.locator("button:has-text('Run ConsensusGate')");
      if (await runGateBtn3.count() > 0) {
        console.log('Clicking Run ConsensusGate on sales dataset...');
        await runGateBtn3.first().click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: path.join(screenshotsDir, '06_sales_swarm_command_center.png') });
        console.log('Captured 06_sales_swarm_command_center.png');
      }
    }
  }

  await browser.close();

  console.log('='.repeat(60));
  console.log(`Console warnings/errors: ${consoleMsgs.length}`);
  consoleMsgs.forEach((m) => console.log('  ', m));
  console.log(`Page uncaught exceptions: ${pageErrors.length}`);
  pageErrors.forEach((e) => console.log('  ', e));
  console.log('='.repeat(60));

  if (pageErrors.length > 0) {
    process.exit(1);
  }
}

run().catch((err) => {
  console.error('Fatal error running verification:', err);
  process.exit(1);
});

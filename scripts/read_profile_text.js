const { chromium } = require(require('path').resolve('frontend/node_modules/playwright'));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('http://127.0.0.1:5173');
  const guestBtn = page.locator("button:has-text('Continue as Guest')");
  if (await guestBtn.count() > 0) await guestBtn.first().click();
  await page.waitForTimeout(1000);

  // Switch to Upload
  await page.locator("button:has-text('Upload')").first().click();
  await page.waitForTimeout(1000);

  // Click Try Sales Data 3
  await page.locator("button:has-text('Try Sales Data 3')").first().click();
  await page.waitForTimeout(2000);

  const profileHeading = await page.locator("h2").first().textContent();
  const tableRows = await page.locator("tbody tr").count();
  console.log("Profile heading:", profileHeading);
  console.log("Total profile table rows:", tableRows);

  // Run ConsensusGate
  await page.locator("button:has-text('Run ConsensusGate')").first().click();
  await page.waitForTimeout(2500);

  const consensusHeading = await page.locator("h2").first().textContent();
  const agentCards = await page.locator("h3").allTextContents();
  console.log("Consensus heading:", consensusHeading);
  console.log("Visible headings on ConsensusGate:", agentCards);

  await browser.close();
})();

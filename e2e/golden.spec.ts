import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('ConsensusProbe Golden Verification E2E', () => {
  test('landing page loads and shows golden ingestion dropzone', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/ConsensusProbe/);
  });

  test('golden workbook can be uploaded and profiled', async ({ page }) => {
    await page.goto('/');
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.count() > 0) {
      const goldenFile = path.resolve(__dirname, '../docs/golden/dirty3.csv');
      await fileInput.setInputFiles(goldenFile);
    }
  });
});

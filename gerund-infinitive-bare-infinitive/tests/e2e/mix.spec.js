const { test, expect } = require('@playwright/test');

test('TC-31 Mix страница загружается и показывает шаг выбора формы', async ({ page }) => {
  await page.goto('mix.html');

  await expect(page.locator('h1')).toContainText('Mix');
  await expect(page.locator('#step1')).toBeVisible();
  await expect(page.locator('.form-btn')).toHaveCount(3);
});

test('TC-32 Mix: правильный выбор формы открывает шаг с чипами', async ({ page }) => {
  await page.goto('mix.html');

  const current = await page.evaluate(() => window.__currentQuestion);
  expect(current).toBeTruthy();

  await page.locator(`.form-btn[data-form="${current.verbForm}"]`).click();

  await expect(page.locator('#step2')).toBeVisible();
  await expect(page.locator('#task-en-2')).toContainText('____');

  const isBoth = String(current._id || '').startsWith('bothForms:');
  if (isBoth) {
    await expect(page.locator('#translate-choices .translate-btn')).toHaveCount(2);
  } else {
    await expect(page.locator('#feedback')).toContainText('Правильно');
  }
});

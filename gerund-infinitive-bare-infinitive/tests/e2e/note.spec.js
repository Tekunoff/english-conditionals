const { test, expect } = require('@playwright/test');

async function solveCurrentQuestion(page, key) {
  const current = await page.evaluate(() => window.__currentQuestion);
  expect(current).toBeTruthy();

  await page.locator(`.form-btn[data-form="${current.verbForm}"]`).click();
  await expect(page.locator('#step2')).toBeVisible();

  if (key === 'bothForms') {
    await page.locator('#translate-choices .translate-btn').filter({ hasText: new RegExp(`^${current.ru.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }).first().click();
  }
  return current;
}

test('TC-51 Для gerund-only note не показывается (note = null)', async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto('gerund-only.html');

  const current = await solveCurrentQuestion(page, 'gerundOnly');
  expect(current.note).toBeNull();
  await expect(page.locator('#feedback .note-box')).toHaveCount(0);
});

test('TC-52 Для both-forms note показывается', async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto('both-forms.html');

  const current = await solveCurrentQuestion(page, 'bothForms');
  expect(current.note).toBeTruthy();
  await expect(page.locator('#feedback .note-box')).toBeVisible();
});

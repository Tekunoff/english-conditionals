const { test, expect } = require('@playwright/test');

async function getCurrentSentence(page, key) {
  const current = await page.evaluate(() => window.__currentQuestion);
  expect(current).toBeTruthy();
  return current;
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto('gerund-only.html');
});

test('TC-21 Неверная кнопка формы подсвечивается красным', async ({ page }) => {
  const current = await getCurrentSentence(page, 'gerundOnly');
  const wrong = ['gerund', 'infinitive', 'bare'].find((form) => form !== current.verbForm);

  await page.locator(`.form-btn[data-form="${wrong}"]`).click();
  await expect(page.locator(`.form-btn[data-form="${wrong}"]`)).toHaveClass(/wrong/);
});

test('TC-22 Правильная кнопка подсвечивается зеленым и остается доступной', async ({ page }) => {
  const current = await getCurrentSentence(page, 'gerundOnly');
  const wrong = ['gerund', 'infinitive', 'bare'].find((form) => form !== current.verbForm);

  await page.locator(`.form-btn[data-form="${wrong}"]`).click();
  await expect(page.locator(`.form-btn[data-form="${current.verbForm}"]`)).toHaveClass(/correct/);
  await expect(page.locator(`.form-btn[data-form="${current.verbForm}"]`)).toBeEnabled();
});

test('TC-23 После неверного выбора шаг 2 не открывается', async ({ page }) => {
  const current = await getCurrentSentence(page, 'gerundOnly');
  const wrong = ['gerund', 'infinitive', 'bare'].find((form) => form !== current.verbForm);

  await page.locator(`.form-btn[data-form="${wrong}"]`).click();
  await expect(page.locator('#step2')).toBeHidden();
});

test('TC-24 После правильного выбора открывается шаг 2', async ({ page }) => {
  const current = await getCurrentSentence(page, 'gerundOnly');

  await page.locator(`.form-btn[data-form="${current.verbForm}"]`).click();
  await expect(page.locator('#step2')).toBeVisible();
});

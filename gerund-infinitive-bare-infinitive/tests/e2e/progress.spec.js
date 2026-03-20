const { test, expect } = require('@playwright/test');

async function solveCurrentQuestion(page, key) {
  const current = await page.evaluate(() => window.__currentQuestion);
  expect(current).toBeTruthy();

  await page.locator(`.form-btn[data-form="${current.verbForm}"]`).click();
  await expect(page.locator('#step2')).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await page.goto('gerund-only.html');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
});

test('TC-41 После правильного ответа индекс сохраняется в localStorage', async ({ page }) => {
  await solveCurrentQuestion(page, 'gerundOnly');

  const done = await page.evaluate(() => JSON.parse(localStorage.getItem('gerundOnly') || '[]'));
  expect(done.length).toBeGreaterThan(0);
});

test('TC-42 После правильного ответа прогресс-бар увеличивается', async ({ page }) => {
  const before = await page.locator('#progress-bar').getAttribute('style');
  await solveCurrentQuestion(page, 'gerundOnly');
  const after = await page.locator('#progress-bar').getAttribute('style');

  expect(after).not.toBe(before);
});

test('TC-43 Прогресс сохраняется после reload', async ({ page }) => {
  await solveCurrentQuestion(page, 'gerundOnly');
  const beforeText = await page.locator('#progress-info').innerText();

  await page.reload();
  const afterText = await page.locator('#progress-info').innerText();

  expect(afterText).toBe(beforeText);
});

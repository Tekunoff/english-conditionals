const { test, expect } = require('@playwright/test');

test('TC-01 Hub загружается, показывает 5 карточек', async ({ page }) => {
  await page.goto('/index.html');
  await expect(page.locator('.group-card')).toHaveCount(5); // 4 группы + mix
});

test('TC-02 Карточка gerund-only содержит заголовок', async ({ page }) => {
  await page.goto('/index.html');
  await expect(page.locator('.group-card').first()).toContainText('Gerund');
});

test('TC-03 Прогресс-бар отображается на каждой карточке', async ({ page }) => {
  await page.goto('/index.html');
  const bars = page.locator('.progress-bar');
  await expect(bars).toHaveCount(5);
});

test('TC-04 Клик по карточке переходит на exercise screen', async ({ page }) => {
  await page.goto('/index.html');
  await page.locator('.group-card').first().click();
  await expect(page).toHaveURL(/gerund-only\.html/);
});

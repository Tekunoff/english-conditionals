const { test, expect } = require('@playwright/test');

test('TC-11 Страница загружается, виден Шаг 1 (выбор формы)', async ({ page }) => {
  await page.goto('gerund-only.html');
  await expect(page.locator('#step1')).toBeVisible();
  await expect(page.locator('#step2')).not.toBeVisible();
});

test('TC-12 Английское предложение с пропуском отображается в Шаге 1', async ({ page }) => {
  await page.goto('gerund-only.html');
  await expect(page.locator('#task-ru')).toContainText('____');
});

test('TC-13 Три кнопки выбора формы присутствуют', async ({ page }) => {
  await page.goto('gerund-only.html');
  await expect(page.locator('.form-btn')).toHaveCount(3);
});

test('TC-14 Правильный выбор формы разблокирует Шаг 2', async ({ page }) => {
  await page.goto('gerund-only.html');
  // Для gerundOnly правильная форма — gerund, кнопка data-form="gerund"
  await page.locator('.form-btn[data-form="gerund"]').click();
  await expect(page.locator('#step2')).toBeVisible();
});

test('TC-15 Шаг 2 показывает подтверждение ответа', async ({ page }) => {
  await page.goto('gerund-only.html');
  await page.locator('.form-btn[data-form="gerund"]').click();
  await expect(page.locator('#task-en-2')).toContainText('____');
  await expect(page.locator('#feedback')).toContainText('Правильно');
});

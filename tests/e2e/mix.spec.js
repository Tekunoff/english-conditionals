// @ts-check
const { test, expect } = require('@playwright/test');

// ==============================================================
// Вспомогательная функция: пишет правильный ответ для текущего
// предложения на mix.html, используя window._testCurrent.
// ==============================================================
async function buildCorrectAnswerMix(page) {
  const words = await page.evaluate(() => window._testCurrent?.words ?? []);
  for (const word of words) {
    const displayWord = word === 'I' ? 'I' : word.replace(/,+$/, '').toLowerCase();
    const chips = page.locator('#word-bank .chip');
    const count = await chips.count();
    for (let i = 0; i < count; i++) {
      const chip = chips.nth(i);
      const txt = await chip.textContent();
      if (txt?.trim() === displayWord) {
        await chip.click();
        break;
      }
    }
  }
}

// ==============================================================
// TC-39: mix.html загружается, #game видим, sentencesData доступен
// ==============================================================
test('TC-39 mix.html загружается, #game видим, sentencesData доступен', async ({ page }) => {
  await page.goto('/mix.html');
  await expect(page.locator('#game')).toBeVisible();
  const hasData = await page.evaluate(() => typeof window.sentencesData === 'object' && window.sentencesData !== null);
  expect(hasData).toBe(true);
});

// ==============================================================
// TC-40: _testSentences содержит ровно 792 предложения
// ==============================================================
test('TC-40 _testSentences содержит ровно 792 предложения', async ({ page }) => {
  await page.goto('/mix.html');
  const count = await page.evaluate(() => window._testSentences?.length ?? 0);
  expect(count).toBe(792);
});

// ==============================================================
// TC-41: правильный ответ в Mix обновляет localStorage именно
//        того условного типа, из которого взято предложение
// ==============================================================
test('TC-41 Правильный ответ обновляет localStorage исходного conditional', async ({ page }) => {
  await page.goto('/mix.html');

  // Узнаём sourceKey текущего предложения
  const sourceKey = await page.evaluate(() => window._testCurrent?._sourceKey ?? null);
  expect(sourceKey).toBeTruthy();

  // Сохраняем начальный размер done-сета
  const doneBefore = await page.evaluate((key) => {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved).length : 0;
  }, sourceKey);

  await buildCorrectAnswerMix(page);
  await page.locator('#btn-check').click();
  await expect(page.locator('#feedback')).toContainText('Correct');

  // localStorage именно этого ключа должен увеличиться на 1
  const doneAfter = await page.evaluate((key) => {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved).length : 0;
  }, sourceKey);
  expect(doneAfter).toBe(doneBefore + 1);
});

// ==============================================================
// TC-42: #progress-info содержит число 792
// ==============================================================
test('TC-42 #progress-info содержит число 792', async ({ page }) => {
  await page.goto('/mix.html');
  await expect(page.locator('#progress-info')).toBeVisible();
  await expect(page.locator('#progress-info')).toContainText('792');
});

// ==============================================================
// TC-43: кнопка «Назад» присутствует на mix.html и ведёт на index.html
// ==============================================================
test('TC-43 Кнопка Назад присутствует на mix.html и ведёт на index.html', async ({ page }) => {
  await page.goto('/mix.html');
  const btn = page.locator('.btn-back');
  await expect(btn).toBeVisible();
  const href = await btn.getAttribute('href');
  expect(href).toBe('index.html');
});

// ==============================================================
// TC-44: карточка Mix видима на index.html и ссылается на mix.html
// ==============================================================
test('TC-44 Карточка Mix видима на index.html со ссылкой на mix.html', async ({ page }) => {
  await page.goto('/index.html');
  const mixCard = page.locator('a.card-mix');
  await expect(mixCard).toBeVisible();
  const href = await mixCard.getAttribute('href');
  expect(href).toBe('mix.html');
  // Карточка содержит 792 предложения
  await expect(mixCard).toContainText('792');
});

// ==============================================================
// TC-45: после правильного ответа в Mix прогресс-бар Mix на
//        index.html отражает обновлённый суммарный прогресс
// ==============================================================
test('TC-45 После правильного ответа в Mix прогресс-бар на index.html обновляется', async ({ page }) => {
  // Сначала проходим одно предложение в Mix
  await page.goto('/mix.html');
  const sourceKey = await page.evaluate(() => window._testCurrent?._sourceKey ?? null);
  await buildCorrectAnswerMix(page);
  await page.locator('#btn-check').click();
  await expect(page.locator('#feedback')).toContainText('Correct');

  // Открываем index.html и проверяем что mixDone > 0 (прогресс-бар ненулевой)
  await page.goto('/index.html');
  const mixCard = page.locator('a.card-mix');
  await expect(mixCard).toBeVisible();
  // Карточка должна показывать X / 792 изучено
  const countText = await page.locator('#ccmix').textContent();
  expect(countText).toMatch(/\d+/);
  // Ширина прогресс-бара должна быть > 0%
  const barWidth = await page.locator('#pbmix').evaluate(el => el.style.width);
  expect(parseFloat(barWidth)).toBeGreaterThan(0);
});

// ==============================================================
// TC-46: после правильного ответа в Mix #progress-info обновляется
// ==============================================================
test('TC-46 После правильного ответа в Mix #progress-info показывает X / 792 изучено', async ({ page }) => {
  await page.goto('/mix.html');
  await buildCorrectAnswerMix(page);
  await page.locator('#btn-check').click();
  await expect(page.locator('#feedback')).toContainText('Correct');
  const text = await page.locator('#progress-info').textContent();
  expect(text).toMatch(/\d+ \/ 792 изучено/);
});

// ==============================================================
// TC-47: feedback показывает источниковый conditional badge
// ==============================================================
test('TC-47 Feedback показывает метку sourceBadge с названием Conditional', async ({ page }) => {
  await page.goto('/mix.html');
  await buildCorrectAnswerMix(page);
  await page.locator('#btn-check').click();
  await expect(page.locator('.feedback .source-badge')).toBeVisible();
  const badge = await page.locator('.feedback .source-badge').textContent();
  expect(badge).toMatch(/Conditional/);
});

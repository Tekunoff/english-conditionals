// ==============================================================
// TC-01 … TC-10  —  index.html (меню выбора уровня)
// ==============================================================
const { test, expect } = require('@playwright/test');

// Каждый тест в Playwright запускается в новом BrowserContext → localStorage пустой автоматически

// TC-01: страница загружается, заголовок виден
test('TC-01 Страница меню загружается', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('English Practice');
});

// TC-02: все 4 карточки присутствуют
test('TC-02 На меню видно 4 карточки с условными предложениями', async ({ page }) => {
  await page.goto('/');
  const cards = page.locator('.card');
  await expect(cards).toHaveCount(4);
});

// TC-03: карточки ведут на правильные файлы
test('TC-03 Ссылки карточек ведут на 0-3.html', async ({ page }) => {
  await page.goto('/');
  const hrefs = await page.locator('.card').evaluateAll(els => els.map(e => e.getAttribute('href')));
  expect(hrefs).toEqual(['0.html', '1.html', '2.html', '3.html']);
});

// TC-04: без localStorage — каждая карточка показывает реальное число предложений
test('TC-04 Без прогресса карточки показывают число предложений', async ({ page }) => {
  await page.goto('/');
  const expected = ['196 предложений', '196 предложений', '203 предложений', '197 предложений'];
  for (let n = 0; n < 4; n++) {
    await expect(page.locator(`#cc${n}`)).toContainText(expected[n]);
  }
});

// TC-05: с данными в localStorage — карточка показывает верное число изученных
test('TC-05 С прогрессом в localStorage карточка показывает счётчик', async ({ page }) => {
  // addInitScript запускается ДО page.goto, поэтому localStorage уже заполнен при рендере
  await page.addInitScript(() => localStorage.setItem('cond0', JSON.stringify([0, 1, 2, 3, 4])));
  await page.goto('/');
  await expect(page.locator('#cc0')).toContainText('5');
});

// TC-06: ширина прогресс-бара соответствует проценту
test('TC-06 Ширина прогресс-бара соответствует числу изученных', async ({ page }) => {
  // cond1 имеет 196 предложений, 98/196 = 50%
  await page.addInitScript(() => {
    const ids = Array.from({length: 98}, (_, i) => i);
    localStorage.setItem('cond1', JSON.stringify(ids));
  });
  await page.goto('/');
  const width = await page.locator('#pb1').evaluate(el => el.style.width);
  expect(width).toBe('50%');
});

// TC-07: при полном прохождении карточка показывает "✓ Все 200 изучены!"
test('TC-07 При 200/200 карточка показывает итоговое сообщение', async ({ page }) => {
  const allIds = Array.from({length: 203}, (_, i) => i); // totals[cond2] = 203
  await page.addInitScript((ids) => localStorage.setItem('cond2', JSON.stringify(ids)), allIds);
  await page.goto('/');
  await expect(page.locator('#cc2')).toContainText('Все 203 изучены');
});

// TC-08: при полном прохождении прогресс-бар получает класс done (зелёный)
test('TC-08 При 200/200 прогресс-бар становится зелёным (.done)', async ({ page }) => {
  const allIds = Array.from({length: 197}, (_, i) => i); // totals[cond3] = 197
  await page.addInitScript((ids) => localStorage.setItem('cond3', JSON.stringify(ids)), allIds);
  await page.goto('/');
  await expect(page.locator('#pb3')).toHaveClass(/done/);
});

// TC-09: нажатие на карточку Zero переходит на 0.html
test('TC-09 Клик по карточке Zero навигирует на 0.html', async ({ page }) => {
  await page.goto('/');
  await page.locator('.card').first().click();
  await expect(page).toHaveURL(/0\.html/);
});

// TC-10: pageshow перерисовывает счётчик (эмуляция возврата назад)
test('TC-10 Прогресс перерисовывается после pageshow (bfcache)', async ({ page }) => {
  await page.goto('/');
  // Изначально 0 → показывает "196 предложений"
  await expect(page.locator('#cc0')).toContainText('196 предложений');
  // Пишем прогресс и сами стреляем pageshow
  await page.evaluate(() => {
    localStorage.setItem('cond0', JSON.stringify([0, 1, 2]));
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
  });
  await expect(page.locator('#cc0')).toContainText('3');
});

// ==============================================================
// TC-30 … TC-33  —  Персистентность прогресса (localStorage)
// ==============================================================
const { test, expect } = require('@playwright/test');

// Каждый тест запускается в свежем BrowserContext → localStorage пустой автоматически

// TC-30: прогресс сохраняется между перезагрузками страницы
test('TC-30 Прогресс сохраняется после перезагрузки страницы', async ({ page }) => {
  await page.goto('/0.html');

  // Ответить правильно
  await buildCorrectAnswer(page);
  await page.locator('#btn-check').click();
  // После ответа #progress-info показывает «изучено»
  await expect(page.locator('#progress-info')).toContainText('изучено');

  // Перезагрузить страницу
  await page.reload();

  // Прогресс сохранился → снова видим «изучено»
  await expect(page.locator('#progress-info')).toContainText('изучено');
});

// TC-31: уже изученные предложения не попадают в очередь после reload
test('TC-31 Изученные предложения не показываются повторно', async ({ page }) => {
  await page.goto('/0.html');
  const firstSentence = await page.locator('#task-ru').textContent();

  await buildCorrectAnswer(page);
  await page.locator('#btn-check').click();
  await page.locator('#btn-check').click(); // Next →

  // Перезагружаем — первое предложение не должно быть в первых 5 позициях очереди
  await page.reload();

  // Пройти 5 вопросов, ни один не должен совпасть с firstSentence
  const seen = new Set();
  for (let i = 0; i < 5; i++) {
    const q = await page.locator('#task-ru').textContent();
    seen.add(q?.trim());
    // Пропускаем
    await page.locator('#btn-skip').click();
    await page.locator('#btn-check').click(); // Next →
  }
  expect(seen.has(firstSentence?.trim())).toBe(false);
});

// TC-32: importProgress восстанавливает done из JSON
test('TC-32 importProgress восстанавливает прогресс из JSON', async ({ page }) => {
  await page.goto('/0.html');
  const importData = JSON.stringify({ key: 'cond0', done: [0, 1, 2, 5, 10], total: 200 });

  await page.evaluate((data) => {
    const file = new File([data], 'cond0-progress.json', { type: 'application/json' });
    const dt = new DataTransfer();
    dt.items.add(file);
    const input = document.getElementById('import-file');
    Object.defineProperty(input, 'files', { value: dt.files });
    input.dispatchEvent(new Event('change'));
  }, importData);

  await page.waitForTimeout(300);
  // После импорта #progress-info показывает 5 из общего счёта
  await expect(page.locator('#progress-info')).toContainText('5');
});

// TC-33: при старте без неизученных предложений сразу экран "все изучены"
test('TC-33 Если всё изучено — показывается экран завершения без игры', async ({ page }) => {
  // Заполняем localStorage всеми ID (0.html имеет 196 предложений с _id 0..195)
  const allIds = Array.from({ length: 200 }, (_, i) => i); // 200 > 196 → всё равно все помечены
  await page.addInitScript((ids) => {
    localStorage.setItem('cond0', JSON.stringify(ids));
  }, allIds);
  await page.goto('/0.html');

  await expect(page.locator('#game')).not.toBeVisible();
  await expect(page.locator('.finish')).toHaveClass(/show/);
  await expect(page.locator('#finish')).toContainText('196'); // sentences.length = 196
});

// ==============================================================
// Вспомогательная функция (дублируем, чтобы файл был независимым)
// ==============================================================
async function buildCorrectAnswer(page) {
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

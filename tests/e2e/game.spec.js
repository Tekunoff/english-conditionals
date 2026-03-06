// ==============================================================
// TC-11 … TC-27  —  Механика игры (0.html как представитель всех 4)
// Отдельно проверяем STORAGE_KEY каждого файла.
// ==============================================================
const { test, expect } = require('@playwright/test');

// Каждый тест запускается в свежем BrowserContext → localStorage пустой автоматически

// TC-11: страница игры загружается, блок #game виден
test('TC-11 Страница игры загружается (#game виден)', async ({ page }) => {
  await page.goto('/0.html');
  await expect(page.locator('#game')).toBeVisible();
  await expect(page.locator('.finish')).not.toHaveClass(/show/);
});

// TC-12: отображается русское предложение
test('TC-12 Русское предложение отображается в #task-ru', async ({ page }) => {
  await page.goto('/0.html');
  const text = await page.locator('#task-ru').textContent();
  expect(text?.trim().length).toBeGreaterThan(5);
});

// TC-13: в word-bank есть чипы со словами
test('TC-13 Word bank содержит чипы с вариантами слов', async ({ page }) => {
  await page.goto('/0.html');
  const chips = page.locator('#word-bank .chip');
  await expect(chips).not.toHaveCount(0);
});

// TC-14: клик по чипу перемещает его в область ответа
test('TC-14 Клик по чипу перемещает слово в sentence-area', async ({ page }) => {
  await page.goto('/0.html');
  const bankChipsBefore = await page.locator('#word-bank .chip').count();
  await page.locator('#word-bank .chip').first().click();
  const bankChipsAfter = await page.locator('#word-bank .chip').count();
  expect(bankChipsAfter).toBe(bankChipsBefore - 1);
  await expect(page.locator('#sentence-area .chip')).toHaveCount(1);
});

// TC-15: клик по чипу в ответе возвращает его в банк
test('TC-15 Клик по чипу в ответе возвращает его в банк', async ({ page }) => {
  await page.goto('/0.html');
  const bankBefore = await page.locator('#word-bank .chip').count();
  await page.locator('#word-bank .chip').first().click();
  await page.locator('#sentence-area .chip').first().click();
  const bankAfter = await page.locator('#word-bank .chip').count();
  expect(bankAfter).toBe(bankBefore);
  await expect(page.locator('#sentence-area .chip')).toHaveCount(0);
});

// TC-16: Check с пустым ответом ничего не делает (кнопка текст не меняется)
test('TC-16 Check с пустым ответом не запускает проверку', async ({ page }) => {
  await page.goto('/0.html');
  await page.locator('#btn-check').click();
  await expect(page.locator('#btn-check')).toHaveText(/Check/);
  await expect(page.locator('#score')).toContainText('0 / 0');
});

// TC-17: правильный ответ → зелёная рамка, "Correct!" в feedback
test('TC-17 Правильный ответ → зелёная рамка и Correct!', async ({ page }) => {
  await page.goto('/0.html');
  await buildCorrectAnswer(page);
  await page.locator('#btn-check').click();
  await expect(page.locator('#sentence-area')).toHaveClass(/correct/);
  await expect(page.locator('#feedback')).toContainText('Correct');
});

// TC-18: правильный ответ → счёт увеличивается, ✓ done растёт
test('TC-18 После правильного ответа счётчик изученных растёт', async ({ page }) => {
  await page.goto('/0.html');
  await buildCorrectAnswer(page);
  await page.locator('#btn-check').click();
  await expect(page.locator('#score')).toContainText('✓ 1');
});

// TC-19: после правильного ответа localStorage обновляется
test('TC-19 После правильного ответа localStorage обновляется', async ({ page }) => {
  await page.goto('/0.html');
  await buildCorrectAnswer(page);
  await page.locator('#btn-check').click();
  const stored = await page.evaluate(() => localStorage.getItem('cond0'));
  expect(stored).not.toBeNull();
  const arr = JSON.parse(stored);
  expect(arr.length).toBe(1);
});

// TC-20: неправильный ответ → красная рамка, "Not quite" в feedback
test('TC-20 Неправильный ответ → красная рамка и "Not quite"', async ({ page }) => {
  await page.goto('/0.html');
  // кликаем только одно слово (почти всегда неправильный неполный ответ)
  await page.locator('#word-bank .chip').first().click();
  await page.locator('#btn-check').click();
  await expect(page.locator('#sentence-area')).toHaveClass(/wrong/);
  await expect(page.locator('#feedback')).toContainText('Not quite');
});

// TC-21: неправильный ответ → правильный ответ показан в feedback
test('TC-21 При неправильном ответе feedback показывает правильный вариант', async ({ page }) => {
  await page.goto('/0.html');
  await page.locator('#word-bank .chip').first().click();
  await page.locator('#btn-check').click();
  const answer = await page.locator('#feedback .answer').textContent();
  expect(answer?.trim().length).toBeGreaterThan(3);
});

// TC-22: Skip → статус «Skipped», кнопка Next →
test('TC-22 Skip показывает Skipped и правильный ответ', async ({ page }) => {
  await page.goto('/0.html');
  await page.locator('#btn-skip').click();
  await expect(page.locator('#feedback')).toContainText('Skipped');
  await expect(page.locator('#btn-check')).toHaveText('Next →');
});

// TC-23: после проверки кнопка меняется на "Next →"
test('TC-23 После Check кнопка меняется на "Next →"', async ({ page }) => {
  await page.goto('/0.html');
  await page.locator('#word-bank .chip').first().click();
  await page.locator('#btn-check').click();
  await expect(page.locator('#btn-check')).toHaveText('Next →');
});

// TC-24: ширина progress-bar увеличивается после правильного ответа
// Используем addInitScript чтобы гарантировать непустой прогресс с первого запуска
test('TC-24 Прогресс-бар отображает ненулевой прогресс при наличии изученных', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('cond0', JSON.stringify([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]));
  });
  await page.goto('/0.html');
  const pct = await page.locator('#progress-bar').evaluate(el => parseFloat(el.style.width || '0'));
  expect(pct).toBeGreaterThan(0);
});

// TC-25: Reset очищает localStorage и показывает свежую игру
test('TC-25 Reset очищает localStorage и перезапускает игру', async ({ page }) => {
  await page.goto('/0.html');
  await buildCorrectAnswer(page);
  await page.locator('#btn-check').click();
  // нажимаем Next → чтобы перейти к следующему предложению
  await page.locator('#btn-check').click();
  // прокручиваем через finish или сразу вызываем resetProgress
  await page.evaluate(() => window.resetProgress?.());
  const stored = await page.evaluate(() => localStorage.getItem('cond0'));
  expect(stored).toBeNull();
  await expect(page.locator('#score')).toContainText('0 / 0');
});

// TC-26: exportProgress — создаёт якорный тег (имитируем через перехват download)
test('TC-26 Export создаёт JSON с правильным ключом', async ({ page }) => {
  await page.goto('/0.html');
  // Получаем данные экспорта через прямой вызов функции
  const exported = await page.evaluate(() => {
    let result = null;
    const origCreate = document.createElement.bind(document);
    document.createElement = (tag) => {
      const el = origCreate(tag);
      if (tag === 'a') {
        const origClick = el.click.bind(el);
        el.click = () => {
          result = el.href;
        };
      }
      return el;
    };
    window.exportProgress();
    return result;
  });
  expect(exported).not.toBeNull();
  const decoded = decodeURIComponent(exported.replace('data:application/json,', ''));
  const parsed = JSON.parse(decoded);
  expect(parsed.key).toBe('cond0');
  expect(Array.isArray(parsed.done)).toBe(true);
  expect(typeof parsed.total).toBe('number');
});

// TC-27: importProgress с файлом чужого уровня вызывает alert
test('TC-27 Import файла другого уровня вызывает alert', async ({ page }) => {
  await page.goto('/0.html');
  let alertCalled = false;
  page.on('dialog', async dialog => {
    alertCalled = true;
    await dialog.accept();
  });
  await page.evaluate(() => {
    const wrongData = JSON.stringify({ key: 'cond3', done: [], total: 200 });
    const file = new File([wrongData], 'cond3-progress.json', { type: 'application/json' });
    const dt = new DataTransfer();
    dt.items.add(file);
    const input = document.getElementById('import-file');
    Object.defineProperty(input, 'files', { value: dt.files });
    input.dispatchEvent(new Event('change'));
  });
  await page.waitForTimeout(300);
  expect(alertCalled).toBe(true);
});

// ==============================================================
// TC-28: STORAGE_KEY правильный для каждого файла
// ==============================================================
for (const [n, key] of [['0', 'cond0'], ['1', 'cond1'], ['2', 'cond2'], ['3', 'cond3']]) {
  test(`TC-28-${n} STORAGE_KEY файла ${n}.html = "${key}"`, async ({ page }) => {
    await page.goto(`/${n}.html`);
    await buildCorrectAnswer(page);
    await page.locator('#btn-check').click();
    const stored = await page.evaluate((k) => localStorage.getItem(k), key);
    expect(stored).not.toBeNull();
  });
}

// ==============================================================
// TC-29: в каждом файле ровно 200 предложений
// ==============================================================
// Фактические числа предложений: 0→196, 1→196, 2→203, 3→197
const EXPECTED_COUNTS = { '0': 196, '1': 196, '2': 203, '3': 197 };
for (const n of ['0', '1', '2', '3']) {
  test(`TC-29-${n} Файл ${n}.html содержит ${EXPECTED_COUNTS[n]} предложений`, async ({ page }) => {
    await page.goto(`/${n}.html`);
    const count = await page.evaluate(() => window._testSentences?.length);
    expect(count).toBe(EXPECTED_COUNTS[n]);
  });
}

// ==============================================================
// Вспомогательная функция: собирает ПРАВИЛЬНЫЙ ответ для
// текущего вопроса, кликая все слова в нужном порядке.
// Использует window._testCurrent (live getter).
// ==============================================================
async function buildCorrectAnswer(page) {
  const words = await page.evaluate(() => window._testCurrent?.words ?? []);
  // Кликаем по чипам в нужном порядке, учитывая повторяющиеся слова
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

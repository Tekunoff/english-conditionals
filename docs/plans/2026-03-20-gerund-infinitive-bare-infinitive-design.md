# Gerund / Infinitive / Bare Infinitive — Design Document

**Date:** 2026-03-20  
**Status:** Approved

---

## Goal

Создать новый обучающий модуль `gerund-infinitive-bare-infinitive/` для практики выбора глагольной формы (герундий / инфинитив / bare infinitive) в контексте предложений. Модуль по механике аналогичен `english-conditionals/`, но добавляет шаг явного выбора формы перед составлением предложения.

---

## Architecture

**Подход:** Клон структуры `english-conditionals` с расширением механики. Никаких изменений в существующем `english-conditionals/` — он работает и остаётся нетронутым.

**Стек:** Pure HTML/CSS/JS, без фреймворков, `localStorage` для прогресса, Playwright для E2E тестов, Python для генерации данных.

**Новое в механике:** Двухшаговое упражнение:
1. Шаг 1 — выбрать форму глагола (3 кнопки)
2. Шаг 2 — составить предложение из чипов (как в conditionals)

---

## File Structure

```
gerund-infinitive-bare-infinitive/
  index.html                  — хаб модуля: 4 карточки групп + mix + прогресс
  gerund-only.html            — группа А (enjoy, mind, avoid, finish, keep...)
  infinitive-only.html        — группа Б (want, need, decide, hope, refuse...)
  bare-infinitive.html        — группа В (make, let, have, help...)
  both-forms.html             — группа Г (like, love, hate, stop, remember... + разница)
  mix.html                    — все 4 группы вперемешку
  sentences-data.js           — данные, генерируется скриптом
  js/
    chips.js                  — chip-механика (после рефакторинга)
    progress.js               — save/load localStorage (после рефакторинга)
    exercise.js               — логика Шага 1 + Шага 2, check (после рефакторинга)
  scripts/
    gen_sentences_data.py     — генератор sentences-data.js
    validate_sentences_data.py — валидатор данных
  tests/
    package.json
    playwright.config.js
    e2e/
      index.spec.js
      exercise.spec.js
      validation.spec.js
      progress.spec.js
      mix.spec.js
      note.spec.js
```

---

## Verb Groups

| Ключ localStorage | Файл | Глаголы | Форма |
|---|---|---|---|
| `gerundOnly` | `gerund-only.html` | enjoy, mind, avoid, finish, keep, consider, suggest, risk, practise, deny | только герундий (`doing`) |
| `infinitiveOnly` | `infinitive-only.html` | want, need, decide, hope, refuse, agree, plan, manage, fail, afford | только инфинитив (`to do`) |
| `bareInfinitive` | `bare-infinitive.html` | make, let, have, help, see, hear, feel, watch | bare infinitive (`do`) |
| `bothForms` | `both-forms.html` | like, love, hate, stop, remember, forget, try, regret, go on, mean | обе формы, разный смысл |

**Объём:** ~100 предложений на группу, ~400 итого.

---

## Data Schema

```js
window.sentencesData = {
  gerundOnly: [
    {
      words: ["He", "couldn't", "help", "laughing"],
      ru: "Он не мог не смеяться",
      verbForm: "gerund",      // "gerund" | "infinitive" | "bare"
      keyVerb: "laughing",     // должен присутствовать в words[]
      note: null               // только для bothForms
    }
  ],
  bothForms: [
    {
      words: ["I", "stopped", "smoking"],
      ru: "Я перестал курить",
      verbForm: "gerund",
      keyVerb: "smoking",
      note: "stop + gerund = перестать делать"
    },
    {
      words: ["I", "stopped", "to", "smoke"],
      ru: "Я остановился, чтобы покурить",
      verbForm: "infinitive",
      keyVerb: "to smoke",
      note: "stop + infinitive = остановиться ради цели"
    }
  ]
}
```

**Инварианты (проверяются скриптом `validate_sentences_data.py`):**
- поля `words`, `ru`, `verbForm`, `keyVerb` — обязательны у каждой записи
- `verbForm` ∈ `{"gerund", "infinitive", "bare"}`
- `keyVerb` присутствует в массиве `words`
- нет полных дубликатов по `words`

---

## Exercise Screen Mechanics

### Шаг 1 — Выбор формы глагола

- Показывается русский перевод (`ru`)
- Три кнопки: `doing` (gerund) / `to do` (infinitive) / `do` (bare)
- Неверный выбор: кнопка краснеет, правильная зеленеет — нужно нажать правильную чтобы продолжить
- Для группы Г: перевод даёт достаточно контекста для выбора формы

### Шаг 2 — Составление предложения (чипы)

- Те же чипы что в `english-conditionals`
- Слова перемешаны в `.word-bank`, пользователь собирает в `.sentence-area`
- Кнопки `Проверить` / `Пропустить`
- Для `bothForms`: после правильного ответа показывается `note` (1 строка)

### Прогресс

- `localStorage.setItem('gerundOnly', JSON.stringify([0, 3, 5, ...]))` — индексы выполненных предложений
- Аналогично для `infinitiveOnly`, `bareInfinitive`, `bothForms`
- `index.html` читает все 4 ключа для прогресс-баров

---

## After-Build Tasks (обязательны в плане реализации)

### 1. `/review-pr` существующего кода

Перед реализацией нового модуля — запустить `/review-pr` на `english-conditionals/`, чтобы выявить паттерны для переноса и антипаттерны для избегания.

### 2. Рефакторинг

После того как все 5 упражнений работают — выделить общую логику в `js/`:
- `chips.js` — chip-механика (перетаскивание, клик)
- `progress.js` — save/load localStorage
- `exercise.js` — логика Шага 1 + Шага 2, проверка

Цель: HTML-файлы упражнений отличаются только одной переменной `const DATA_KEY = 'gerundOnly'`.

### 3. Анализ пирамиды тестирования

| Уровень | Инструмент | Файл | Что проверяет |
|---|---|---|---|
| Данные | Python | `validate_sentences_data.py` | Целостность sentences-data.js |
| E2E | Playwright | `exercise.spec.js` | Happy path: выбор формы + чипы |
| E2E | Playwright | `validation.spec.js` | Неверный выбор формы — ошибка |
| E2E | Playwright | `progress.spec.js` | Прогресс в localStorage |
| E2E | Playwright | `mix.spec.js` | Mix показывает все 4 группы |
| E2E | Playwright | `note.spec.js` | Note показывается для bothForms |
| E2E | Playwright | `index.spec.js` | Хаб: карточки, прогресс-бары |

---

## Decisions Log

| Решение | Причина |
|---|---|
| `english-conditionals/` не трогать | Работает, риск регрессий не оправдан |
| Нет общего `english-app/` хаба в v1 | YAGNI — хаб нужен только если модулей 2+ и они должны быть связаны |
| Рефакторинг после реализации, не до | Сначала рабочий продукт, потом чистота |
| Фиксированный ответ для bothForms | Русский перевод однозначно определяет нужную форму |
| `note` только для bothForms | Для групп А/Б/В правило простое, объяснение избыточно |

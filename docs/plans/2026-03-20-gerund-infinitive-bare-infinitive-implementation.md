# Gerund / Infinitive / Bare Infinitive — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Создать модуль `gerund-infinitive-bare-infinitive/` — обучающая игра на выбор глагольной формы + составление предложений, по механике аналогичная `english-conditionals/`.

**Architecture:** Клон структуры `english-conditionals` с расширением механики (двухшаговое упражнение: сначала выбрать форму, потом собрать предложение из чипов). Никаких изменений в `english-conditionals/`.

**Tech Stack:** Pure HTML/CSS/JS, localStorage, Playwright (E2E), Python 3 (генерация и валидация данных)

**Design Doc:** `docs/plans/2026-03-20-gerund-infinitive-bare-infinitive-design.md`

---

## Task 0: Code Review существующего кода

**Files:**
- Read: `english-conditionals/0.html`
- Read: `english-conditionals/index.html`
- Read: `english-conditionals/mix.html`
- Read: `english-conditionals/scripts/gen_sentences_data.py`
- Read: `english-conditionals/tests/e2e/game.spec.js`

**Step 1: Запустить `/review-pr` на english-conditionals**

В Copilot Chat выполнить:
```
/review-pr
```
И скопировать в него содержимое `english-conditionals/` (или указать нужные файлы).

**Step 2: Зафиксировать ключевые паттерны для переноса**

Из review выписать:
- CSS-классы для переиспользования
- JS-паттерны для chip-механики
- Структуру `const sentences = [...]` в HTML
- Антипаттерны, которых стоит избегать

---

## Task 1: Scaffold — структура папок и тестовое окружение

**Files:**
- Create: `gerund-infinitive-bare-infinitive/scripts/.gitkeep`
- Create: `gerund-infinitive-bare-infinitive/js/.gitkeep`
- Create: `gerund-infinitive-bare-infinitive/tests/package.json`
- Create: `gerund-infinitive-bare-infinitive/tests/playwright.config.js`

**Step 1: Создать структуру папок**

```bash
mkdir -p gerund-infinitive-bare-infinitive/{scripts,js,tests/e2e}
touch gerund-infinitive-bare-infinitive/scripts/.gitkeep
touch gerund-infinitive-bare-infinitive/js/.gitkeep
```

**Step 2: Создать `tests/package.json`**

```json
{
  "name": "gerund-infinitive-bare-infinitive-tests",
  "version": "1.0.0",
  "scripts": {
    "test": "playwright test",
    "test:report": "playwright show-report playwright-report"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

**Step 3: Создать `tests/playwright.config.js`**

```js
// @ts-check
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 15000,
  use: {
    baseURL: 'http://localhost:8082',
    headless: true,
  },
  webServer: {
    command: 'python3 -m http.server 8082 --directory ..',
    url: 'http://localhost:8082',
    reuseExistingServer: false,
    timeout: 10000,
  },
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
});
```

**Step 4: Установить зависимости**

```bash
cd gerund-infinitive-bare-infinitive/tests
npm install
npx playwright install chromium
```

**Step 5: Commit**

```bash
git add gerund-infinitive-bare-infinitive/
git commit -m "feat: scaffold gerund-infinitive-bare-infinitive structure"
```

---

## Task 2: Скрипт генерации данных

**Files:**
- Create: `gerund-infinitive-bare-infinitive/scripts/gen_sentences_data.py`

**Step 1: Создать `scripts/gen_sentences_data.py`**

Скрипт извлекает `const sentences = [...]` из каждого HTML-файла упражнения и объединяет в `sentences-data.js`:

```python
#!/usr/bin/env python3
"""Generate sentences-data.js from all exercise HTML files."""
import re, json, os

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

def extract_sentences(filename):
    with open(filename, encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'const sentences = (\[[\s\S]*?\n\];)', text)
    if not m:
        print(f'NOT FOUND in {filename}')
        return None
    arr_text = m.group(1).rstrip(';')
    # Remove JS single-line comments
    arr_text = re.sub(r'//[^\n]*', '', arr_text)
    # Remove blank lines
    arr_text = re.sub(r'\n\s*\n', '\n', arr_text)
    # Quote all unquoted JS object keys: word: -> "word":
    arr_text = re.sub(r'(?<!["\w])([a-zA-Z_]\w*)\s*:', r'"\1":', arr_text)
    try:
        return json.loads(arr_text)
    except Exception as e:
        print(f'JSON error in {filename}: {e}')
        # Show context around error
        err_str = str(e)
        char_match = re.search(r'char (\d+)', err_str)
        if char_match:
            pos = int(char_match.group(1))
            print('Context:', repr(arr_text[max(0, pos-40):pos+40]))
        return None

files = [
    ('gerund-only.html',       'gerundOnly'),
    ('infinitive-only.html',   'infinitiveOnly'),
    ('bare-infinitive.html',   'bareInfinitive'),
    ('both-forms.html',        'bothForms'),
]

result = {}
for filename, key in files:
    data = extract_sentences(filename)
    if data is not None:
        result[key] = data
        print(f'{filename} -> {key}: {len(data)} sentences OK')

with open('sentences-data.js', 'w', encoding='utf-8') as f:
    f.write('// Auto-generated by scripts/gen_sentences_data.py\n')
    f.write('// Do not edit manually — run the script to regenerate\n')
    f.write('window.sentencesData = ')
    f.write(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    f.write(';\n')

total = sum(len(v) for v in result.values())
print(f'\nsentences-data.js written: {total} total sentences across {len(result)} keys')
```

**Step 2: Commit**

```bash
git add gerund-infinitive-bare-infinitive/scripts/gen_sentences_data.py
git commit -m "feat: add gen_sentences_data.py for new module"
```

---

## Task 3: Скрипт валидации данных (TDD)

**Files:**
- Create: `gerund-infinitive-bare-infinitive/scripts/validate_sentences_data.py`

**Step 1: Написать `validate_sentences_data.py`**

```python
#!/usr/bin/env python3
"""Validate sentences-data.js integrity.
Usage: python3 scripts/validate_sentences_data.py
Exit code 0 = all valid, 1 = errors found.
"""
import json, re, sys, os

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

VALID_VERB_FORMS = {"gerund", "infinitive", "bare"}
REQUIRED_KEYS = {"words", "ru", "verbForm", "keyVerb"}

with open('sentences-data.js', encoding='utf-8') as f:
    content = f.read()

# Extract JSON from JS file
m = re.search(r'window\.sentencesData = (\{[\s\S]+\});', content)
if not m:
    print('ERROR: Cannot parse sentences-data.js')
    sys.exit(1)

data = json.loads(m.group(1))
errors = []

for group_key, sentences in data.items():
    seen_words = []
    for i, s in enumerate(sentences):
        loc = f'{group_key}[{i}]'

        # Required keys
        for key in REQUIRED_KEYS:
            if key not in s:
                errors.append(f'{loc}: missing field "{key}"')

        if 'verbForm' in s and s['verbForm'] not in VALID_VERB_FORMS:
            errors.append(f'{loc}: verbForm="{s["verbForm"]}" not in {VALID_VERB_FORMS}')

        if 'keyVerb' in s and 'words' in s:
            words_str = ' '.join(s['words'])
            if s['keyVerb'] not in words_str:
                errors.append(f'{loc}: keyVerb="{s["keyVerb"]}" not found in words={s["words"]}')

        # Duplicate detection
        words_tuple = tuple(s.get('words', []))
        if words_tuple in seen_words:
            errors.append(f'{loc}: duplicate sentence {s.get("words")}')
        seen_words.append(words_tuple)

if errors:
    print(f'VALIDATION FAILED: {len(errors)} error(s)')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)

total = sum(len(v) for v in data.values())
print(f'OK: {total} sentences validated across {len(data)} groups')
sys.exit(0)
```

**Step 2: Проверить что скрипт работает (пока нет sentences-data.js — ожидается ошибка)**

```bash
cd gerund-infinitive-bare-infinitive
python3 scripts/validate_sentences_data.py
# Expected: ERROR: Cannot parse sentences-data.js
```

**Step 3: Commit**

```bash
git add gerund-infinitive-bare-infinitive/scripts/validate_sentences_data.py
git commit -m "feat: add validate_sentences_data.py"
```

---

## Task 4: Данные — gerund-only.html (HTML + sentences)

**Files:**
- Create: `gerund-infinitive-bare-infinitive/gerund-only.html`

**Step 1: Создать `gerund-only.html` с данными**

Структура файла — аналогична `english-conditionals/0.html`, но содержит поля `verbForm`, `keyVerb`, `note: null`.  
~100 предложений на глаголы: `enjoy, mind, avoid, finish, keep, consider, suggest, risk, practise, deny, miss, fancy, can't help, can't stand, it's worth`.

Шаблон начала файла (CSS и HTML реализуется в Task 6, здесь только данные):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Gerund Only</title>
  <!-- CSS будет добавлен в Task 6 -->
</head>
<body>
<script>
const DATA_KEY = 'gerundOnly';
const sentences = [
  {words:["I","enjoy","swimming","in","the","sea"],ru:"Мне нравится плавать в море",verbForm:"gerund",keyVerb:"swimming",note:null},
  {words:["She","doesn't","mind","waiting","for","a","few","minutes"],ru:"Она не против подождать несколько минут",verbForm:"gerund",keyVerb:"waiting",note:null},
  {words:["He","avoids","eating","junk","food"],ru:"Он избегает есть вредную еду",verbForm:"gerund",keyVerb:"eating",note:null},
  {words:["They","finished","painting","the","house"],ru:"Они закончили красить дом",verbForm:"gerund",keyVerb:"painting",note:null},
  {words:["She","keeps","checking","her","phone"],ru:"Она постоянно проверяет телефон",verbForm:"gerund",keyVerb:"checking",note:null},
  {words:["I","consider","moving","to","a","new","city"],ru:"Я думаю о переезде в новый город",verbForm:"gerund",keyVerb:"moving",note:null},
  {words:["He","suggested","going","to","the","cinema"],ru:"Он предложил сходить в кино",verbForm:"gerund",keyVerb:"going",note:null},
  {words:["She","risks","losing","her","job"],ru:"Она рискует потерять работу",verbForm:"gerund",keyVerb:"losing",note:null},
  {words:["I","practise","speaking","English","every","day"],ru:"Я практикую разговорный английский каждый день",verbForm:"gerund",keyVerb:"speaking",note:null},
  {words:["He","denied","taking","the","money"],ru:"Он отрицал, что взял деньги",verbForm:"gerund",keyVerb:"taking",note:null},
  {words:["I","miss","living","near","the","beach"],ru:"Я скучаю по жизни у моря",verbForm:"gerund",keyVerb:"living",note:null},
  {words:["Do","you","fancy","going","out","tonight?"],ru:"Хочешь выйти сегодня вечером?",verbForm:"gerund",keyVerb:"going",note:null},
  {words:["He","can't","help","laughing","at","silly","jokes"],ru:"Он не может не смеяться над глупыми шутками",verbForm:"gerund",keyVerb:"laughing",note:null},
  {words:["I","can't","stand","waiting","in","long","queues"],ru:"Я не выношу стоять в длинных очередях",verbForm:"gerund",keyVerb:"waiting",note:null},
  {words:["It's","worth","trying","this","restaurant"],ru:"Стоит попробовать этот ресторан",verbForm:"gerund",keyVerb:"trying",note:null},
  {words:["She","enjoys","reading","novels","before","bed"],ru:"Ей нравится читать романы перед сном",verbForm:"gerund",keyVerb:"reading",note:null},
  {words:["They","avoided","making","eye","contact"],ru:"Они избегали зрительного контакта",verbForm:"gerund",keyVerb:"making",note:null},
  {words:["He","finished","writing","the","report"],ru:"Он закончил писать отчёт",verbForm:"gerund",keyVerb:"writing",note:null},
  {words:["She","keeps","interrupting","me"],ru:"Она постоянно меня перебивает",verbForm:"gerund",keyVerb:"interrupting",note:null},
  {words:["I","don't","mind","helping","you"],ru:"Я не против помочь тебе",verbForm:"gerund",keyVerb:"helping",note:null},
  // продолжить до ~100 предложений следуя тому же паттерну
];
</script>
</body>
</html>
```

**Важно:** Сгенерировать ~100 предложений, используя Claude / Copilot Chat с промптом:
```
Generate 80 more English sentences where the verb requires GERUND (doing).
Use verbs: enjoy, mind, avoid, finish, keep, consider, suggest, risk, practise, deny, miss, fancy, can't help, can't stand, it's worth.
Format: {words:["..."], ru:"...", verbForm:"gerund", keyVerb:"...", note:null}
```

**Step 2: Commit**

```bash
git add gerund-infinitive-bare-infinitive/gerund-only.html
git commit -m "feat: add gerund-only sentence data (~100 sentences)"
```

---

## Task 5: Данные — infinitive-only.html

**Files:**
- Create: `gerund-infinitive-bare-infinitive/infinitive-only.html`

**Step 1: Создать файл с данными**

```js
const DATA_KEY = 'infinitiveOnly';
const sentences = [
  {words:["I","want","to","learn","Spanish"],ru:"Я хочу выучить испанский",verbForm:"infinitive",keyVerb:"to learn",note:null},
  {words:["She","needs","to","finish","this","by","Friday"],ru:"Ей нужно закончить это к пятнице",verbForm:"infinitive",keyVerb:"to finish",note:null},
  {words:["He","decided","to","quit","his","job"],ru:"Он решил уволиться",verbForm:"infinitive",keyVerb:"to quit",note:null},
  {words:["They","hope","to","visit","Japan","next","year"],ru:"Они надеются посетить Японию в следующем году",verbForm:"infinitive",keyVerb:"to visit",note:null},
  {words:["She","refused","to","answer","the","question"],ru:"Она отказалась отвечать на вопрос",verbForm:"infinitive",keyVerb:"to answer",note:null},
  {words:["We","agreed","to","meet","at","noon"],ru:"Мы договорились встретиться в полдень",verbForm:"infinitive",keyVerb:"to meet",note:null},
  {words:["He","plans","to","start","a","business"],ru:"Он планирует открыть бизнес",verbForm:"infinitive",keyVerb:"to start",note:null},
  {words:["She","managed","to","solve","the","problem"],ru:"Ей удалось решить проблему",verbForm:"infinitive",keyVerb:"to solve",note:null},
  {words:["I","failed","to","understand","his","explanation"],ru:"Я не смог понять его объяснение",verbForm:"infinitive",keyVerb:"to understand",note:null},
  {words:["They","couldn't","afford","to","buy","a","new","car"],ru:"Они не могли позволить себе купить новую машину",verbForm:"infinitive",keyVerb:"to buy",note:null},
  // продолжить до ~100 предложений
];
```

**Промпт для генерации:** Глаголы: `want, need, decide, hope, refuse, agree, plan, manage, fail, afford, offer, promise, expect, seem, pretend, learn, choose`.

**Step 2: Commit**

```bash
git add gerund-infinitive-bare-infinitive/infinitive-only.html
git commit -m "feat: add infinitive-only sentence data (~100 sentences)"
```

---

## Task 6: Данные — bare-infinitive.html

**Files:**
- Create: `gerund-infinitive-bare-infinitive/bare-infinitive.html`

**Step 1: Создать файл с данными**

```js
const DATA_KEY = 'bareInfinitive';
const sentences = [
  {words:["She","made","him","apologise"],ru:"Она заставила его извиниться",verbForm:"bare",keyVerb:"apologise",note:null},
  {words:["Let","me","help","you","with","that"],ru:"Позволь мне помочь тебе с этим",verbForm:"bare",keyVerb:"help",note:null},
  {words:["I'll","have","the","technician","fix","it"],ru:"Я попрошу техника починить это",verbForm:"bare",keyVerb:"fix",note:null},
  {words:["She","heard","him","leave","the","room"],ru:"Она слышала, как он вышел из комнаты",verbForm:"bare",keyVerb:"leave",note:null},
  {words:["We","watched","the","children","play","in","the","park"],ru:"Мы наблюдали, как дети играют в парке",verbForm:"bare",keyVerb:"play",note:null},
  {words:["He","felt","his","heart","beat","faster"],ru:"Он почувствовал, как его сердце забилось быстрее",verbForm:"bare",keyVerb:"beat",note:null},
  {words:["Can","you","help","me","carry","these","bags?"],ru:"Ты можешь помочь мне донести эти пакеты?",verbForm:"bare",keyVerb:"carry",note:null},
  {words:["She","saw","him","cross","the","street"],ru:"Она видела, как он переходил улицу",verbForm:"bare",keyVerb:"cross",note:null},
  {words:["Don't","let","fear","stop","you"],ru:"Не позволяй страху останавливать тебя",verbForm:"bare",keyVerb:"stop",note:null},
  {words:["They","made","the","students","rewrite","the","essay"],ru:"Они заставили студентов переписать эссе",verbForm:"bare",keyVerb:"rewrite",note:null},
  // продолжить до ~100 предложений
];
```

**Промпт для генерации:** Глаголы: `make, let, have (causative), help, see, hear, feel, watch, notice, observe`.

**Step 2: Commit**

```bash
git add gerund-infinitive-bare-infinitive/bare-infinitive.html
git commit -m "feat: add bare-infinitive sentence data (~100 sentences)"
```

---

## Task 7: Данные — both-forms.html

**Files:**
- Create: `gerund-infinitive-bare-infinitive/both-forms.html`

**Step 1: Создать файл с данными (пары противопоставлений)**

```js
const DATA_KEY = 'bothForms';
const sentences = [
  // STOP
  {words:["I","stopped","smoking","last","year"],ru:"Я бросил курить в прошлом году",verbForm:"gerund",keyVerb:"smoking",note:"stop + gerund = перестать делать"},
  {words:["She","stopped","to","buy","some","water"],ru:"Она остановилась, чтобы купить воды",verbForm:"infinitive",keyVerb:"to buy",note:"stop + infinitive = остановиться ради чего-то"},
  // REMEMBER
  {words:["I","remember","meeting","her","for","the","first","time"],ru:"Я помню, как впервые встретил её",verbForm:"gerund",keyVerb:"meeting",note:"remember + gerund = помнить о том, что уже произошло"},
  {words:["Remember","to","lock","the","door"],ru:"Не забудь закрыть дверь",verbForm:"infinitive",keyVerb:"to lock",note:"remember + infinitive = не забыть сделать в будущем"},
  // FORGET
  {words:["I'll","never","forget","seeing","the","northern","lights"],ru:"Я никогда не забуду, как видел северное сияние",verbForm:"gerund",keyVerb:"seeing",note:"forget + gerund = не забыть уже пережитое"},
  {words:["Don't","forget","to","call","me","tonight"],ru:"Не забудь позвонить мне сегодня вечером",verbForm:"infinitive",keyVerb:"to call",note:"forget + infinitive = не забыть сделать"},
  // TRY
  {words:["Try","adding","a","little","salt","to","the","soup"],ru:"Попробуй добавить немного соли в суп",verbForm:"gerund",keyVerb:"adding",note:"try + gerund = попробовать как эксперимент"},
  {words:["She","tried","to","open","the","window","but","it","was","stuck"],ru:"Она пыталась открыть окно, но оно застряло",verbForm:"infinitive",keyVerb:"to open",note:"try + infinitive = стараться, прилагать усилия"},
  // REGRET
  {words:["I","regret","saying","those","words"],ru:"Я сожалею, что сказал те слова",verbForm:"gerund",keyVerb:"saying",note:"regret + gerund = сожалеть о прошлом"},
  {words:["We","regret","to","inform","you","that","your","application","was","rejected"],ru:"Мы сожалеем, что должны сообщить вам об отказе",verbForm:"infinitive",keyVerb:"to inform",note:"regret + infinitive = с сожалением сообщать (формально)"},
  // GO ON
  {words:["He","went","on","talking","for","another","hour"],ru:"Он продолжал говорить ещё час",verbForm:"gerund",keyVerb:"talking",note:"go on + gerund = продолжать то же самое"},
  {words:["After","the","break,","she","went","on","to","explain","the","next","topic"],ru:"После перерыва она перешла к объяснению следующей темы",verbForm:"infinitive",keyVerb:"to explain",note:"go on + infinitive = перейти к другому действию"},
  // MEAN
  {words:["Being","healthy","means","exercising","regularly"],ru:"Быть здоровым — значит регулярно заниматься",verbForm:"gerund",keyVerb:"exercising",note:"mean + gerund = означать (следствие)"},
  {words:["I","didn't","mean","to","upset","you"],ru:"Я не хотел расстраивать тебя",verbForm:"infinitive",keyVerb:"to upset",note:"mean + infinitive = намереваться"},
  // LIKE (general preference vs specific preference)
  {words:["I","like","swimming","in","the","morning"],ru:"Мне нравится плавать по утрам (вообще).",verbForm:"gerund",keyVerb:"swimming",note:"like + gerund = общее удовольствие от занятия"},
  {words:["I","like","to","check","my","emails","first","thing"],ru:"Мне нравится проверять почту первым делом (привычка).",verbForm:"infinitive",keyVerb:"to check",note:"like + infinitive = привычка, которую считаешь правильной"},
  // продолжить до ~100 предложений с остальными глаголами
];
```

**Промпт для генерации:** Глаголы для пар: `like, love, hate, stop, remember, forget, try, regret, go on, mean, need, begin, start, continue`.

**Step 2: Commit**

```bash
git add gerund-infinitive-bare-infinitive/both-forms.html
git commit -m "feat: add both-forms sentence data with note field"
```

---

## Task 8: Генерация sentences-data.js

**Files:**
- Create: `gerund-infinitive-bare-infinitive/sentences-data.js` (авто)

**Step 1: Запустить скрипт**

```bash
cd gerund-infinitive-bare-infinitive
python3 scripts/gen_sentences_data.py
```

Ожидаемый вывод:
```
gerund-only.html -> gerundOnly: 100 sentences OK
infinitive-only.html -> infinitiveOnly: 100 sentences OK
bare-infinitive.html -> bareInfinitive: 100 sentences OK
both-forms.html -> bothForms: 100 sentences OK

sentences-data.js written: 400 total sentences across 4 keys
```

**Step 2: Валидировать данные**

```bash
python3 scripts/validate_sentences_data.py
```

Ожидаемый вывод:
```
OK: 400 sentences validated across 4 groups
```

Если ошибки — исправить данные в соответствующем HTML-файле и повторить Step 1.

**Step 3: Commit**

```bash
git add gerund-infinitive-bare-infinitive/sentences-data.js
git commit -m "feat: generate sentences-data.js (400 sentences)"
```

---

## Task 9: Hub — index.html

**Files:**
- Create: `gerund-infinitive-bare-infinitive/index.html`

**Step 1: Написать failing E2E тест для hub (TDD)**

Создать `tests/e2e/index.spec.js`:

```js
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
```

**Step 2: Запустить тест — убедиться что FAIL**

```bash
cd tests && npx playwright test e2e/index.spec.js
# Expected: FAIL (страница не существует)
```

**Step 3: Создать `index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>Verb Forms</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f0f14; color: #f0f0f0;
      min-height: 100vh; display: flex; flex-direction: column;
      align-items: center; padding: 24px 16px 40px;
    }
    h1 { font-size: 22px; color: #9d9dff; margin-bottom: 6px; text-align: center; }
    .subtitle { font-size: 14px; color: #555; margin-bottom: 28px; text-align: center; }
    .group-card {
      width: 100%; max-width: 480px; background: #1a1a2e;
      border: 1.5px solid #2e2e50; border-radius: 16px;
      padding: 18px 20px; margin-bottom: 14px;
      text-decoration: none; color: inherit;
      display: block; cursor: pointer;
      transition: border-color 0.2s;
    }
    .group-card:hover { border-color: #7b68ee; }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .card-badge { font-size: 11px; color: #7b68ee; background: #1e1e3a; border-radius: 10px; padding: 2px 8px; font-weight: 600; }
    .card-title { font-size: 17px; font-weight: 700; color: #e0e0ff; margin-bottom: 2px; }
    .card-formula { font-size: 12px; color: #9d9dff; font-style: italic; margin-bottom: 10px; }
    .card-desc { font-size: 13px; color: #888; line-height: 1.5; margin-bottom: 12px; }
    .progress-bar-wrap { background: #1e1e2a; border-radius: 6px; height: 6px; }
    .progress-bar { height: 6px; background: #7b68ee; border-radius: 6px; transition: width 0.4s ease; }
    .progress-count { font-size: 12px; color: #555; margin-top: 5px; }
  </style>
</head>
<body>
  <h1>Verb Forms</h1>
  <p class="subtitle">Герундий, инфинитив и bare infinitive</p>

  <a href="gerund-only.html" class="group-card" id="card-gerundOnly">
    <div class="card-header">
      <span class="card-badge">Группа А</span>
    </div>
    <div class="card-title">Gerund Only</div>
    <div class="card-formula">enjoy doing / avoid doing</div>
    <div class="card-desc">Глаголы, требующие только герундия: enjoy, mind, avoid, finish, keep, suggest…</div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="bar-gerundOnly" style="width:0%"></div></div>
    <div class="progress-count" id="count-gerundOnly">0 / 0 изучено</div>
  </a>

  <a href="infinitive-only.html" class="group-card" id="card-infinitiveOnly">
    <div class="card-header">
      <span class="card-badge">Группа Б</span>
    </div>
    <div class="card-title">Infinitive Only</div>
    <div class="card-formula">want to do / decide to do</div>
    <div class="card-desc">Глаголы, требующие инфинитива: want, need, decide, hope, refuse, agree…</div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="bar-infinitiveOnly" style="width:0%"></div></div>
    <div class="progress-count" id="count-infinitiveOnly">0 / 0 изучено</div>
  </a>

  <a href="bare-infinitive.html" class="group-card" id="card-bareInfinitive">
    <div class="card-header">
      <span class="card-badge">Группа В</span>
    </div>
    <div class="card-title">Bare Infinitive</div>
    <div class="card-formula">make him do / let her do</div>
    <div class="card-desc">Глаголы, требующие bare infinitive: make, let, have, help, see, hear…</div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="bar-bareInfinitive" style="width:0%"></div></div>
    <div class="progress-count" id="count-bareInfinitive">0 / 0 изучено</div>
  </a>

  <a href="both-forms.html" class="group-card" id="card-bothForms">
    <div class="card-header">
      <span class="card-badge">Группа Г</span>
    </div>
    <div class="card-title">Both Forms — Different Meaning</div>
    <div class="card-formula">stop doing vs stop to do</div>
    <div class="card-desc">Глаголы с разным значением: stop, remember, forget, try, regret, go on…</div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="bar-bothForms" style="width:0%"></div></div>
    <div class="progress-count" id="count-bothForms">0 / 0 изучено</div>
  </a>

  <a href="mix.html" class="group-card" id="card-mix">
    <div class="card-header">
      <span class="card-badge">Mix</span>
    </div>
    <div class="card-title">Mix — All Forms</div>
    <div class="card-formula">doing / to do / do — ?</div>
    <div class="card-desc">Все четыре группы вперемешку. Угадай форму без подсказки.</div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="bar-mix" style="width:0%"></div></div>
    <div class="progress-count" id="count-mix">0 / 0 изучено</div>
  </a>

  <script src="sentences-data.js"></script>
  <script>
    const GROUPS = [
      { key: 'gerundOnly',       total: null },
      { key: 'infinitiveOnly',   total: null },
      { key: 'bareInfinitive',   total: null },
      { key: 'bothForms',        total: null },
    ];

    function updateProgress() {
      let mixDone = 0, mixTotal = 0;
      GROUPS.forEach(({ key }) => {
        const allSentences = window.sentencesData?.[key] || [];
        const done = JSON.parse(localStorage.getItem(key) || '[]');
        const total = allSentences.length;
        const pct = total ? Math.round(done.length / total * 100) : 0;
        document.getElementById('bar-' + key).style.width = pct + '%';
        document.getElementById('count-' + key).textContent = done.length + ' / ' + total + ' изучено';
        mixDone += done.length;
        mixTotal += total;
      });
      const mixPct = mixTotal ? Math.round(mixDone / mixTotal * 100) : 0;
      document.getElementById('bar-mix').style.width = mixPct + '%';
      document.getElementById('count-mix').textContent = mixDone + ' / ' + mixTotal + ' изучено';
    }

    updateProgress();
  </script>
</body>
</html>
```

**Step 4: Запустить тест — убедиться что PASS**

```bash
cd tests && npx playwright test e2e/index.spec.js
# Expected: 4 passed
```

**Step 5: Commit**

```bash
git add gerund-infinitive-bare-infinitive/index.html gerund-infinitive-bare-infinitive/tests/e2e/index.spec.js
git commit -m "feat: add index.html hub with progress bars"
```

---

## Task 10: Exercise screen — gerund-only.html (полная реализация)

**Files:**
- Modify: `gerund-infinitive-bare-infinitive/gerund-only.html` (добавить CSS + HTML + JS поверх данных из Task 4)

**Step 1: Написать failing тест**

Создать `tests/e2e/exercise.spec.js`:

```js
const { test, expect } = require('@playwright/test');

test('TC-11 Страница загружается, виден Шаг 1 (выбор формы)', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await expect(page.locator('#step1')).toBeVisible();
  await expect(page.locator('#step2')).not.toBeVisible();
});

test('TC-12 Русское предложение отображается в Шаге 1', async ({ page }) => {
  await page.goto('/gerund-only.html');
  const text = await page.locator('#task-ru').textContent();
  expect(text?.trim().length).toBeGreaterThan(5);
});

test('TC-13 Три кнопки выбора формы присутствуют', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await expect(page.locator('.form-btn')).toHaveCount(3);
});

test('TC-14 Правильный выбор формы разблокирует Шаг 2', async ({ page }) => {
  await page.goto('/gerund-only.html');
  // Для gerundOnly правильная форма — gerund, кнопка data-form="gerund"
  await page.locator('.form-btn[data-form="gerund"]').click();
  await expect(page.locator('#step2')).toBeVisible();
});

test('TC-15 Шаг 2 содержит word-bank с чипами', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await page.locator('.form-btn[data-form="gerund"]').click();
  const chips = page.locator('#word-bank .chip');
  await expect(chips).not.toHaveCount(0);
});
```

**Step 2: Запустить тест — убедиться что FAIL**

```bash
cd tests && npx playwright test e2e/exercise.spec.js
# Expected: FAIL
```

**Step 3: Реализовать полный `gerund-only.html`**

Структура HTML (CSS берётся из `english-conditionals/0.html` + новые стили для Шага 1):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>Gerund Only</title>
  <style>
    /* --- Базовый reset + тёмная тема (идентично 0.html из english-conditionals) --- */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f0f14; color: #f0f0f0;
      min-height: 100vh; display: flex; flex-direction: column;
      align-items: center; padding: 14px 16px 40px;
    }
    .top-bar { width: 100%; max-width: 480px; display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 10px; margin-bottom: 12px; }
    .top-bar h1 { font-size: 15px; color: #666; text-transform: uppercase; letter-spacing: 1.5px; text-align: center; }
    .btn-back { background: none; border: 1.5px solid #3d3d5c; color: #9d9dff; border-radius: 20px; padding: 8px 14px; font-size: 15px; cursor: pointer; text-decoration: none; line-height: 1; -webkit-tap-highlight-color: transparent; white-space: nowrap; }
    .btn-rule { background: none; border: 1.5px solid #3d3d5c; color: #9d9dff; border-radius: 20px; padding: 8px 14px; font-size: 15px; cursor: pointer; -webkit-tap-highlight-color: transparent; white-space: nowrap; }
    .progress-bar-wrap { width: 100%; max-width: 480px; background: #1e1e2a; border-radius: 6px; height: 6px; margin-bottom: 6px; }
    .progress-bar { height: 6px; background: #7b68ee; border-radius: 6px; transition: width 0.4s ease; }
    .progress-info { width: 100%; max-width: 480px; font-size: 14px; color: #555; margin-bottom: 14px; }
    .task-card { width: 100%; max-width: 480px; background: #1a1a2e; border: 1.5px solid #2e2e50; border-radius: 14px; padding: 18px 20px; margin-bottom: 14px; }
    .task-label { font-size: 12px; color: #555; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
    .task-ru { font-size: 22px; color: #e0e0ff; line-height: 1.5; font-weight: 500; }
    /* --- Шаг 1: кнопки выбора формы --- */
    .form-choices { width: 100%; max-width: 480px; display: flex; gap: 10px; margin-bottom: 16px; }
    .form-btn {
      flex: 1; padding: 18px 8px; font-size: 18px; font-weight: 700;
      border: 1.5px solid #3d3d5c; border-radius: 14px;
      background: #1a1a2e; color: #d0d0f0; cursor: pointer;
      transition: background 0.15s, border-color 0.15s, transform 0.1s;
      -webkit-tap-highlight-color: transparent;
    }
    .form-btn:active { transform: scale(0.97); }
    .form-btn.correct { border-color: #4caf82; background: #1a2e22; color: #4caf82; }
    .form-btn.wrong   { border-color: #e05c5c; background: #2e1a1a; color: #e05c5c; }
    /* --- Шаг 2: chip-механика (идентично 0.html) --- */
    .sentence-area { width: 100%; max-width: 480px; min-height: 70px; background: #1a1a24; border: 2px solid #2e2e44; border-radius: 14px; padding: 12px 14px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; transition: border-color 0.3s; }
    .sentence-area.correct { border-color: #4caf82; }
    .sentence-area.wrong   { border-color: #e05c5c; }
    .placeholder { color: #444; font-size: 16px; font-style: italic; }
    .chip { background: #2a2a3e; border: 1.5px solid #3d3d5c; color: #d0d0f0; border-radius: 22px; padding: 11px 18px; font-size: 19px; cursor: pointer; user-select: none; transition: background 0.15s, transform 0.1s; -webkit-tap-highlight-color: transparent; }
    .chip:active { transform: scale(0.95); }
    .chip.in-answer { background: #35355a; border-color: #7b68ee; color: #c8c8ff; }
    .bank-label { font-size: 12px; color: #555; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; align-self: flex-start; max-width: 480px; width: 100%; }
    .word-bank { width: 100%; max-width: 480px; display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; min-height: 50px; }
    .btn-row { display: flex; gap: 12px; width: 100%; max-width: 480px; }
    button { border: none; border-radius: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.2s, transform 0.1s; -webkit-tap-highlight-color: transparent; }
    button:active { transform: scale(0.97); }
    .btn-row button { flex: 1; padding: 20px; font-size: 20px; }
    #btn-check { background: #7b68ee; color: #fff; }
    #btn-skip  { background: #1e1e2a; color: #777; border: 1.5px solid #2e2e44; flex: 0 0 auto; padding: 20px 24px; }
    .feedback { margin-top: 14px; width: 100%; max-width: 480px; font-size: 17px; line-height: 1.6; min-height: 50px; }
    .feedback .correct-label { color: #4caf82; font-weight: 700; }
    .feedback .wrong-label   { color: #e05c5c; font-weight: 700; }
    .feedback .answer        { color: #9d9dff; margin-top: 4px; }
    .note-box { margin-top: 10px; background: #1e1e3a; border-left: 3px solid #7b68ee; padding: 10px 14px; border-radius: 6px; font-size: 14px; color: #c8c8ff; display: none; }
    .finish { display: none; flex-direction: column; align-items: center; text-align: center; gap: 16px; margin-top: 40px; }
    .finish.show { display: flex; }
    .finish h2 { font-size: 30px; color: #7b68ee; }
    .finish button { max-width: 260px; background: #7b68ee; color: #fff; font-size: 18px; padding: 18px; }
    /* Modal */
    .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
    .modal-overlay.show { display: flex; }
    .modal { background: #1a1a2e; border: 1.5px solid #3d3d5c; border-radius: 18px; padding: 24px 22px; max-width: 460px; width: 100%; max-height: 85vh; overflow-y: auto; }
    .modal h2 { font-size: 18px; color: #9d9dff; margin-bottom: 16px; }
    .modal p { font-size: 14px; color: #aaa; line-height: 1.7; margin-bottom: 10px; }
    .modal .example { background: #12122a; border-left: 3px solid #7b68ee; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; font-size: 14px; color: #d0d0f0; line-height: 1.6; }
    .modal .example span { display: block; color: #777; font-size: 13px; margin-top: 2px; font-style: italic; }
    .modal-close { margin-top: 20px; width: 100%; background: #7b68ee; color: #fff; border: none; padding: 14px; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; }
  </style>
</head>
<body>

<div class="top-bar">
  <a href="index.html" class="btn-back">‹ Назад</a>
  <h1>Gerund Only</h1>
  <button class="btn-rule" onclick="showRule()">📖 Правило</button>
</div>
<div class="progress-bar-wrap">
  <div class="progress-bar" id="progress-bar" style="width:0%"></div>
</div>
<div class="progress-info" id="progress-info">загрузка…</div>

<!-- ШАГ 1: Выбор формы -->
<div id="step1">
  <div class="task-card">
    <div class="task-label">Какая форма глагола?</div>
    <div class="task-ru" id="task-ru">…</div>
  </div>
  <div class="form-choices">
    <button class="form-btn" data-form="gerund"     onclick="chooseForm('gerund')">doing</button>
    <button class="form-btn" data-form="infinitive" onclick="chooseForm('infinitive')">to do</button>
    <button class="form-btn" data-form="bare"       onclick="chooseForm('bare')">do</button>
  </div>
</div>

<!-- ШАГ 2: Составление предложения -->
<div id="step2" style="display:none">
  <div id="game">
    <div class="task-card">
      <div class="task-label">Переведи на английский</div>
      <div class="task-ru" id="task-ru-2">…</div>
    </div>
    <div class="sentence-area" id="sentence-area">
      <span class="placeholder" id="placeholder">Tap words to build the sentence</span>
    </div>
    <div class="bank-label">Слова</div>
    <div class="word-bank" id="word-bank"></div>
    <div class="btn-row">
      <button id="btn-skip"  onclick="skip()">Skip</button>
      <button id="btn-check" onclick="check()">Check ✓</button>
    </div>
    <div class="feedback" id="feedback">
      <div class="note-box" id="note-box"></div>
    </div>
  </div>
</div>

<div class="finish" id="finish">
  <h2>🎉 Готово!</h2>
  <p id="final-score"></p>
  <button onclick="restart()">Продолжить</button>
  <button onclick="resetProgress()" style="background:#1e1e2a;color:#777;border:1.5px solid #2e2e44;margin-top:4px;">Сначала</button>
</div>

<!-- Modal: Правило -->
<div class="modal-overlay" id="modal">
  <div class="modal">
    <h2>Gerund Only — Правило</h2>
    <p>Следующие глаголы всегда требуют <strong style="color:#c8c8ff">герундия</strong> (doing):</p>
    <div class="example">enjoy, mind, avoid, finish, keep, consider, suggest, risk, practise, deny, miss, fancy, can't help, can't stand, it's worth</div>
    <div class="example">I enjoy <em style="color:#9d9dff">swimming</em>. She avoids <em style="color:#9d9dff">eating</em> late.</div>
    <button class="modal-close" onclick="hideRule()">Понятно ✓</button>
  </div>
</div>

<script src="sentences-data.js"></script>
<script>
const DATA_KEY = 'gerundOnly';
/* --- Данные --- */
const sentences = window.sentencesData[DATA_KEY];

/* --- Состояние --- */
let done = JSON.parse(localStorage.getItem(DATA_KEY) || '[]');
let queue = [];
let current = null;
let formChosen = false;

function buildQueue() {
  const all = sentences.map((_, i) => i);
  const notDone = all.filter(i => !done.includes(i));
  queue = notDone.length ? shuffle([...notDone]) : shuffle([...all]);
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function updateProgressBar() {
  const pct = sentences.length ? Math.round(done.length / sentences.length * 100) : 0;
  document.getElementById('progress-bar').style.width = pct + '%';
  document.getElementById('progress-info').textContent =
    done.length + ' / ' + sentences.length + ' изучено';
}

/* --- Шаг 1: выбор формы --- */
function loadQuestion() {
  if (!queue.length) buildQueue();
  const idx = queue.shift();
  current = { ...sentences[idx], idx };
  formChosen = false;

  // Reset step1 UI
  document.getElementById('step1').style.display = '';
  document.getElementById('step2').style.display = 'none';
  document.querySelectorAll('.form-btn').forEach(btn => {
    btn.classList.remove('correct', 'wrong');
    btn.disabled = false;
  });
  document.getElementById('task-ru').textContent = current.ru;
}

function chooseForm(form) {
  if (formChosen) return;
  const btns = document.querySelectorAll('.form-btn');
  btns.forEach(btn => btn.disabled = true);

  if (form === current.verbForm) {
    formChosen = true;
    btns.forEach(btn => {
      if (btn.dataset.form === form) btn.classList.add('correct');
    });
    setTimeout(goToStep2, 600);
  } else {
    btns.forEach(btn => {
      if (btn.dataset.form === form) btn.classList.add('wrong');
      if (btn.dataset.form === current.verbForm) btn.classList.add('correct');
    });
    // Re-enable correct button to force user to click it
    btns.forEach(btn => {
      if (btn.dataset.form === current.verbForm) btn.disabled = false;
    });
  }
}

/* --- Шаг 2: chip-механика --- */
function goToStep2() {
  document.getElementById('step1').style.display = 'none';
  document.getElementById('step2').style.display = '';
  document.getElementById('task-ru-2').textContent = current.ru;
  document.getElementById('feedback').innerHTML = '<div class="note-box" id="note-box"></div>';
  document.getElementById('sentence-area').className = 'sentence-area';
  document.getElementById('sentence-area').innerHTML =
    '<span class="placeholder" id="placeholder">Tap words to build the sentence</span>';
  renderBank(shuffle([...current.words]));
  document.getElementById('btn-check').textContent = 'Check ✓';
}

function renderBank(words) {
  const bank = document.getElementById('word-bank');
  bank.innerHTML = '';
  words.forEach(word => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.textContent = word;
    chip.onclick = () => moveToAnswer(chip);
    bank.appendChild(chip);
  });
}

function moveToAnswer(chip) {
  chip.classList.add('in-answer');
  const area = document.getElementById('sentence-area');
  const placeholder = document.getElementById('placeholder');
  if (placeholder) placeholder.remove();
  area.appendChild(chip);
  chip.onclick = () => moveToBank(chip);
}

function moveToBank(chip) {
  chip.classList.remove('in-answer');
  document.getElementById('word-bank').appendChild(chip);
  chip.onclick = () => moveToAnswer(chip);
  const area = document.getElementById('sentence-area');
  if (!area.querySelector('.chip')) {
    const ph = document.createElement('span');
    ph.className = 'placeholder'; ph.id = 'placeholder';
    ph.textContent = 'Tap words to build the sentence';
    area.appendChild(ph);
  }
}

function getAnswer() {
  return [...document.querySelectorAll('#sentence-area .chip')].map(c => c.textContent);
}

function check() {
  const answer = getAnswer();
  if (!answer.length) return;
  const area = document.getElementById('sentence-area');
  const fb = document.getElementById('feedback');
  const noteBox = document.getElementById('note-box');

  if (JSON.stringify(answer) === JSON.stringify(current.words)) {
    area.classList.add('correct');
    fb.innerHTML = '<span class="correct-label">✓ Правильно!</span>';
    if (current.note) {
      const nb = document.createElement('div');
      nb.className = 'note-box';
      nb.id = 'note-box';
      nb.style.display = 'block';
      nb.textContent = '💡 ' + current.note;
      fb.appendChild(nb);
    }
    if (!done.includes(current.idx)) {
      done.push(current.idx);
      localStorage.setItem(DATA_KEY, JSON.stringify(done));
    }
    updateProgressBar();
    document.getElementById('btn-check').textContent = 'Далее →';
    document.getElementById('btn-check').onclick = nextQuestion;
    if (done.length === sentences.length) setTimeout(showFinish, 800);
  } else {
    area.classList.add('wrong');
    fb.innerHTML = '<span class="wrong-label">✗ Неверно.</span><div class="answer">' + current.words.join(' ') + '</div>';
  }
}

function skip() {
  nextQuestion();
}

function nextQuestion() {
  document.getElementById('btn-check').textContent = 'Check ✓';
  document.getElementById('btn-check').onclick = check;
  loadQuestion();
}

function showFinish() {
  document.getElementById('step1').style.display = 'none';
  document.getElementById('step2').style.display = 'none';
  const finish = document.getElementById('finish');
  finish.classList.add('show');
  document.getElementById('final-score').textContent =
    'Все ' + sentences.length + ' предложений пройдено!';
}

function restart() {
  document.getElementById('finish').classList.remove('show');
  buildQueue();
  loadQuestion();
}

function resetProgress() {
  done = [];
  localStorage.removeItem(DATA_KEY);
  updateProgressBar();
  restart();
}

function showRule() { document.getElementById('modal').classList.add('show'); }
function hideRule() { document.getElementById('modal').classList.remove('show'); }

/* --- Init --- */
buildQueue();
loadQuestion();
updateProgressBar();
</script>

<!-- ===== ДАННЫЕ (Task 4) ===== -->
<!-- Вставить const sentences = [...] из Task 4 ПОСЛЕ основного <script> -->
<!-- НО gen_sentences_data.py читает sentences из этого файла,           -->
<!-- поэтому данные должны быть в отдельном <script> НИЖЕ:              -->
</body>
</html>
```

**Важно — порядок `<script>` тегов:**
1. `<script src="sentences-data.js">` — загружает `window.sentencesData`
2. Основной `<script>` — использует `window.sentencesData[DATA_KEY]`
3. `const sentences` из Task 4 — нужен только для `gen_sentences_data.py`, встроен в HTML до секции данных

Чтобы совместить оба требования, структура данных:

```html
<!-- В конце body, после основного script: -->
<script>
// Source data for gen_sentences_data.py (do not remove this comment)
const sentences = [ ...данные из Task 4... ];
</script>
```

И в основном JS: `const sentences = window.sentencesData[DATA_KEY];` — всегда берём из `sentences-data.js`.

**Step 4: Запустить тест — убедиться что PASS**

```bash
cd tests && npx playwright test e2e/exercise.spec.js
# Expected: 5 passed
```

**Step 5: Commit**

```bash
git add gerund-infinitive-bare-infinitive/gerund-only.html gerund-infinitive-bare-infinitive/tests/e2e/exercise.spec.js
git commit -m "feat: implement gerund-only.html with 2-step exercise mechanic"
```

---

## Task 11: Exercise screens — infinitive-only, bare-infinitive, both-forms

**Files:**
- Create: `gerund-infinitive-bare-infinitive/infinitive-only.html`
- Create: `gerund-infinitive-bare-infinitive/bare-infinitive.html`
- Create: `gerund-infinitive-bare-infinitive/both-forms.html`

**Step 1: Создать три файла по шаблону `gerund-only.html`**

Каждый файл: скопировать `gerund-only.html`, изменить:
- `const DATA_KEY = 'infinitiveOnly'` / `'bareInfinitive'` / `'bothForms'`
- `<title>` и `<h1>`: "Infinitive Only" / "Bare Infinitive" / "Both Forms"
- Текст в модальном окне "Правило" (глаголы своей группы)
- `const sentences` — данные из Task 5 / 6 / 7

Для `both-forms.html` — модальное окно объясняет разницу значений при каждой форме.

**Step 2: Запустить тест exercise.spec.js для каждого файла**

```bash
cd tests && npx playwright test e2e/exercise.spec.js --grep "TC-1[1-5]"
# Если тесты ходят на /gerund-only.html — добавить аналогичные тесты для других файлов
```

**Step 3: Commit**

```bash
git add gerund-infinitive-bare-infinitive/infinitive-only.html \
        gerund-infinitive-bare-infinitive/bare-infinitive.html \
        gerund-infinitive-bare-infinitive/both-forms.html
git commit -m "feat: add infinitive-only, bare-infinitive, both-forms exercise screens"
```

---

## Task 12: Mix screen — mix.html

**Files:**
- Create: `gerund-infinitive-bare-infinitive/mix.html`

**Step 1: Написать failing тест**

Создать `tests/e2e/mix.spec.js`:

```js
const { test, expect } = require('@playwright/test');

test('TC-31 Mix загружается', async ({ page }) => {
  await page.goto('/mix.html');
  await expect(page.locator('#step1')).toBeVisible();
});

test('TC-32 Mix имеет Counter который показывает суммарный прогресс', async ({ page }) => {
  await page.goto('/mix.html');
  const info = await page.locator('#progress-info').textContent();
  // Должно содержать число (общее количество предложений)
  expect(info).toMatch(/\d+/);
});
```

**Step 2: Запустить тест — убедиться что FAIL**

```bash
cd tests && npx playwright test e2e/mix.spec.js
```

**Step 3: Создать `mix.html`**

Скопировать `gerund-only.html`. Изменить логику загрузки данных:

```js
// В mix.html вместо одного DATA_KEY — объединяем все группы
const ALL_KEYS = ['gerundOnly', 'infinitiveOnly', 'bareInfinitive', 'bothForms'];

// Строим плоский массив со ссылкой на исходный ключ
const allSentences = [];
ALL_KEYS.forEach(key => {
  (window.sentencesData[key] || []).forEach((s, i) => {
    allSentences.push({ ...s, _key: key, _idx: i });
  });
});

// Прогресс: индекс в allSentences (не в локальных массивах)
const STORAGE_KEY = 'verbFormsMix';
```

Прогресс-бар mix показывает суммарный прогресс по всем 4 группам из `localStorage`.

**Step 4: Запустить тест — убедиться что PASS**

```bash
cd tests && npx playwright test e2e/mix.spec.js
# Expected: 2 passed
```

**Step 5: Commit**

```bash
git add gerund-infinitive-bare-infinitive/mix.html gerund-infinitive-bare-infinitive/tests/e2e/mix.spec.js
git commit -m "feat: add mix.html combining all 4 verb form groups"
```

---

## Task 13: E2E тесты — валидация и прогресс

**Files:**
- Create: `gerund-infinitive-bare-infinitive/tests/e2e/validation.spec.js`
- Create: `gerund-infinitive-bare-infinitive/tests/e2e/progress.spec.js`
- Create: `gerund-infinitive-bare-infinitive/tests/e2e/note.spec.js`

**Step 1: Написать `validation.spec.js`**

```js
const { test, expect } = require('@playwright/test');

test('TC-21 Неверный выбор формы показывает ошибку (кнопка краснеет)', async ({ page }) => {
  await page.goto('/gerund-only.html');
  // Для gerundOnly неверная форма — infinitive
  await page.locator('.form-btn[data-form="infinitive"]').click();
  await expect(page.locator('.form-btn[data-form="infinitive"]')).toHaveClass(/wrong/);
});

test('TC-22 После неверного выбора правильная кнопка зеленеет и остаётся активной', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await page.locator('.form-btn[data-form="infinitive"]').click();
  await expect(page.locator('.form-btn[data-form="gerund"]')).toHaveClass(/correct/);
  // Правильная кнопка не задизейблена
  await expect(page.locator('.form-btn[data-form="gerund"]')).not.toBeDisabled();
});

test('TC-23 После неверного выбора Шаг 2 НЕ отображается', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await page.locator('.form-btn[data-form="infinitive"]').click();
  await expect(page.locator('#step2')).not.toBeVisible();
});

test('TC-24 После нажатия правильной кнопки (после ошибки) Шаг 2 открывается', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await page.locator('.form-btn[data-form="infinitive"]').click();
  await page.locator('.form-btn[data-form="gerund"]').click();
  await expect(page.locator('#step2')).toBeVisible();
});
```

**Step 2: Написать `progress.spec.js`**

```js
const { test, expect } = require('@playwright/test');

test('TC-41 Прогресс сохраняется в localStorage после правильного ответа', async ({ page }) => {
  await page.goto('/gerund-only.html');
  // Шаг 1 — выбрать правильную форму
  await page.locator('.form-btn[data-form="gerund"]').click();
  await page.waitForSelector('#step2:visible');
  // Шаг 2 — собрать все чипы и проверить
  const chips = page.locator('#word-bank .chip');
  const count = await chips.count();
  for (let i = 0; i < count; i++) {
    await page.locator('#word-bank .chip').first().click();
  }
  await page.locator('#btn-check').click();
  // Проверяем localStorage
  const stored = await page.evaluate(() => localStorage.getItem('gerundOnly'));
  expect(stored).not.toBeNull();
  const arr = JSON.parse(stored);
  expect(arr.length).toBeGreaterThan(0);
});

test('TC-42 Прогресс-бар обновляется после правильного ответа', async ({ page }) => {
  await page.goto('/gerund-only.html');
  const barBefore = await page.locator('#progress-bar').getAttribute('style');
  await page.locator('.form-btn[data-form="gerund"]').click();
  await page.waitForSelector('#step2:visible');
  const count = await page.locator('#word-bank .chip').count();
  for (let i = 0; i < count; i++) {
    await page.locator('#word-bank .chip').first().click();
  }
  await page.locator('#btn-check').click();
  // Нажать Далее
  await page.locator('#btn-check').click();
  const barAfter = await page.locator('#progress-bar').getAttribute('style');
  expect(barAfter).not.toBe(barBefore);
});

test('TC-43 Прогресс сохраняется после reload страницы', async ({ page }) => {
  await page.goto('/gerund-only.html');
  // Выполнить одно упражнение (шаги 1+2)
  await page.locator('.form-btn[data-form="gerund"]').click();
  await page.waitForSelector('#step2:visible');
  const count = await page.locator('#word-bank .chip').count();
  for (let i = 0; i < count; i++) {
    await page.locator('#word-bank .chip').first().click();
  }
  await page.locator('#btn-check').click();
  // Reload
  await page.reload();
  // localStorage должен содержать запись
  const stored = await page.evaluate(() => localStorage.getItem('gerundOnly'));
  expect(stored).not.toBeNull();
  const arr = JSON.parse(stored);
  expect(arr.length).toBeGreaterThan(0);
});
```

**Step 3: Написать `note.spec.js`**

```js
const { test, expect } = require('@playwright/test');

test('TC-51 Note НЕ отображается для gerundOnly после правильного ответа', async ({ page }) => {
  await page.goto('/gerund-only.html');
  await page.locator('.form-btn[data-form="gerund"]').click();
  await page.waitForSelector('#step2:visible');
  const count = await page.locator('#word-bank .chip').count();
  for (let i = 0; i < count; i++) {
    await page.locator('#word-bank .chip').first().click();
  }
  await page.locator('#btn-check').click();
  // note-box не должен быть виден (null note)
  await expect(page.locator('#note-box')).not.toBeVisible();
});

test('TC-52 Note отображается для bothForms после правильного ответа', async ({ page }) => {
  await page.goto('/both-forms.html');
  // Первое предложение bothForms имеет note
  const verbForm = await page.evaluate(() => window.sentencesData.bothForms[0].verbForm);
  await page.locator(`.form-btn[data-form="${verbForm}"]`).click();
  await page.waitForSelector('#step2:visible');
  const count = await page.locator('#word-bank .chip').count();
  for (let i = 0; i < count; i++) {
    await page.locator('#word-bank .chip').first().click();
  }
  await page.locator('#btn-check').click();
  // note-box должен быть виден
  await expect(page.locator('#note-box')).toBeVisible();
});
```

**Step 4: Запустить все тесты**

```bash
cd tests && npx playwright test
# Expected: все тесты проходят
```

**Step 5: Commit**

```bash
git add gerund-infinitive-bare-infinitive/tests/e2e/
git commit -m "test: add validation, progress, note E2E tests"
```

---

## Task 14: Рефакторинг — выделение shared JS

**Files:**
- Create: `gerund-infinitive-bare-infinitive/js/chips.js`
- Create: `gerund-infinitive-bare-infinitive/js/progress.js`
- Create: `gerund-infinitive-bare-infinitive/js/exercise.js`
- Modify: `gerund-infinitive-bare-infinitive/gerund-only.html`
- Modify: `gerund-infinitive-bare-infinitive/infinitive-only.html`
- Modify: `gerund-infinitive-bare-infinitive/bare-infinitive.html`
- Modify: `gerund-infinitive-bare-infinitive/both-forms.html`
- Modify: `gerund-infinitive-bare-infinitive/mix.html`

**Step 1: Запустить все тесты — зафиксировать baseline (все должны PASS)**

```bash
cd tests && npx playwright test
# Все тесты должны пройти перед рефакторингом
```

**Step 2: Создать `js/progress.js`**

```js
// js/progress.js — save/load localStorage for exercise progress
window.ProgressManager = {
  load(key) {
    return JSON.parse(localStorage.getItem(key) || '[]');
  },
  save(key, arr) {
    localStorage.setItem(key, JSON.stringify(arr));
  },
  remove(key) {
    localStorage.removeItem(key);
  },
  updateBar(key, total) {
    const done = this.load(key);
    const pct = total ? Math.round(done.length / total * 100) : 0;
    const bar = document.getElementById('progress-bar');
    const info = document.getElementById('progress-info');
    if (bar) bar.style.width = pct + '%';
    if (info) info.textContent = done.length + ' / ' + total + ' изучено';
    return done;
  }
};
```

**Step 3: Создать `js/chips.js`**

```js
// js/chips.js — chip mechanic (word bank ↔ sentence area)
window.ChipsManager = {
  render(words, bankEl) {
    bankEl.innerHTML = '';
    words.forEach(word => {
      const chip = document.createElement('button');
      chip.className = 'chip';
      chip.textContent = word;
      chip.onclick = () => this.moveToAnswer(chip);
      bankEl.appendChild(chip);
    });
  },
  moveToAnswer(chip) {
    chip.classList.add('in-answer');
    const area = document.getElementById('sentence-area');
    const placeholder = document.getElementById('placeholder');
    if (placeholder) placeholder.remove();
    area.appendChild(chip);
    chip.onclick = () => this.moveToBank(chip);
  },
  moveToBank(chip) {
    chip.classList.remove('in-answer');
    document.getElementById('word-bank').appendChild(chip);
    chip.onclick = () => this.moveToAnswer(chip);
    const area = document.getElementById('sentence-area');
    if (!area.querySelector('.chip')) {
      const ph = document.createElement('span');
      ph.className = 'placeholder'; ph.id = 'placeholder';
      ph.textContent = 'Tap words to build the sentence';
      area.appendChild(ph);
    }
  },
  getAnswer() {
    return [...document.querySelectorAll('#sentence-area .chip')].map(c => c.textContent);
  },
  shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
};
```

**Step 4: Создать `js/exercise.js`**

```js
// js/exercise.js — 2-step exercise logic (form choice + chips)
// Expects: DATA_KEY, sentences to be defined externally
// Expects: ProgressManager and ChipsManager to be loaded

window.ExerciseController = {
  done: [],
  queue: [],
  current: null,

  init(dataKey, sentences) {
    this.dataKey = dataKey;
    this.sentences = sentences;
    this.done = ProgressManager.load(dataKey);
    this.buildQueue();
    this.loadQuestion();
    ProgressManager.updateBar(dataKey, sentences.length);

    document.getElementById('btn-check').onclick = () => this.check();
    document.getElementById('btn-skip').onclick  = () => this.skip();
  },

  buildQueue() {
    const all = this.sentences.map((_, i) => i);
    const notDone = all.filter(i => !this.done.includes(i));
    this.queue = ChipsManager.shuffle(notDone.length ? notDone : all);
  },

  loadQuestion() {
    if (!this.queue.length) this.buildQueue();
    const idx = this.queue.shift();
    this.current = { ...this.sentences[idx], idx };
    this.formChosen = false;

    document.getElementById('step1').style.display = '';
    document.getElementById('step2').style.display = 'none';
    document.querySelectorAll('.form-btn').forEach(btn => {
      btn.classList.remove('correct', 'wrong');
      btn.disabled = false;
    });
    document.getElementById('task-ru').textContent = this.current.ru;
  },

  chooseForm(form) {
    if (this.formChosen) return;
    const btns = document.querySelectorAll('.form-btn');
    btns.forEach(btn => btn.disabled = true);

    if (form === this.current.verbForm) {
      this.formChosen = true;
      btns.forEach(btn => { if (btn.dataset.form === form) btn.classList.add('correct'); });
      setTimeout(() => this.goToStep2(), 600);
    } else {
      btns.forEach(btn => {
        if (btn.dataset.form === form) btn.classList.add('wrong');
        if (btn.dataset.form === this.current.verbForm) {
          btn.classList.add('correct');
          btn.disabled = false;
        }
      });
    }
  },

  goToStep2() {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = '';
    document.getElementById('task-ru-2').textContent = this.current.ru;
    document.getElementById('feedback').innerHTML = '<div class="note-box" id="note-box"></div>';
    document.getElementById('sentence-area').className = 'sentence-area';
    document.getElementById('sentence-area').innerHTML =
      '<span class="placeholder" id="placeholder">Tap words to build the sentence</span>';
    ChipsManager.render(ChipsManager.shuffle(this.current.words),
                        document.getElementById('word-bank'));
    const checkBtn = document.getElementById('btn-check');
    checkBtn.textContent = 'Check ✓';
    checkBtn.onclick = () => this.check();
  },

  check() {
    const answer = ChipsManager.getAnswer();
    if (!answer.length) return;
    const area = document.getElementById('sentence-area');
    const fb = document.getElementById('feedback');

    if (JSON.stringify(answer) === JSON.stringify(this.current.words)) {
      area.classList.add('correct');
      fb.innerHTML = '<span class="correct-label">✓ Правильно!</span>';
      if (this.current.note) {
        const nb = document.createElement('div');
        nb.className = 'note-box'; nb.id = 'note-box';
        nb.style.display = 'block';
        nb.textContent = '💡 ' + this.current.note;
        fb.appendChild(nb);
      }
      if (!this.done.includes(this.current.idx)) {
        this.done.push(this.current.idx);
        ProgressManager.save(this.dataKey, this.done);
      }
      ProgressManager.updateBar(this.dataKey, this.sentences.length);
      const checkBtn = document.getElementById('btn-check');
      checkBtn.textContent = 'Далее →';
      checkBtn.onclick = () => this.nextQuestion();
      if (this.done.length === this.sentences.length) setTimeout(() => this.showFinish(), 800);
    } else {
      area.classList.add('wrong');
      fb.innerHTML = '<span class="wrong-label">✗ Неверно.</span><div class="answer">'
        + this.current.words.join(' ') + '</div>';
    }
  },

  skip() { this.nextQuestion(); },

  nextQuestion() {
    const checkBtn = document.getElementById('btn-check');
    checkBtn.textContent = 'Check ✓';
    checkBtn.onclick = () => this.check();
    this.loadQuestion();
  },

  showFinish() {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('finish').classList.add('show');
    document.getElementById('final-score').textContent =
      'Все ' + this.sentences.length + ' предложений пройдено!';
  },
};
```

**Step 5: Обновить все HTML-файлы**

В каждом `gerund-only.html`, `infinitive-only.html`, `bare-infinitive.html`, `both-forms.html`:

1. Заменить инлайн JS на:
```html
<script src="sentences-data.js"></script>
<script src="js/progress.js"></script>
<script src="js/chips.js"></script>
<script src="js/exercise.js"></script>
<script>
  const DATA_KEY = 'gerundOnly'; // изменить для каждого файла
  ExerciseController.init(DATA_KEY, window.sentencesData[DATA_KEY]);

  function chooseForm(form) { ExerciseController.chooseForm(form); }
  function showRule() { document.getElementById('modal').classList.add('show'); }
  function hideRule() { document.getElementById('modal').classList.remove('show'); }
  function resetProgress() {
    ExerciseController.done = [];
    ProgressManager.remove(DATA_KEY);
    ProgressManager.updateBar(DATA_KEY, window.sentencesData[DATA_KEY].length);
    ExerciseController.buildQueue();
    ExerciseController.loadQuestion();
    document.getElementById('finish').classList.remove('show');
  }
  function restart() {
    document.getElementById('finish').classList.remove('show');
    ExerciseController.buildQueue();
    ExerciseController.loadQuestion();
  }
</script>
```

Каждый файл отличается только `const DATA_KEY = '...'`.

**Step 6: Запустить все тесты — убедиться что все PASS**

```bash
cd tests && npx playwright test
# Expected: все тесты pass (рефакторинг не должен ничего сломать)
```

**Step 7: Commit**

```bash
git add gerund-infinitive-bare-infinitive/js/ \
        gerund-infinitive-bare-infinitive/gerund-only.html \
        gerund-infinitive-bare-infinitive/infinitive-only.html \
        gerund-infinitive-bare-infinitive/bare-infinitive.html \
        gerund-infinitive-bare-infinitive/both-forms.html \
        gerund-infinitive-bare-infinitive/mix.html
git commit -m "refactor: extract js/chips.js, progress.js, exercise.js"
```

---

## Task 15: Финальная валидация

**Step 1: Запустить полный тестовый прогон**

```bash
cd gerund-infinitive-bare-infinitive/tests
npx playwright test
```

Ожидаемый результат: все тесты зелёные.

**Step 2: Запустить валидатор данных**

```bash
cd gerund-infinitive-bare-infinitive
python3 scripts/validate_sentences_data.py
# Expected: OK: 400 sentences validated across 4 groups
```

**Step 3: Открыть в браузере и проверить вручную**

```bash
cd gerund-infinitive-bare-infinitive
python3 -m http.server 8082
# Открыть http://localhost:8082/index.html
```

Проверить:
- [ ] Hub показывает 5 карточек
- [ ] Каждая карточка открывает exercise screen
- [ ] Шаг 1 работает (верный/неверный выбор)
- [ ] Шаг 2 работает (чипы, проверка)
- [ ] `note` отображается для `both-forms`
- [ ] Прогресс сохраняется при reload
- [ ] Mix работает

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: gerund-infinitive-bare-infinitive module complete"
```

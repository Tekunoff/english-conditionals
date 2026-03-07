---
applyTo: "**"
---

# UX Rules: Confirmations & Technical Messages

## Language

Always communicate with the user in **Russian**, unless the user writes in another language.

---

## Context Window Management

When the context window is running low (conversation is getting long and complex), proactively suggest to the user:

1. **Notify** the user with this message format:
   > ⚠️ Контекстное окно близко к заполнению. Предлагаю сохранить контекст сессии в файл, чтобы продолжить работу в новой сессии без потери прогресса.

2. **Create a session file** in `.github/sessions/` with a short kebab-case name matching the session topic, e.g. `.github/sessions/gmail-cleaner-setup.md`

3. **The file must contain TWO sections:**

   ### Section 1 — PROMPT
   A ready-to-paste prompt for starting a new chat session. Written as a direct instruction to the assistant, including:
   - What the project is and what was being worked on
   - What was completed
   - What needs to be done next (concrete next steps)
   - Key file paths, commands, decisions made
   - Any known issues or constraints
   
   Example format:
   ```
   ## Продолжение сессии: [название]
   
   Мы работали над [описание]. Вот что уже сделано: [список]. 
   Следующий шаг: [конкретное действие]. Файлы проекта: [пути].
   ```

   ### Section 2 — CONTEXT
   Full structured context of the session:
   - Goals and current state
   - All files created/modified with their purpose
   - Progress summary (completed / pending)
   - Technical details (credentials, configs, commands)
   - Known issues and solutions found

4. **Do not wait** for the context to be fully exhausted — suggest proactively when roughly 70-80% is used.

5. **Sessions folder**: `.github/sessions/` — all session files go here, not in the workspace root.



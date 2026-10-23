# Cogni-Routine

Cogni-Routine is a chat-first, multilingual self-tracking app for daily check-ins and short cognitive activities. It records participant-approved observations, shows descriptive changes over time, and can create a PDF to discuss with a healthcare professional.

This build is a web MVP using FastAPI, SQLite, HTML, CSS, and browser JavaScript. It is not a neurological assessment or a disease-pattern detector. Its activities are product activities, not validated clinical tests. The app does not diagnose, screen for, predict, or rule out a condition.

## Run locally on Windows

Python and pip are required. In PowerShell, from the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GEMINI_API_KEY = "your-key"
# Optional; defaults to gemini-2.5-flash
$env:GEMINI_MODEL = "gemini-2.5-flash"
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. Keep the PowerShell window open while using the app and stop the server with **Ctrl+C**. The local SQLite database is stored at `data/cogni_routine.sqlite3`; set `COGNI_DB_PATH` to change its location. Never paste an API key into the app, commit it, or share it in a presentation. If no Agent provider key is configured, chat and summaries return a clear service-unavailable message; local tracking and PDF generation remain available.

## Account and daily use

1. Choose English, Hindi, or Marathi and create an account. Registration currently requires age 18 or older, a password of at least 10 characters, and consent to store data locally.
2. The optional profile can include interests and participant-entered health context. These fields are stored in the local SQLite database and are not included in Agent prompts.
3. A separate, optional Agent consent controls whether chat text and activity observations can be sent to the configured Agent provider for replies and report reflections. It can be revoked in the app. Revoking it also removes the saved report summary; prior chat and activity records remain until the participant deletes their account data.
4. Start a daily check-in in the chat. The voice button uses the browser's speech-recognition capability when available; depending on the browser, audio may be processed by its speech service. Review the transcribed text before sending and prefer typing for sensitive information. Greeting playback uses the browser's speech synthesis.
5. Optional activities are word recall, category fluency, spatial recall, symbol matching, and visual response. The app stores scores, task type, duration, and aggregate activity metrics—not the participant's typed answers.
6. The report shows the last 30 days of check-in and activity counts, participation streaks, average task scores, and observed variation. A “complete day” is an app-defined day with three distinct activity types; it is not a clinical threshold.
7. **Agent summary** requests an Agent-generated reflection when separate Agent consent is enabled and a key is configured. **Download report PDF** saves a PDF with the descriptive report, participant-entered context, activity entries, and—if generated and still consented—the Agent reflection. Report labels are in English; Hindi or Marathi participant notes are included when the server has a compatible Unicode font installed. The existing print action opens the browser's print dialog.
8. **Delete saved data** permanently removes the account, profile, chat, report summary, and associated activity records from the local database.

The PDF contains participant-entered profile notes because the participant explicitly downloads it for sharing. Check its contents before sending it to anyone. Agent reflections may be incomplete or inaccurate and are not medical advice.

## What the analysis means

The report has transparent, descriptive tracking views:

- **Participation:** check-in days, messages, activity counts, complete days, and streak.
- **Task performance:** recorded result percentages are summarized within each activity. Different activities are not directly comparable.
- **Observed variation:** repeated scores are summarized to show how recorded values varied. Variation alone does not indicate decline or a disorder.
- **Personal reference window:** tracks eligible complete days in the product's early-use window. It is not a validated baseline and produces no clinical alert.

No clinical accuracy, sensitivity, specificity, positive predictive value, or disease detection performance has been established. Scores can vary with language, reading or typing ability, education, vision, hearing, fatigue, device, familiarity, and environment. Category fluency counts distinct entries but does not verify that each is an animal. Do not use this app to decide whether cognition is “normal” or “declining,” or to delay clinical care. New or sudden confusion warrants prompt medical attention.

## Agent data flow

The Agent provider is used for conversational responses and optional report reflections. Only after separate Agent consent, the app may send recent chat messages and recent task observations to the configured provider. It does not send the optional profile fields. The provider key is read by the server and is never sent to the browser. Model availability, quotas, and terms can change, so verify the chosen model and data-handling terms before a presentation or deployment.

This local development setup is not suitable for real patient records or public deployment. Before using sensitive or care-related data in any deployment, obtain appropriate privacy, security, legal, ethics, and clinical review. Configure secure hosting, HTTPS, encrypted backups, retention and deletion policies, and production-grade secret/session management.

## Chat-platform integration

Telegram, WhatsApp, and other chat integrations are not implemented in this build. The fastest next step is a bot that shares a link to this web app, so account consent, activities, and reports remain in one place. A Telegram Mini App can later host visual or timed tasks; a normal chat thread is not a reliable way to control stimuli or measure response timing. For any webhook integration, add signature verification, rate limits, secure identity mapping, secret management, and authorization before exposing participant data. Do not treat a chat-platform user ID as authentication.

## API overview

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — account and session.
- `GET /api/conversations/{participant_id}`, `POST /api/chat` — authenticated chat history and Agent response.
- `GET /api/tasks`, `POST /api/task-results`, `POST /api/activities/attempts` — task bank and the current activity-result routes.
- `POST /api/tasks/attempts` — legacy word-recall result route.
- `GET /api/reports/{participant_id}` — 30-day descriptive report.
- `POST /api/reports/{participant_id}/summary` — consent-required Agent reflection.
- `GET /api/reports/{participant_id}/pdf` — authenticated PDF download.
- `PUT /api/profile`, `PUT /api/consent/gemini` — profile and separate Agent-consent settings. The route name is retained for compatibility.
- `DELETE /api/conversations/{participant_id}` — delete the signed-in participant's account and associated records.

Participant-specific routes require an authenticated session and verify ownership.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
node --check .\app.js
```

Passing software tests verify implementation behavior, not clinical validity or disease-detection accuracy.

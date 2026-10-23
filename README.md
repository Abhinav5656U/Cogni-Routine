# Cogni-Routine

Cogni-Routine is a chat-first, multilingual self-tracking app for daily check-ins and short cognitive activities. It records participant-approved observations, shows descriptive changes over time, and can create a PDF to discuss with a healthcare professional.

This build is a web MVP using FastAPI, SQLite, HTML, CSS, and browser JavaScript. It is not a neurological assessment or a disease-pattern detector. Its activities are product activities, not validated clinical tests. The app does not diagnose, screen for, predict, or rule out a condition.

## Accessibility and display controls

- The header includes **A-** and **A+** controls for a smaller or larger whole-app display. The default remains 100%, and the selected size is saved only in the current browser.
- The navigation menu can be opened with the menu button and closed with **Escape**; focus returns to the menu button.
- Reports expose loading status and a retry action when history cannot be loaded.
- Visible focus outlines, keyboard-operable controls, live status regions, reduced-motion support, and responsive layouts are included in the current web MVP.

## Run locally on Windows

Python and pip are required. In PowerShell, from the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GEMINI_API_KEY = "your-key"
# Optional separate model configuration; both default to gemini-2.5-flash
$env:GEMINI_LLM1_API_KEY = "model-1-key"
$env:GEMINI_LLM1_MODEL = "gemini-2.5-flash"
$env:GEMINI_LLM2_API_KEY = "model-2-key"
$env:GEMINI_LLM2_MODEL = "gemini-2.5-flash"
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. Keep the PowerShell window open while using the app and stop the server with **Ctrl+C**. The local SQLite database is stored at `data/cogni_routine.sqlite3`; set `COGNI_DB_PATH` to change its location. Never paste an API key into the app, commit it, or share it in a presentation. If no Agent provider key is configured, chat and summaries return a clear service-unavailable message; local tracking and PDF generation remain available.

## Container and production readiness

Copy `.env.example` to `.env` locally, then replace demo values through a secret manager before any public deployment. The included Compose file stores SQLite data in a named persistent volume:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
Invoke-WebRequest http://127.0.0.1:8000/readyz
docker compose logs -f cogni-routine
```

Stop it with `docker compose down`; keep the named volume if the local database should remain.

The container exposes:

- `/healthz` for process liveness.
- `/readyz` for a SQLite readiness probe.
- `/api/health` for backward-compatible local checks.

Before a public deployment, use HTTPS, a persistent encrypted database or managed database, encrypted backups, a shared rate limiter, centralized secret storage, log redaction, monitoring, a documented retention/deletion policy, and legal/privacy review. Set `COGNI_COOKIE_SECURE=1` and configure `COGNI_ALLOWED_ORIGINS` to the exact HTTPS origins. Do not enable demo mode or use SQLite test data for real sensitive records.

## Account and daily use

1. Choose English, Hindi, or Marathi and create an account. Registration currently requires age 18 or older, a password of at least 10 characters, and consent to store data locally.
2. The optional profile can include interests and participant-entered health context. These fields are stored in the local SQLite database and are not included in Agent prompts.
3. A separate, optional Agent consent controls whether chat text and activity observations can be sent to the configured Agent provider for replies and report reflections. It can be revoked in the app. Revoking it also removes the saved report summary; prior chat and activity records remain until the participant deletes their account data.
4. Start a daily check-in in the chat. The voice button uses the browser's speech-recognition capability when available; depending on the browser, audio may be processed by its speech service. The server supplies a stable, language-specific practice word for the day and records only whether that word appeared in the recognized transcript plus a neutral capture-quality label (`matched`, `not_matched`, or `unavailable`). This is an input-capture signal, not evidence of a speech disorder. Review the transcribed text before sending and prefer typing for sensitive information. Greeting playback uses the browser's speech synthesis.
5. Optional activities are word recall, category fluency, spatial recall, symbol matching, and visual response. The app stores scores, task type, duration, and aggregate activity metrics—not the participant's typed answers.
6. The report shows the last 30 days of check-in and activity counts, participation streaks, average task scores, and observed variation. A “complete day” is an app-defined day with three distinct activity types; it is not a clinical threshold.
7. **Agent summary** requests an Agent-generated reflection when separate Agent consent is enabled and a key is configured. **Download report PDF** saves the rolling 30-day descriptive report; **Download today** saves a date-specific PDF. Report labels are in English; Hindi or Marathi participant notes are included when the server has a compatible Unicode font installed. The existing print action opens the browser's print dialog.
8. **Clear current chat** removes only chat messages and their derived observations so the same account can be used for a clean self-test. **Delete saved data** permanently removes the account, profile, chat, report summary, and associated activity records from the local database.

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

The two-model flow uses Model 1 as a structured observation extractor after chat turns and activities. It records response time, typing corrections, and repeated-message counts when available. Model 2 runs when the participant requests an Agent summary and produces a patient-facing, non-diagnostic report without raw scores. If `GEMINI_LLM1_API_KEY` is not configured, local measured fields are still retained and Model 1's inferred fields remain empty; configure both model keys before deployment.

The constrained agentic workflow is described in `data/agentic_ai_configuration.json` and exposed to the signed-in application through `GET /api/agent/workflow`. It separates conversation, structured observation, and reporting responsibilities; validates the required workflow order; uses only consented server-provided context; keeps the daily session server-authoritative; allows no autonomous external actions; and forbids diagnosis, score invention, medication advice, or raw-score display in the patient view. The endpoint reports role availability without exposing credentials or participant data. Real credentials and external integrations remain deployment decisions.

For local hackathon demonstrations only, set `COGNI_DEMO_MODE=true` to use a clearly limited,
non-Agent chat reply when no Model 2 key is configured. This keeps the chat and activities
testable without exposing a key, but it is not an Agent integration and should be disabled
when validating the real provider setup.

The activity report now includes a personal-reference analysis: a 14-day calibration window with the first two days excluded as familiarization, descriptive per-domain baselines, recent within-person drift, data-quality notes, and a gentle persistent-pattern status. The status is not a clinical alert and is not used to diagnose or screen for a condition.

This local development setup is not suitable for real patient records or public deployment. Before using sensitive or care-related data in any deployment, obtain appropriate privacy, security, legal, ethics, and clinical review. Configure secure hosting, HTTPS, encrypted backups, retention and deletion policies, and production-grade secret/session management.

## Chat-platform integration

Telegram minimal proof is implemented behind `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, and `COGNI_PUBLIC_URL`: `POST /api/telegram/webhook` handles `/start`, `/report`, and `/help`, while `POST /api/auth/telegram` verifies signed, fresh Telegram Web App `initData`, requires local-data consent for first sign-in, maps the verified Telegram user to an app account, and issues the normal HttpOnly session cookie. The Mini App reuses the existing web UI and server-authoritative daily flow. Configure a public HTTPS URL and register the webhook with Telegram before a demo; local `127.0.0.1` cannot receive Telegram webhooks. Reminders, voice-note processing, family linking, alerts, and autonomous actions remain deferred. Do not treat a chat-platform user ID as authentication without verifying `initData`.

## API overview

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — account and session.
- `GET /api/conversations/{participant_id}`, `POST /api/chat` — authenticated chat history and Agent response.
- `GET /api/tasks`, `POST /api/task-results`, `POST /api/activities/attempts` — task bank and the current activity-result routes.
- `POST /api/sessions/today`, `GET /api/sessions/{date}` — create or retrieve the server-authoritative 13-step daily routine. An unfinished session restarts when a new daily entry begins; completed sessions remain complete.
- `POST /api/sessions/{date}/context`, `POST /api/sessions/{date}/messages`, `POST /api/sessions/{date}/games/{game_id}` — idempotent daily-session events. The server validates ordering and returns the next action.

Each session stores a stable participant/date-seeded order for all five activities: spatial recall, symbol matching, reaction tap, word recall, and category fluency. The browser submits each chat answer and activity result as an idempotent session event and disables activities that are not the current server step. Legacy chat and activity endpoints remain available for compatibility while the browser migration is completed.
- `POST /api/tasks/attempts` — legacy word-recall result route.
- `GET /api/reports/{participant_id}` — 30-day descriptive report.
- Family Track — authenticated 30-day routine view showing complete, partial, and not-started days in a responsive monthly grid.
- `GET /api/reports/{participant_id}/weekly/{YYYY-MM-DD}` — seven-day descriptive report ending on the requested local date.
- `POST /api/reports/{participant_id}/summary` — consent-required Agent reflection.
- `GET /api/reports/{participant_id}/pdf` — authenticated PDF download.
- `GET /api/reports/{participant_id}/daily/{YYYY-MM-DD}/pdf` — authenticated date-specific PDF download.
- `GET /api/reports/{participant_id}/weekly/{YYYY-MM-DD}/pdf` — authenticated seven-day PDF download.
- `DELETE /api/conversations/{participant_id}/messages` — clears chat messages and derived observations without deleting the account.
- `PUT /api/profile`, `PUT /api/consent/gemini` — profile and separate Agent-consent settings. The route name is retained for compatibility.
- `DELETE /api/conversations/{participant_id}` — delete the signed-in participant's account and associated records.

Participant-specific routes require an authenticated session and verify ownership.

## Privacy and security baseline

- Session tokens are random, stored hashed in SQLite, and sent only in `HttpOnly`, `SameSite=Lax` cookies. Set `COGNI_COOKIE_SECURE=1` behind HTTPS.
- Mutating API requests accept only configured same-origin browser requests. Set `COGNI_ALLOWED_ORIGINS` to a comma-separated allowlist when the frontend is hosted separately.
- API responses are marked `no-store`; browser responses include clickjacking, MIME-sniffing, referrer, permissions, and content-security policies.
- API body sizes are capped at 1 MiB and mutating routes have lightweight per-IP throttling. A production deployment must move rate limiting to a shared gateway or datastore.
- Agent keys are server-side environment secrets only. Never place them in browser code, JSON data, logs, reports, or Git.
- Account deletion cascades participant data. The chat-only reset removes messages and derived observations without deleting the account or activity history.
- This SQLite/local configuration is for development and hackathon testing, not sensitive production records. Production still requires HTTPS, encrypted storage/backups, managed secrets, monitoring, retention policy, and privacy/legal review.

The daily routine is ordered as: greeting, five conversational prompts, word seeding, Pattern Recall,
Symbol Match, Reaction Tap, Word Recall, Category Fluency, and completion. Browser clients must render
the returned `next` action rather than choosing the next step locally. Replaying a `client_event_id`
returns the existing session state without applying the event twice.

The web client uses a collapsible Menu button for navigation. Activity rounds become gradually more
challenging after completed activities on the same browser, without showing patient-facing scores.
Voice input uses the browser speech-recognition API when available, supports the selected language,
allows stopping and reviewing the transcript, and reports microphone permission failures explicitly. Activity order, word sets, visual patterns, and difficulty are stable but varied for each participant and local calendar day. A recognized voice transcript is treated as an input-capture signal only; it cannot establish a speech disorder, and recognition can be affected by accent, language, microphone quality, and browser support.
The web interface keeps keyboard-visible focus, touch-sized controls, reduced-motion support, live status messaging, and server-state activity gating. Telegram-specific layout and nonessential onboarding features remain intentionally deferred.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
node --check .\app.js
```

Passing software tests verify implementation behavior, not clinical validity or disease-detection accuracy.

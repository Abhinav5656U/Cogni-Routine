"""FastAPI application for Cogni-Routine."""

import os
import hashlib
import hmac
import html
import io
import json
import math
import re
import secrets
import sqlite3
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlsplit
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("COGNI_DB_PATH", BASE_DIR / "data" / "cogni_routine.sqlite3"))
TASKS_PATH = BASE_DIR / "data" / "cognitive_tasks.json"
QUESTIONS_PATH = BASE_DIR / "data" / "questions_30_days.json"
AGENTIC_CONFIG_PATH = BASE_DIR / "data" / "agentic_ai_configuration.json"
SESSION_COOKIE = "cogni_session"
SESSION_DAYS = 30
PASSWORD_ITERATIONS = 310_000
MAX_API_BODY_BYTES = 1_048_576
TELEGRAM_INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
DAILY_STEPS: tuple[tuple[str, str, str | None], ...] = (
    ("greet", "bot", None),
    ("q1", "ask", None),
    ("seed", "bot", None),
    ("g1", "game", "pattern_recall"),
    ("q2", "ask", None),
    ("g2", "game", "symbol_match"),
    ("q3", "ask", None),
    ("g3", "game", "reaction_tap"),
    ("q4", "ask", None),
    ("g4", "game", "word_recall"),
    ("q5", "ask", None),
    ("g5", "game", "category_fluency"),
    ("done", "complete", None),
)

app = FastAPI(
    title="Cogni-Routine",
    description="Multilingual check-ins and longitudinal activity summaries.",
    version="0.3.0",
)

_rate_limit_state: dict[tuple[str, str], list[float]] = {}


def _agentic_configuration() -> dict[str, Any]:
    try:
        configuration = json.loads(AGENTIC_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("Agentic AI configuration could not be loaded.") from error
    if not isinstance(configuration, dict) or not isinstance(configuration.get("agents"), list):
        raise RuntimeError("Agentic AI configuration is invalid.")
    agent_ids = [
        agent.get("id")
        for agent in configuration["agents"]
        if isinstance(agent, dict)
    ]
    expected_order = ["conversation-agent", "observation-agent", "reporting-agent"]
    if agent_ids != expected_order:
        raise RuntimeError("Agentic AI configuration has an invalid workflow order.")
    return configuration


def _agent_role(role_id: str) -> dict[str, Any]:
    configuration = _agentic_configuration()
    for agent in configuration["agents"]:
        if isinstance(agent, dict) and agent.get("id") == role_id:
            return agent
    raise RuntimeError(f"Agentic AI role is missing: {role_id}.")


def _agent_has_key(model_number: int) -> bool:
    if model_number == 1:
        return bool(
            os.environ.get("GEMINI_LLM1_API_KEY", "").strip()
            or os.environ.get("GEMINI_API_KEY", "").strip()
        )
    return bool(
        os.environ.get("GEMINI_LLM2_API_KEY", "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
    )


def _allowed_origins() -> set[str]:
    configured = os.environ.get("COGNI_ALLOWED_ORIGINS", "").strip()
    if configured:
        return {origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()}
    return {
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    }


def _rate_limit(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    client_host = request.client.host if request.client else "unknown"
    if request.url.path.startswith("/api/auth/"):
        limit, window = 60, 60.0
    elif request.url.path == "/api/chat":
        limit, window = 30, 60.0
    else:
        limit, window = 120, 60.0
    key = (client_host, request.url.path)
    now = time.monotonic()
    recent = [timestamp for timestamp in _rate_limit_state.get(key, []) if now - timestamp < window]
    if len(recent) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait and try again.")
    recent.append(now)
    _rate_limit_state[key] = recent


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            body_size = int(content_length)
        except ValueError:
            return Response(status_code=400, content="Invalid Content-Length header.")
        if body_size > MAX_API_BODY_BYTES:
            return Response(status_code=413, content="Request body is too large.")
    if request.url.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        if origin and origin.rstrip("/") not in _allowed_origins():
            return Response(status_code=403, content="Request origin is not allowed.")
        if not origin and referer:
            referer_origin = f"{urlsplit(referer).scheme}://{urlsplit(referer).netloc}"
            if referer_origin.rstrip("/") not in _allowed_origins():
                return Response(status_code=403, content="Request origin is not allowed.")
        try:
            _rate_limit(request)
        except HTTPException as error:
            return Response(
                status_code=error.status_code,
                content=json.dumps({"detail": error.detail}),
                media_type="application/json",
                headers={"Retry-After": "60"},
            )
    response = await call_next(request)
    response.headers.setdefault("X-Request-ID", secrets.token_hex(12))
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "microphone=(self), geolocation=(), camera=()")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    else:
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' https://telegram.org; frame-ancestors 'none'",
        )
    if os.environ.get("COGNI_COOKIE_SECURE", "0") == "1":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id TEXT PRIMARY KEY,
                language TEXT NOT NULL CHECK (language IN ('en', 'hi', 'mr')),
                consented_at TEXT NOT NULL,
                ai_consented_at TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                sender TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
                text TEXT NOT NULL,
                language TEXT NOT NULL CHECK (language IN ('en', 'hi', 'mr')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS task_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                task_name TEXT NOT NULL CHECK (task_name = 'word_recall'),
                score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 3),
                duration_seconds INTEGER NOT NULL CHECK (duration_seconds BETWEEN 0 AND 600),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activity_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                task_name TEXT NOT NULL CHECK (task_name IN ('word_recall', 'category_fluency', 'spatial_recall')),
                score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 50),
                max_score INTEGER NOT NULL CHECK (max_score BETWEEN 1 AND 50),
                duration_seconds INTEGER NOT NULL CHECK (duration_seconds BETWEEN 0 AND 600),
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS messages_participant_created
            ON messages (participant_id, id);

            CREATE INDEX IF NOT EXISTS tasks_participant_created
            ON task_attempts (participant_id, id);

            CREATE INDEX IF NOT EXISTS activities_participant_created
            ON activity_results (participant_id, created_at);

            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                participant_id TEXT NOT NULL UNIQUE REFERENCES participants(id) ON DELETE CASCADE,
                telegram_user_id TEXT UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_sessions (
                token_hash TEXT PRIMARY KEY,
                account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS sessions_account_expiry
            ON app_sessions (account_id, expires_at);

            CREATE TABLE IF NOT EXISTS participant_profiles (
                participant_id TEXT PRIMARY KEY REFERENCES participants(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 120),
                hobbies TEXT NOT NULL DEFAULT '',
                health_conditions TEXT NOT NULL DEFAULT '',
                concerns TEXT NOT NULL DEFAULT '',
                prior_report_notes TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS cognitive_task_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                task_id TEXT NOT NULL,
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                duration_seconds REAL NOT NULL,
                metrics_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS task_results_participant_created
            ON cognitive_task_results (participant_id, created_at);

            CREATE TABLE IF NOT EXISTS ai_report_summaries (
                participant_id TEXT PRIMARY KEY REFERENCES participants(id) ON DELETE CASCADE,
                summary_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cognitive_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                source TEXT NOT NULL,
                observation_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS observations_participant_created
            ON cognitive_observations (participant_id, created_at);

            CREATE TABLE IF NOT EXISTS daily_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                session_date TEXT NOT NULL,
                state TEXT NOT NULL,
                step_index INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                context_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (participant_id, session_date)
            );
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
                session_id INTEGER NOT NULL REFERENCES daily_sessions(id) ON DELETE CASCADE,
                client_event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE (participant_id, client_event_id)
            );
            CREATE INDEX IF NOT EXISTS sessions_participant_date
            ON daily_sessions (participant_id, session_date);
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(daily_sessions)").fetchall()
        }
        if "plan_json" not in columns:
            connection.execute("ALTER TABLE daily_sessions ADD COLUMN plan_json TEXT NOT NULL DEFAULT '[]'")
        participant_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(participants)")
        }
        if "ai_consented_at" not in participant_columns:
            connection.execute("ALTER TABLE participants ADD COLUMN ai_consented_at TEXT")
        account_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(accounts)").fetchall()
        }
        if "telegram_user_id" not in account_columns:
            connection.execute("ALTER TABLE accounts ADD COLUMN telegram_user_id TEXT")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS accounts_telegram_user_id "
                "ON accounts (telegram_user_id)"
            )


class ChatRequest(BaseModel):
    participant_id: UUID
    language: Literal["en", "hi", "mr"]
    text: str = Field(min_length=1, max_length=1000)
    consented: bool
    response_time_ms: int | None = Field(default=None, ge=0, le=3600000)
    typo_frequency: int = Field(default=0, ge=0, le=10000)
    repetition_count: int = Field(default=0, ge=0, le=1000)
    typing_duration_ms: int | None = Field(default=None, ge=0, le=3600000)
    keypress_count: int = Field(default=0, ge=0, le=100000)
    voice_duration_ms: int | None = Field(default=None, ge=0, le=3600000)
    voice_pause_count: int | None = Field(default=None, ge=0, le=10000)
    target_word_match: bool | None = None
    speech_capture_quality: Literal["matched", "not_matched", "unavailable"] | None = None
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    illness_today: bool | None = None
    device_type: Literal["phone", "tablet", "desktop", "unknown"] = "unknown"


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1, max_length=4096)
    consented: bool = False
    language: Literal["en", "hi", "mr"] = "en"
    name: str = Field(default="Telegram participant", min_length=1, max_length=100)
    age: int = Field(default=40, ge=18, le=120)


class TelegramUpdate(BaseModel):
    update_id: int | None = None
    message: dict[str, Any] | None = None


class RegistrationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=120)
    language: Literal["en", "hi", "mr"] = "en"
    hobbies: str = Field(default="", max_length=500)
    health_conditions: str = Field(default="", max_length=1000)
    concerns: str = Field(default="", max_length=1000)
    prior_report_notes: str = Field(default="", max_length=2000)
    consented: bool


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AiConsentRequest(BaseModel):
    consented: bool


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=120)
    language: Literal["en", "hi", "mr"]
    hobbies: str = Field(default="", max_length=500)
    health_conditions: str = Field(default="", max_length=1000)
    concerns: str = Field(default="", max_length=1000)
    prior_report_notes: str = Field(default="", max_length=2000)


class TaskResultRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=60)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0, le=1000)
    duration_seconds: float = Field(ge=0, le=3600)
    metrics: dict[str, float] = Field(default_factory=dict)
    consented: bool


class ReportSummaryRequest(BaseModel):
    pass


class SessionContextRequest(BaseModel):
    sleep: int | None = Field(default=None, ge=1, le=5)
    mood: Literal["positive", "neutral", "low", "anxious"] | None = None
    unwell: bool | None = None
    client_event_id: str = Field(min_length=1, max_length=100)


class SessionMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    latency_ms: int | None = Field(default=None, ge=0, le=3600000)
    typing: dict[str, Any] = Field(default_factory=dict)
    client_event_id: str = Field(min_length=1, max_length=100)


class SessionGameRequest(BaseModel):
    skipped: bool = False
    result: dict[str, Any] = Field(default_factory=dict)
    client_event_id: str = Field(min_length=1, max_length=100)


class Model1Observation(BaseModel):
    language_and_fluency: dict[str, Any]
    memory_indicators: dict[str, Any]
    sentiment_and_mood: dict[str, Any]
    behavioral_markers: dict[str, Any]


def _default_observation() -> dict[str, Any]:
    return {
        "language_and_fluency": {
            "vocabulary_richness": None,
            "sentence_coherence": None,
            "word_finding_difficulty": False,
        },
        "memory_indicators": {"short_term_recall": None, "context_retention": None},
        "sentiment_and_mood": {"current_sentiment": "Neutral", "engagement_level": None},
        "behavioral_markers": {
            "response_time_ms": None,
            "typo_frequency": 0,
            "repetition_count": 0,
        },
    }


class MessageResponse(BaseModel):
    id: int
    sender: Literal["user", "assistant"]
    text: str
    language: Literal["en", "hi", "mr"]
    created_at: str


class ChatResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class HistoryResponse(BaseModel):
    messages: list[MessageResponse]


class TaskAttemptRequest(BaseModel):
    participant_id: UUID
    language: Literal["en", "hi", "mr"]
    task_name: Literal["word_recall"]
    score: int = Field(ge=0, le=3)
    duration_seconds: int = Field(ge=0, le=600)
    consented: bool


class TaskAttemptResponse(BaseModel):
    id: int
    task_name: str
    score: int
    max_score: int = 3
    duration_seconds: int
    created_at: str


class ActivityResultRequest(BaseModel):
    participant_id: UUID
    language: Literal["en", "hi", "mr"]
    task_name: Literal["word_recall", "category_fluency", "spatial_recall"]
    score: int = Field(ge=0, le=50)
    max_score: int = Field(ge=1, le=50)
    duration_seconds: int = Field(ge=0, le=600)
    consented: bool


class ActivityResultResponse(BaseModel):
    id: int
    task_name: str
    score: int
    max_score: int
    duration_seconds: int
    created_at: str
    metrics: dict[str, float] = Field(default_factory=dict)


class DailyReportPoint(BaseModel):
    date: str
    task_count: int
    checkin_messages: int
    complete: bool
    domain_scores: dict[str, float]


class ActivityReportResponse(BaseModel):
    period_start: str
    period_end: str
    checkin_days: int
    user_messages: int
    assistant_responses: int
    current_streak: int
    valid_days: int
    baseline_days: int
    baseline_ready: bool
    days_since_signup: int
    daily: list[DailyReportPoint]
    attempts: list[ActivityResultResponse]
    baseline_analysis: dict[str, Any] = Field(default_factory=dict)


def _slice_report(
    report: ActivityReportResponse,
    period_start: date,
    period_end: date,
) -> ActivityReportResponse:
    daily = [
        point for point in report.daily
        if period_start.isoformat() <= point.date <= period_end.isoformat()
    ]
    attempts = [
        attempt for attempt in report.attempts
        if period_start.isoformat() <= attempt.created_at[:10] <= period_end.isoformat()
    ]
    completed_dates = {point.date for point in daily if point.complete}
    candidate = period_end
    streak = 0
    while candidate.isoformat() in completed_dates:
        streak += 1
        candidate -= timedelta(days=1)
    return report.model_copy(update={
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "checkin_days": sum(point.checkin_messages > 0 for point in daily),
        "user_messages": sum(point.checkin_messages for point in daily),
        "assistant_responses": sum(point.checkin_messages for point in daily),
        "current_streak": streak,
        "valid_days": sum(point.complete for point in daily),
        "daily": daily,
        "attempts": attempts,
    })


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


def _password_hash(password: str, salt: bytes | None = None) -> str:
    actual_salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), actual_salt, PASSWORD_ITERATIONS)
    return f"{actual_salt.hex()}${derived.hex()}"


def _password_matches(password: str, stored_hash: str) -> bool:
    salt_hex, expected_hex = stored_hash.split("$", 1)
    return hmac.compare_digest(_password_hash(password, bytes.fromhex(salt_hex)), f"{salt_hex}${expected_hex}")


def _inserted_id(cursor: sqlite3.Cursor) -> int:
    if cursor.lastrowid is None:
        raise RuntimeError("Database insert did not return a row ID.")
    return cursor.lastrowid


def _issue_session(account_id: int, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=SESSION_DAYS)
    with database() as connection:
        connection.execute(
            "DELETE FROM app_sessions WHERE expires_at <= ?",
            (now.isoformat(),),
        )
        connection.execute(
            "INSERT INTO app_sessions (token_hash, account_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (
                hashlib.sha256(token.encode()).hexdigest(),
                account_id,
                expires.isoformat(),
                now.isoformat(),
            ),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=os.environ.get("COGNI_COOKIE_SECURE", "0") == "1",
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 60 * 60,
        path="/",
    )


def _telegram_bot_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def _verify_telegram_init_data(init_data: str) -> dict[str, Any]:
    bot_token = _telegram_bot_token()
    if not bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot integration is not configured.")
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = fields.pop("hash", "")
    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram sign-in data is incomplete.")
    check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, expected_hash):
        raise HTTPException(status_code=401, detail="Telegram sign-in data could not be verified.")
    try:
        auth_date = int(fields["auth_date"])
        user = json.loads(fields["user"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=401, detail="Telegram sign-in data is invalid.") from error
    if datetime.now(timezone.utc).timestamp() - auth_date > TELEGRAM_INIT_DATA_MAX_AGE_SECONDS:
        raise HTTPException(status_code=401, detail="Telegram sign-in data has expired.")
    if datetime.now(timezone.utc).timestamp() < auth_date - 60:
        raise HTTPException(status_code=401, detail="Telegram sign-in data is not yet valid.")
    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise HTTPException(status_code=401, detail="Telegram user data is invalid.")
    return user


def _telegram_web_app_url() -> str:
    public_url = os.environ.get("COGNI_PUBLIC_URL", "").strip().rstrip("/")
    if not public_url.startswith(("https://", "http://")):
        raise HTTPException(status_code=503, detail="Set COGNI_PUBLIC_URL before enabling Telegram.")
    return public_url


def _telegram_api_call(method: str, payload: dict[str, Any]) -> None:
    bot_token = _telegram_bot_token()
    if not bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot integration is not configured.")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=502, detail="Telegram could not be reached.") from error
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail="Telegram rejected the bot request.")


def _telegram_start_markup() -> dict[str, Any]:
    return {
        "inline_keyboard": [[
            {
                "text": "Open Cogni-Routine",
                "web_app": {"url": _telegram_web_app_url()},
            }
        ]]
    }


def _current_account(request: Request) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        row = connection.execute(
            """
            SELECT accounts.id, accounts.email, accounts.participant_id,
                   participants.language, participants.ai_consented_at,
                   participant_profiles.name, participant_profiles.age,
                   participant_profiles.hobbies, participant_profiles.health_conditions,
                   participant_profiles.concerns, participant_profiles.prior_report_notes
            FROM app_sessions
            JOIN accounts ON accounts.id = app_sessions.account_id
            JOIN participants ON participants.id = accounts.participant_id
            JOIN participant_profiles ON participant_profiles.participant_id = participants.id
            WHERE app_sessions.token_hash = ? AND app_sessions.expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Your session expired. Please sign in again.")
    return dict(row)


def _require_owned_participant(participant_id: UUID, account: dict[str, Any]) -> str:
    owned_id = str(account["participant_id"])
    if str(participant_id) != owned_id:
        raise HTTPException(status_code=404, detail="Participant record was not found.")
    return owned_id


def _register_unicode_report_font() -> str | None:
    font_name = "CogniRoutineUnicode"
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name
    windows_directory = Path(os.environ.get("WINDIR", "C:\\Windows"))
    candidates = (
        windows_directory / "Fonts" / "Nirmala.ttc",
        Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
        Path("/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
    )
    font_path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if font_path is None:
        return None
    pdfmetrics.registerFont(TTFont(font_name, str(font_path), subfontIndex=0))
    pdfmetrics.registerFontFamily(
        font_name,
        normal=font_name,
        bold=font_name,
        italic=font_name,
        boldItalic=font_name,
    )
    return font_name


def _create_model_response(
    prompt: str,
    contents: list[dict[str, Any]],
    *,
    model_number: int,
) -> str:
    suffix = f"LLM{model_number}"
    api_key = os.environ.get(f"GEMINI_{suffix}_API_KEY", "").strip()
    if not api_key and model_number == 1:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Agent provider is not configured. Set the provider key on the server to enable replies.",
        )
    model = os.environ.get(
        f"GEMINI_{suffix}_MODEL",
        os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
    ).strip()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 700},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Agent request failed with status {error.code}. Check the server key, model, and quota.",
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise HTTPException(status_code=502, detail="Agent could not be reached. Please try again.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=502, detail="Agent returned an unreadable response.") from error

    try:
        text = "".join(
            part["text"]
            for part in result["candidates"][0]["content"]["parts"]
            if isinstance(part.get("text"), str)
        ).strip()
    except (KeyError, IndexError, TypeError) as error:
        raise HTTPException(status_code=502, detail="Agent returned no usable text.") from error
    if not text:
        raise HTTPException(status_code=502, detail="Agent returned an empty reply.")
    return text


def _create_gemini_response(prompt: str, contents: list[dict[str, Any]]) -> str:
    """Compatibility wrapper for existing integrations and tests."""
    return _create_model_response(prompt, contents, model_number=2)


def _extract_model1_observation(
    *,
    text: str,
    language: str,
    response_time_ms: int | None,
    typo_frequency: int,
    repetition_count: int,
    activity: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not _agent_has_key(1):
        observation = _default_observation()
        observation["behavioral_markers"].update(
            {
                "response_time_ms": response_time_ms,
                "typo_frequency": typo_frequency,
                "repetition_count": repetition_count,
                **(context or {}),
            }
        )
        return observation
    role = _agent_role("observation-agent")
    prompt = (
        f"You are the {role['role']} for a wellbeing app. "
        "Return JSON only with exactly these keys: language_and_fluency, memory_indicators, "
        "sentiment_and_mood, behavioral_markers. Use null when an indicator cannot be observed. "
        "Do not diagnose, screen, predict, or call anything a red flag. "
        f"Language: {language}. User input: {json.dumps(text, ensure_ascii=False)}. "
        f"Activity context: {json.dumps(activity or {}, ensure_ascii=False)}. "
        f"Daily context: {json.dumps(context or {}, ensure_ascii=False)}. "
        f"Measured response_time_ms: {response_time_ms}; typo_frequency: {typo_frequency}; "
        f"repetition_count: {repetition_count}."
    )
    try:
        raw = _create_model_response(
            prompt,
            [{"role": "user", "parts": [{"text": text}]}],
            model_number=1,
        )
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Model 1 returned a non-object.")
        observation = _default_observation()
        for key in observation:
            if isinstance(parsed.get(key), dict):
                observation[key].update(parsed[key])
        observation["behavioral_markers"].update(
            {
                "response_time_ms": response_time_ms,
                "typo_frequency": typo_frequency,
                "repetition_count": repetition_count,
                **(context or {}),
            }
        )
        return observation
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise HTTPException(status_code=502, detail="Model 1 returned invalid observation JSON.") from error


def _save_observation(participant_id: str, source: str, observation: dict[str, Any]) -> None:
    with database() as connection:
        connection.execute(
            """
            INSERT INTO cognitive_observations
                (participant_id, source, observation_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                participant_id,
                source,
                json.dumps(observation, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def _calculate_baseline_analysis(
    rows: list[dict[str, Any]],
    registration_date: date,
    local_end_date: date,
    task_domains: dict[str, str],
) -> dict[str, Any]:
    """Calculate descriptive within-person drift; this is not a clinical alert."""
    daily_domains: dict[str, dict[str, list[float]]] = {}
    quality_notes: list[str] = []
    for row in rows:
        day = datetime.fromisoformat(row["created_at"]).astimezone(INDIA_TIMEZONE).date()
        domain = task_domains.get(row["task_name"], row["task_name"])
        if row["max_score"] <= 0:
            quality_notes.append(f"{day.isoformat()}: missing activity maximum")
            continue
        daily_domains.setdefault(day.isoformat(), {}).setdefault(domain, []).append(
            row["score"] / row["max_score"] * 100
        )
        metrics = row.get("metrics", {})
        if metrics.get("median_response_ms") is None and domain == "response":
            quality_notes.append(f"{day.isoformat()}: response timing unavailable")

    calibration_days = [
        registration_date + timedelta(days=offset)
        for offset in range(2, 14)
        if registration_date + timedelta(days=offset) <= local_end_date
    ]
    calibration_values: dict[str, list[float]] = {}
    for day in calibration_days:
        for domain, values in daily_domains.get(day.isoformat(), {}).items():
            calibration_values.setdefault(domain, []).append(sum(values) / len(values))

    baselines: dict[str, dict[str, Any]] = {}
    for domain, values in calibration_values.items():
        if not values:
            continue
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        baselines[domain] = {
            "mean": round(mean, 1),
            "sd": round(math.sqrt(variance), 1),
            "days": len(values),
        }

    recent_dates = [
        local_end_date - timedelta(days=offset)
        for offset in range(2, -1, -1)
    ]
    domain_analysis: dict[str, dict[str, Any]] = {}
    low_domains_by_day: dict[str, set[str]] = {}
    for domain, baseline in baselines.items():
        recent: list[dict[str, Any]] = []
        for day in recent_dates:
            values = daily_domains.get(day.isoformat(), {}).get(domain, [])
            if not values:
                continue
            observed = sum(values) / len(values)
            sd = baseline["sd"] or 1.0
            z_score = (observed - baseline["mean"]) / sd
            recent.append({"date": day.isoformat(), "z_score": round(z_score, 2)})
            if z_score <= -1.5:
                low_domains_by_day.setdefault(day.isoformat(), set()).add(domain)
        domain_analysis[domain] = {
            **baseline,
            "recent": recent,
            "unusual_days": sum(
                1 for entry in recent if entry["z_score"] <= -1.5
            ),
        }

    persistent_dates = [
        day for day, domains in low_domains_by_day.items() if len(domains) >= 2
    ]
    return {
        "calibration": {
            "start": (registration_date + timedelta(days=2)).isoformat(),
            "end": (registration_date + timedelta(days=13)).isoformat(),
            "eligible_days": len(calibration_days),
            "observed_domains": len(baselines),
        },
        "domains": domain_analysis,
        "persistent_change": len(persistent_dates) >= 3,
        "persistent_change_days": sorted(persistent_dates),
        "data_quality": sorted(set(quality_notes))[:20],
        "interpretation": (
            "Unusual within-person pattern for review; not a diagnosis."
            if len(persistent_dates) >= 3
            else "No persistent multi-domain pattern identified in this period."
        ),
    }


def _ai_is_consented(account: dict[str, Any]) -> bool:
    return account["ai_consented_at"] is not None


def _demo_mode_enabled() -> bool:
    return os.environ.get("COGNI_DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}


def _demo_chat_reply(text: str, language: str) -> str:
    replies = {
        "en": "Thanks for sharing. I’m here with you. What would you like to tell me about your day?",
        "hi": "साझा करने के लिए धन्यवाद। मैं आपके साथ हूँ। आप अपने दिन के बारे में और क्या बताना चाहेंगे?",
        "mr": "सांगितल्याबद्दल धन्यवाद. मी तुमच्यासोबत आहे. तुमच्या दिवसाबद्दल आणखी काय सांगाल?",
    }
    return replies[language]


def _session_copy(session: sqlite3.Row) -> dict[str, Any]:
    steps = _steps_for_session(session)
    game_order = json.loads(session["plan_json"] or "[]")
    step_id, step_type, game_id = steps[session["step_index"]]
    return {
        "id": session["id"],
        "date": session["session_date"],
        "status": session["status"],
        "state": step_id,
        "step_index": session["step_index"],
        "steps_total": len(DAILY_STEPS),
        "tasks_completed": sum(
            1
            for index in range(session["step_index"])
            if steps[index][1] == "game"
        ),
        "next": {
            "type": step_type,
            **({"game_id": game_id} if game_id else {}),
        },
        "context": json.loads(session["context_json"] or "{}"),
        "game_order": game_order,
    }


def _steps_for_session(session: sqlite3.Row) -> tuple[tuple[str, str, str | None], ...]:
    order = json.loads(session["plan_json"] or "[]")
    if len(order) != 5:
        order = ["pattern_recall", "symbol_match", "reaction_tap", "word_recall", "category_fluency"]
    game_index = 0
    steps: list[tuple[str, str, str | None]] = []
    for step_id, step_type, game_id in DAILY_STEPS:
        if step_type == "game":
            steps.append((step_id, step_type, order[game_index]))
            game_index += 1
        else:
            steps.append((step_id, step_type, game_id))
    return tuple(steps)


def _session_bot_messages(session: sqlite3.Row, language: str) -> list[dict[str, str]]:
    copy = {
        "en": {
            "greet": "Good to see you. How are you feeling today?",
            "seed": "Keep these three words in mind for later: mango, river, candle.",
            "done": "That's everything for today. Thank you.",
        },
        "hi": {
            "greet": "आपसे फिर बात करके अच्छा लगा। आज आपको कैसा महसूस हो रहा है?",
            "seed": "इन तीन शब्दों को बाद के लिए याद रखें: आम, नदी, दीपक।",
            "done": "आज के लिए इतना ही। धन्यवाद।",
        },
        "mr": {
            "greet": "तुमच्याशी पुन्हा बोलून आनंद झाला. आज तुम्हाला कसे वाटत आहे?",
            "seed": "हे तीन शब्द नंतरसाठी लक्षात ठेवा: आंबा, नदी, दिवा.",
            "done": "आजसाठी एवढेच. धन्यवाद.",
        },
    }[language]
    messages: list[dict[str, str]] = []
    steps = _steps_for_session(session)
    for index in range(session["step_index"]):
        step_id = steps[index][0]
        if step_id in copy:
            messages.append({"role": "bot", "text": copy[step_id], "step": step_id})
    return messages


def _advance_automatic_steps(connection: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    while True:
        session = connection.execute(
            "SELECT * FROM daily_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=404, detail="Daily session was not found.")
        steps = _steps_for_session(session)
        step_type = steps[session["step_index"]][1]
        if step_type not in {"bot", "complete"}:
            return session
        next_index = min(session["step_index"] + 1, len(steps) - 1)
        status = "complete" if steps[session["step_index"]][0] == "done" else "active"
        connection.execute(
            """
            UPDATE daily_sessions SET step_index = ?, state = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                next_index if status == "active" else session["step_index"],
                steps[next_index if status == "active" else session["step_index"]][0],
                status,
                datetime.now(timezone.utc).isoformat(),
                session_id,
            ),
        )
        if status == "complete":
            return connection.execute(
                "SELECT * FROM daily_sessions WHERE id = ?", (session_id,)
            ).fetchone()


def _session_payload(session: sqlite3.Row, language: str) -> dict[str, Any]:
    return {
        "session": _session_copy(session),
        "bot_messages": _session_bot_messages(session, language),
        "voice_practice_word": _daily_voice_practice_word(
            str(session["participant_id"]), session["session_date"], language
        ),
    }


def _daily_voice_practice_word(participant_id: str, session_date: str, language: str) -> str:
    words = {
        "en": ["river", "garden", "window", "candle", "morning", "silver"],
        "hi": ["नदी", "बगीचा", "खिड़की", "दीपक", "सुबह", "चाँदी"],
        "mr": ["नदी", "बाग", "खिडकी", "दिवा", "सकाळ", "चांदी"],
    }[language]
    digest = hashlib.sha256(f"voice:{participant_id}:{session_date}".encode("utf-8")).digest()
    return words[digest[0] % len(words)]


def _daily_game_order(participant_id: str, session_date: str) -> list[str]:
    games = ["pattern_recall", "symbol_match", "reaction_tap", "word_recall", "category_fluency"]
    seed = hashlib.sha256(f"{participant_id}:{session_date}".encode("utf-8")).digest()
    ordered = list(games)
    for index in range(len(ordered) - 1, 0, -1):
        swap_index = seed[index] % (index + 1)
        ordered[index], ordered[swap_index] = ordered[swap_index], ordered[index]
    return ordered


def _get_or_create_session(
    participant_id: str,
    session_date: str,
    language: str,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO daily_sessions
                (participant_id, session_date, state, step_index, plan_json, created_at, updated_at)
            VALUES (?, ?, 'greet', 0, ?, ?, ?)
            """,
            (
                participant_id,
                session_date,
                json.dumps(_daily_game_order(participant_id, session_date)),
                timestamp,
                timestamp,
            ),
        )
        session = connection.execute(
            "SELECT * FROM daily_sessions WHERE participant_id = ? AND session_date = ?",
            (participant_id, session_date),
        ).fetchone()
        session = _advance_automatic_steps(connection, session["id"])
        return _session_payload(session, language)


def _record_session_event(
    connection: sqlite3.Connection,
    participant_id: str,
    session_id: int,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    try:
        connection.execute(
            """
            INSERT INTO session_events
                (participant_id, session_id, client_event_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                participant_id,
                session_id,
                event_id,
                event_type,
                json.dumps(payload, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return True
    except sqlite3.IntegrityError:
        return False


@app.post("/api/sessions/today")
def create_or_resume_today(account: dict[str, Any] = Depends(_current_account)) -> dict[str, Any]:
    today = datetime.now(INDIA_TIMEZONE).date().isoformat()
    participant_id = str(account["participant_id"])
    with database() as connection:
        existing = connection.execute(
            "SELECT * FROM daily_sessions WHERE participant_id = ? AND session_date = ?",
            (participant_id, today),
        ).fetchone()
        if existing and existing["status"] != "complete":
            connection.execute(
                """
                UPDATE daily_sessions
                SET state = 'greet', step_index = 0, status = 'active',
                    context_json = '{}', plan_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(_daily_game_order(participant_id, today)),
                    datetime.now(timezone.utc).isoformat(),
                    existing["id"],
                ),
            )
    return _get_or_create_session(participant_id, today, account["language"])


@app.get("/api/sessions/{session_date}")
def get_daily_session(
    session_date: str,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    try:
        date.fromisoformat(session_date)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Session date must be YYYY-MM-DD.") from error
    participant_id = str(account["participant_id"])
    with database() as connection:
        session = connection.execute(
            "SELECT * FROM daily_sessions WHERE participant_id = ? AND session_date = ?",
            (participant_id, session_date),
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=404, detail="Daily session was not found.")
        session = _advance_automatic_steps(connection, session["id"])
        return _session_payload(session, account["language"])


@app.post("/api/sessions/{session_date}/context")
def save_session_context(
    session_date: str,
    request: SessionContextRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    participant_id = str(account["participant_id"])
    with database() as connection:
        session = connection.execute(
            "SELECT * FROM daily_sessions WHERE participant_id = ? AND session_date = ?",
            (participant_id, session_date),
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=404, detail="Daily session was not found.")
        if not _record_session_event(connection, participant_id, session["id"], request.client_event_id, "context", request.model_dump()):
            return _session_payload(session, account["language"])
        context = json.loads(session["context_json"] or "{}")
        context.update(request.model_dump(exclude={"client_event_id"}))
        connection.execute(
            "UPDATE daily_sessions SET context_json = ?, step_index = ?, state = ?, updated_at = ? WHERE id = ?",
            (
                json.dumps(context, ensure_ascii=False),
                2,
                _steps_for_session(session)[2][0],
                datetime.now(timezone.utc).isoformat(),
                session["id"],
            ),
        )
        session = _advance_automatic_steps(connection, session["id"])
        return _session_payload(session, account["language"])


def _advance_session_after_event(
    connection: sqlite3.Connection,
    session: sqlite3.Row,
) -> sqlite3.Row:
    steps = _steps_for_session(session)
    next_index = min(session["step_index"] + 1, len(steps) - 1)
    connection.execute(
        """
        UPDATE daily_sessions SET step_index = ?, state = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            next_index,
            steps[next_index][0],
            datetime.now(timezone.utc).isoformat(),
            session["id"],
        ),
    )
    return _advance_automatic_steps(connection, session["id"])


@app.post("/api/sessions/{session_date}/messages")
def save_session_message(
    session_date: str,
    request: SessionMessageRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    participant_id = str(account["participant_id"])
    with database() as connection:
        session = connection.execute(
            "SELECT * FROM daily_sessions WHERE participant_id = ? AND session_date = ?",
            (participant_id, session_date),
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=404, detail="Daily session was not found.")
        steps = _steps_for_session(session)
        if steps[session["step_index"]][1] != "ask":
            raise HTTPException(status_code=409, detail="The daily session is waiting for its current step.")
        if not _record_session_event(connection, participant_id, session["id"], request.client_event_id, "message", request.model_dump()):
            return _session_payload(session, account["language"])
        existing_message = connection.execute(
            """
            SELECT id FROM messages
            WHERE participant_id = ? AND sender = 'user' AND text = ?
            ORDER BY id DESC LIMIT 1
            """,
            (participant_id, request.text.strip()),
        ).fetchone()
        if existing_message is None:
            timestamp = datetime.now(timezone.utc).isoformat()
            connection.execute(
                """
                INSERT INTO messages (participant_id, sender, text, language, created_at)
                VALUES (?, 'user', ?, ?, ?)
                """,
                (participant_id, request.text.strip(), account["language"], timestamp),
            )
        next_session = _advance_session_after_event(connection, session)
        return _session_payload(next_session, account["language"])


@app.post("/api/sessions/{session_date}/games/{game_id}")
def save_session_game(
    session_date: str,
    game_id: str,
    request: SessionGameRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    participant_id = str(account["participant_id"])
    with database() as connection:
        session = connection.execute(
            "SELECT * FROM daily_sessions WHERE participant_id = ? AND session_date = ?",
            (participant_id, session_date),
        ).fetchone()
        if session is None:
            raise HTTPException(status_code=404, detail="Daily session was not found.")
        steps = _steps_for_session(session)
        expected_game = steps[session["step_index"]][2]
        if steps[session["step_index"]][1] != "game" or expected_game != game_id:
            raise HTTPException(status_code=409, detail="That puzzle is not the current daily step.")
        if not _record_session_event(connection, participant_id, session["id"], request.client_event_id, "game", request.model_dump()):
            return _session_payload(session, account["language"])
        next_session = _advance_session_after_event(connection, session)
        return _session_payload(next_session, account["language"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    try:
        with database() as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as error:
        raise HTTPException(status_code=503, detail="Database is not ready.") from error
    return {"status": "ready"}


@app.get("/api/agent/workflow")
def agent_workflow(
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    """Expose safe workflow metadata without provider credentials or participant data."""
    try:
        configuration = _agentic_configuration()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {
        "name": configuration["name"],
        "version": configuration["version"],
        "state_source": configuration["orchestration"]["state_source"],
        "order": configuration["orchestration"]["order"],
        "external_actions": configuration["orchestration"]["external_actions"],
        "consented": _ai_is_consented(account),
        "agents": [
            {
                "id": agent["id"],
                "role": agent["role"],
                "available": _agent_has_key(1 if agent["id"] == "observation-agent" else 2)
                or agent["id"] == "conversation-agent" and _demo_mode_enabled(),
                "consent_required": agent.get("consent_required", False),
            }
            for agent in configuration["agents"]
        ],
    }


@app.get("/api/daily-question/{participant_id}")
def daily_question(
    participant_id: UUID,
    language: Literal["en", "hi", "mr"] = "en",
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, str]:
    owned_id = _require_owned_participant(participant_id, account)
    question_bank = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    questions = question_bank.get("questions", [])[: int(question_bank.get("cycle_days", 30))]
    if not questions:
        raise HTTPException(status_code=500, detail="The daily question file is empty.")
    today = datetime.now(INDIA_TIMEZONE).date().isoformat()
    seed = hashlib.sha256(f"{owned_id}:{today}".encode("utf-8")).digest()
    index = int.from_bytes(seed[:8], "big") % len(questions)
    text = questions[index].get("text", {}).get(language)
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=500, detail="The daily question has no translation.")
    report = activity_report(participant_id, account)
    difficulty = "gentle" if report.baseline_analysis.get("persistent_change") else "standard"
    return {"id": str(questions[index].get("id", index)), "text": text, "difficulty": difficulty}


@app.post("/api/auth/telegram")
def telegram_auth(request: TelegramAuthRequest, response: Response) -> dict[str, Any]:
    user = _verify_telegram_init_data(request.init_data)
    telegram_user_id = str(user["id"])
    with database() as connection:
        row = connection.execute(
            """
            SELECT accounts.id, accounts.email, accounts.participant_id, participant_profiles.name
            FROM accounts
            JOIN participant_profiles ON participant_profiles.participant_id = accounts.participant_id
            WHERE accounts.telegram_user_id = ?
            """,
            (telegram_user_id,),
        ).fetchone()
        if row is None:
            if not request.consented:
                raise HTTPException(
                    status_code=400,
                    detail="Consent to save check-ins and activity results is required before Telegram sign-in.",
                )
            participant_id = str(UUID(bytes=secrets.token_bytes(16), version=4))
            timestamp = datetime.now(timezone.utc).isoformat()
            display_name = request.name.strip() or user.get("first_name") or "Telegram participant"
            email = f"telegram-{telegram_user_id}@telegram.local"
            connection.execute(
                "INSERT INTO participants (id, language, consented_at, created_at) VALUES (?, ?, ?, ?)",
                (participant_id, request.language, timestamp, timestamp),
            )
            cursor = connection.execute(
                """
                INSERT INTO accounts
                    (email, password_hash, participant_id, telegram_user_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (email, _password_hash(secrets.token_urlsafe(32)), participant_id, telegram_user_id, timestamp),
            )
            connection.execute(
                """
                INSERT INTO participant_profiles
                    (participant_id, name, age, hobbies, health_conditions, concerns, prior_report_notes)
                VALUES (?, ?, ?, '', '', '', '')
                """,
                (participant_id, display_name, request.age),
            )
            account_id = _inserted_id(cursor)
            account = {"participant_id": participant_id, "email": email, "name": display_name}
        else:
            account_id = row["id"]
            account = dict(row)
    _issue_session(account_id, response)
    return account


@app.post("/api/telegram/webhook")
def telegram_webhook(request: Request, update: TelegramUpdate) -> dict[str, bool]:
    expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not expected_secret or not hmac.compare_digest(
        request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""),
        expected_secret,
    ):
        raise HTTPException(status_code=403, detail="Telegram webhook authorization failed.")
    message = update.message or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = str(message.get("text") or "").strip()
    if not isinstance(chat_id, int):
        return {"ok": True}
    if text.startswith("/start"):
        _telegram_api_call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "Open Cogni-Routine to start your daily check-in.",
                "reply_markup": _telegram_start_markup(),
            },
        )
    elif text.startswith("/report"):
        _telegram_api_call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "Open Cogni-Routine and choose My history to view your report.",
                "reply_markup": _telegram_start_markup(),
            },
        )
    elif text.startswith("/help"):
        _telegram_api_call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "Use /start to open Cogni-Routine. The bot does not provide medical advice or diagnosis.",
            },
        )
    return {"ok": True}


@app.post("/api/auth/register", status_code=201)
def register(request: RegistrationRequest, response: Response) -> dict[str, Any]:
    if not request.consented:
        raise HTTPException(status_code=400, detail="Consent to local data storage is required to create an account.")
    email = request.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    participant_id = str(UUID(bytes=secrets.token_bytes(16), version=4))
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with database() as connection:
            connection.execute(
                "INSERT INTO participants (id, language, consented_at, created_at) VALUES (?, ?, ?, ?)",
                (participant_id, request.language, timestamp, timestamp),
            )
            cursor = connection.execute(
                "INSERT INTO accounts (email, password_hash, participant_id, created_at) VALUES (?, ?, ?, ?)",
                (email, _password_hash(request.password), participant_id, timestamp),
            )
            connection.execute(
                """
                INSERT INTO participant_profiles
                    (participant_id, name, age, hobbies, health_conditions, concerns, prior_report_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    participant_id,
                    request.name.strip(),
                    request.age,
                    request.hobbies.strip(),
                    request.health_conditions.strip(),
                    request.concerns.strip(),
                    request.prior_report_notes.strip(),
                ),
            )
            account_id = _inserted_id(cursor)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="An account with that email already exists.") from error
    _issue_session(account_id, response)
    return {"participant_id": participant_id, "email": email, "name": request.name.strip()}


@app.post("/api/auth/login")
def login(request: LoginRequest, response: Response) -> dict[str, Any]:
    email = request.email.strip().lower()
    with database() as connection:
        row = connection.execute(
            """
            SELECT accounts.id, accounts.password_hash, accounts.participant_id, participant_profiles.name
            FROM accounts
            JOIN participant_profiles ON participant_profiles.participant_id = accounts.participant_id
            WHERE accounts.email = ?
            """,
            (email,),
        ).fetchone()
    if row is None or not _password_matches(request.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    _issue_session(row["id"], response)
    return {
        "participant_id": row["participant_id"],
        "email": email,
        "name": row["name"],
    }


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with database() as connection:
            connection.execute(
                "DELETE FROM app_sessions WHERE token_hash = ?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            )
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax")


@app.get("/api/auth/me")
def current_user(account: dict[str, Any] = Depends(_current_account)) -> dict[str, Any]:
    return {
        **account,
        "ai_consented": _ai_is_consented(account),
    }


@app.put("/api/profile")
def update_profile(
    request: ProfileUpdateRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, str]:
    participant_id = str(account["participant_id"])
    with database() as connection:
        connection.execute(
            """
            UPDATE participant_profiles
            SET name = ?, age = ?, hobbies = ?, health_conditions = ?, concerns = ?, prior_report_notes = ?
            WHERE participant_id = ?
            """,
            (
                request.name.strip(),
                request.age,
                request.hobbies.strip(),
                request.health_conditions.strip(),
                request.concerns.strip(),
                request.prior_report_notes.strip(),
                participant_id,
            ),
        )
        connection.execute(
            "UPDATE participants SET language = ? WHERE id = ?",
            (request.language, participant_id),
        )
    return {"status": "saved"}


@app.put("/api/consent/gemini")
def set_gemini_consent(
    request: AiConsentRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, bool]:
    consented_at = datetime.now(timezone.utc).isoformat() if request.consented else None
    with database() as connection:
        connection.execute(
            "UPDATE participants SET ai_consented_at = ? WHERE id = ?",
            (consented_at, str(account["participant_id"])),
        )
        if not request.consented:
            connection.execute(
                "DELETE FROM ai_report_summaries WHERE participant_id = ?",
                (str(account["participant_id"]),),
            )
    return {"ai_consented": request.consented}


@app.get("/api/conversations/{participant_id}", response_model=HistoryResponse)
def conversation_history(
    participant_id: UUID,
    account: dict[str, Any] = Depends(_current_account),
) -> HistoryResponse:
    owned_id = _require_owned_participant(participant_id, account)
    with database() as connection:
        rows = connection.execute(
            """
            SELECT id, sender, text, language, created_at
            FROM messages
            WHERE participant_id = ?
            ORDER BY id
            """,
            (owned_id,),
        ).fetchall()
    return HistoryResponse(messages=[MessageResponse(**dict(row)) for row in rows])


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> ChatResponse:
    owned_id = _require_owned_participant(request.participant_id, account)
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")
    if not request.consented:
        raise HTTPException(status_code=403, detail="Consent is required before saving messages.")
    if not _ai_is_consented(account):
        raise HTTPException(status_code=403, detail="Enable separate Agent data consent before using chat.")

    timestamp = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        history = connection.execute(
            """
            SELECT sender, text FROM messages
            WHERE participant_id = ? ORDER BY id DESC LIMIT 10
            """,
            (owned_id,),
        ).fetchall()
    history.reverse()
    contents = [
        {
            "role": "model" if row["sender"] == "assistant" else "user",
            "parts": [{"text": row["text"]}],
        }
        for row in history
    ]
    contents.append({"role": "user", "parts": [{"text": text}]})
    language_name = {"en": "English", "hi": "Hindi", "mr": "Marathi"}[request.language]
    if _demo_mode_enabled() and not (
        os.environ.get("GEMINI_LLM2_API_KEY", "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
    ):
        reply = _demo_chat_reply(text, request.language)
    else:
        reply = _create_gemini_response(
            (
                f"You are the {_agent_role('conversation-agent')['role']}, not a clinician. "
                "Respond in "
                f"{language_name}. Discuss routines and feelings in plain language. Do not diagnose, screen for, "
                "predict, or rule out a condition, and do not claim the user has cognitive decline. If asked for "
                "a diagnosis, say you cannot assess that and encourage discussing concerns with a qualified "
                "healthcare professional. Never present activity scores as clinical test results. Be brief, "
                "respectful, and avoid pretending certainty. Do not provide medication changes."
            ),
            contents,
        )
    observation = _extract_model1_observation(
        text=text,
        language=request.language,
        response_time_ms=request.response_time_ms,
        typo_frequency=request.typo_frequency,
        repetition_count=request.repetition_count,
        context={
            "typing_duration_ms": request.typing_duration_ms,
            "keypress_count": request.keypress_count,
            "voice_duration_ms": request.voice_duration_ms,
            "voice_pause_count": request.voice_pause_count,
            "target_word_match": request.target_word_match,
            "speech_capture_quality": request.speech_capture_quality,
            "sleep_quality": request.sleep_quality,
            "illness_today": request.illness_today,
            "device_type": request.device_type,
        },
    )

    with database() as connection:
        user_cursor = connection.execute(
            """
            INSERT INTO messages (participant_id, sender, text, language, created_at)
            VALUES (?, 'user', ?, ?, ?)
            """,
            (owned_id, text, request.language, timestamp),
        )
        assistant_cursor = connection.execute(
            """
            INSERT INTO messages (participant_id, sender, text, language, created_at)
            VALUES (?, 'assistant', ?, ?, ?)
            """,
            (owned_id, reply, request.language, timestamp),
        )
    _save_observation(owned_id, "chat", observation)

    return ChatResponse(
        user_message=MessageResponse(
            id=_inserted_id(user_cursor),
            sender="user",
            text=text,
            language=request.language,
            created_at=timestamp,
        ),
        assistant_message=MessageResponse(
            id=_inserted_id(assistant_cursor),
            sender="assistant",
            text=reply,
            language=request.language,
            created_at=timestamp,
        ),
    )


@app.post("/api/tasks/attempts", response_model=TaskAttemptResponse)
def save_task_attempt(
    request: TaskAttemptRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> TaskAttemptResponse:
    if not request.consented:
        raise HTTPException(status_code=403, detail="Consent is required before saving activity results.")

    participant_id = _require_owned_participant(request.participant_id, account)
    timestamp = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO task_attempts (participant_id, task_name, score, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (participant_id, request.task_name, request.score, request.duration_seconds, timestamp),
        )

    return TaskAttemptResponse(
        id=_inserted_id(cursor),
        task_name=request.task_name,
        score=request.score,
        max_score=3,
        duration_seconds=request.duration_seconds,
        created_at=timestamp,
    )


@app.post("/api/activities/attempts", response_model=ActivityResultResponse)
def save_activity_result(
    request: ActivityResultRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> ActivityResultResponse:
    if not request.consented:
        raise HTTPException(status_code=403, detail="Consent is required before saving activity results.")
    expected_max_scores = {"word_recall": 3, "category_fluency": 50, "spatial_recall": 3}
    expected_max_score = expected_max_scores[request.task_name]
    if request.max_score != expected_max_score or request.score > expected_max_score:
        raise HTTPException(status_code=422, detail="The score is outside the selected activity's range.")

    participant_id = _require_owned_participant(request.participant_id, account)
    timestamp = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO activity_results
                (participant_id, task_name, score, max_score, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                participant_id,
                request.task_name,
                request.score,
                request.max_score,
                request.duration_seconds,
                timestamp,
            ),
        )

    return ActivityResultResponse(
        id=_inserted_id(cursor),
        task_name=request.task_name,
        score=request.score,
        max_score=request.max_score,
        duration_seconds=request.duration_seconds,
        created_at=timestamp,
    )


@app.get("/api/tasks")
def get_cognitive_tasks(account: dict[str, Any] = Depends(_current_account)) -> dict[str, Any]:
    del account
    return json.loads(TASKS_PATH.read_text(encoding="utf-8"))


@app.post("/api/task-results", status_code=201)
def save_cognitive_task_result(
    request: TaskResultRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    if not request.consented:
        raise HTTPException(status_code=403, detail="Consent is required before saving activity results.")
    bank = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in bank["tasks"]}
    task = tasks.get(request.task_id)
    if task is None:
        raise HTTPException(status_code=422, detail="Unknown cognitive activity.")
    if request.max_score != task["max_score"] or request.score > request.max_score:
        raise HTTPException(status_code=422, detail="Score does not match this activity's scale.")
    if any(not key or len(key) > 50 for key in request.metrics):
        raise HTTPException(status_code=422, detail="Invalid activity metric.")
    timestamp = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO cognitive_task_results
                (participant_id, task_id, score, max_score, duration_seconds, metrics_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(account["participant_id"]),
                request.task_id,
                request.score,
                request.max_score,
                request.duration_seconds,
                json.dumps(request.metrics),
                timestamp,
            ),
        )
    _save_observation(
        str(account["participant_id"]),
        "activity",
        _extract_model1_observation(
            text="",
            language=account["language"],
            response_time_ms=None,
            typo_frequency=0,
            repetition_count=0,
            activity={
                "task_id": request.task_id,
                "score": request.score,
                "max_score": request.max_score,
                "duration_seconds": request.duration_seconds,
                "metrics": request.metrics,
            },
        ),
    )
    return {
        "id": _inserted_id(cursor),
        "task_id": request.task_id,
        "score": request.score,
        "max_score": request.max_score,
        "duration_seconds": request.duration_seconds,
        "created_at": timestamp,
    }


@app.get("/api/reports/{participant_id}", response_model=ActivityReportResponse)
def activity_report(
    participant_id: UUID,
    account: dict[str, Any] = Depends(_current_account),
) -> ActivityReportResponse:
    owned_id = _require_owned_participant(participant_id, account)
    end = datetime.now(timezone.utc)
    local_end = end.astimezone(INDIA_TIMEZONE)
    start = end - timedelta(days=30)
    period_start = (local_end.date() - timedelta(days=29)).isoformat()
    period_end = local_end.date().isoformat()
    start_timestamp = start.isoformat()
    with database() as connection:
        rows = connection.execute(
            """
            SELECT id, task_name, score, 3 AS max_score, duration_seconds, created_at, '{}' AS metrics_json
            FROM task_attempts
            WHERE participant_id = ? AND created_at >= ?
            UNION ALL
            SELECT id, task_name, score, max_score, duration_seconds, created_at, '{}' AS metrics_json
            FROM activity_results
            WHERE participant_id = ? AND created_at >= ?
            UNION ALL
            SELECT id, task_id AS task_name, CAST(score AS INTEGER) AS score,
                   CAST(max_score AS INTEGER) AS max_score,
                   CAST(duration_seconds AS INTEGER) AS duration_seconds, created_at, metrics_json
            FROM cognitive_task_results
            WHERE participant_id = ? AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT 300
            """,
            (owned_id, start_timestamp, owned_id, start_timestamp, owned_id, start_timestamp),
        ).fetchall()
        message_rows = connection.execute(
            """
            SELECT sender, created_at
            FROM messages
            WHERE participant_id = ? AND created_at >= ?
            """,
            (owned_id, start_timestamp),
        ).fetchall()
        participant_row = connection.execute(
            "SELECT created_at FROM participants WHERE id = ?",
            (owned_id,),
        ).fetchone()

    task_bank = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    task_domains = {task["id"]: task["domain"] for task in task_bank["tasks"]}
    localized_rows = [
        {**dict(row), "metrics": json.loads(row["metrics_json"] or "{}")}
        for row in rows
    ]
    day_tasks: dict[str, set[str]] = {}
    day_domains: dict[str, dict[str, list[float]]] = {}
    for row in localized_rows:
        day = datetime.fromisoformat(row["created_at"]).astimezone(INDIA_TIMEZONE).date().isoformat()
        day_tasks.setdefault(day, set()).add(row["task_name"])
        domain = task_domains.get(row["task_name"], row["task_name"])
        day_domains.setdefault(day, {}).setdefault(domain, []).append(row["score"] / row["max_score"] * 100)

    day_messages: dict[str, int] = {}
    sender_counts = {"user": 0, "assistant": 0}
    for row in message_rows:
        day = datetime.fromisoformat(row["created_at"]).astimezone(INDIA_TIMEZONE).date().isoformat()
        sender_counts[row["sender"]] += 1
        if row["sender"] == "user":
            day_messages[day] = day_messages.get(day, 0) + 1

    report_dates = [
        (local_end.date() - timedelta(days=offset)).isoformat()
        for offset in range(29, -1, -1)
    ]
    daily = [
        DailyReportPoint(
            date=day,
            task_count=len(day_tasks.get(day, set())),
            checkin_messages=day_messages.get(day, 0),
            complete=len(day_tasks.get(day, set())) >= 3,
            domain_scores={
                domain: round(sum(scores) / len(scores), 1)
                for domain, scores in day_domains.get(day, {}).items()
            },
        )
        for day in report_dates
    ]
    valid_days = sum(point.complete for point in daily)
    completed_dates = {point.date for point in daily if point.complete}
    candidate_date = local_end.date()
    if candidate_date.isoformat() not in completed_dates:
        candidate_date -= timedelta(days=1)
    streak_days = 0
    while candidate_date.isoformat() in completed_dates:
        streak_days += 1
        candidate_date -= timedelta(days=1)
    registration_date = (
        datetime.fromisoformat(participant_row["created_at"])
        .astimezone(INDIA_TIMEZONE)
        .date()
    )
    baseline_days = sum(
        point.complete
        and 3 <= (date.fromisoformat(point.date) - registration_date).days + 1 <= 14
        for point in daily
    )
    days_since_signup = (local_end.date() - registration_date).days + 1
    baseline_analysis = _calculate_baseline_analysis(
        localized_rows,
        registration_date,
        local_end.date(),
        task_domains,
    )
    return ActivityReportResponse(
        period_start=period_start,
        period_end=period_end,
        checkin_days=len(day_messages),
        user_messages=sender_counts["user"],
        assistant_responses=sender_counts["assistant"],
        current_streak=streak_days,
        valid_days=valid_days,
        baseline_days=baseline_days,
        baseline_ready=baseline_days >= 10,
        days_since_signup=days_since_signup,
        daily=daily,
        baseline_analysis=baseline_analysis,
        attempts=[
            ActivityResultResponse(
                id=row["id"],
                task_name=row["task_name"],
                score=row["score"],
                max_score=row["max_score"],
                duration_seconds=row["duration_seconds"],
                created_at=row["created_at"],
                metrics=row["metrics"],
            )
            for row in localized_rows
        ],
    )


@app.post("/api/reports/{participant_id}/summary")
def ai_report_summary(
    participant_id: UUID,
    request: ReportSummaryRequest,
    account: dict[str, Any] = Depends(_current_account),
) -> dict[str, Any]:
    del request
    owned_id = _require_owned_participant(participant_id, account)
    if not _ai_is_consented(account):
        raise HTTPException(status_code=403, detail="Enable Agent data consent before generating a summary.")
    report = activity_report(participant_id, account)
    with database() as connection:
        messages = connection.execute(
            """
            SELECT sender, text, created_at FROM messages
            WHERE participant_id = ? AND created_at >= ?
            ORDER BY id DESC LIMIT 120
            """,
            (owned_id, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()),
        ).fetchall()
        model_observations = connection.execute(
            """
            SELECT observation_json FROM cognitive_observations
            WHERE participant_id = ? AND created_at >= ?
            ORDER BY id
            LIMIT 300
            """,
            (owned_id, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()),
        ).fetchall()
    bank = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    task_names = {task["id"]: task["name"] for task in bank["tasks"]}
    observations = [
        {
            "activity": task_names.get(attempt.task_name, attempt.task_name),
            "score": attempt.score,
            "maximum": attempt.max_score,
            "duration_seconds": attempt.duration_seconds,
            "date": attempt.created_at[:10],
            "metrics": attempt.metrics,
        }
        for attempt in report.attempts
    ]
    chat_excerpt = [
        {"role": "assistant" if row["sender"] == "assistant" else "user", "text": row["text"]}
        for row in reversed(messages)
    ]
    prompt = (
        f"You are the {_agent_role('reporting-agent')['role']}, not a clinician. Do not diagnose, "
        "screen, classify, predict, or rule out disease. Do not call observations red flags or clinical "
        "findings. Return JSON only with exactly this structure: patient_overview (session_date, "
        "session_duration_minutes, overall_mood), cognitive_summary (memory_status, language_status, "
        "processing_speed), alerts_and_flags (cognitive_decline_indicators, mood_alerts), "
        "recommendations (clinical_action, next_session_adjustments). Use plain, gentle language, no "
        "raw scores, and say that persistent concerns should be discussed with a qualified professional. "
        "Use 'No concerning pattern identified in this session' rather than a diagnosis when appropriate. "
        "Do not include profile fields. "
        f"Activity observations: {json.dumps(observations, ensure_ascii=False)}\n"
        f"Personal baseline analysis: {json.dumps(report.baseline_analysis, ensure_ascii=False)}\n"
        f"Model 1 structured observations: {json.dumps([json.loads(row['observation_json']) for row in model_observations], ensure_ascii=False)}\n"
        f"Conversation excerpt: {json.dumps(chat_excerpt, ensure_ascii=False)}"
    )
    text = _create_gemini_response(
        "Follow the requested JSON format exactly. Do not use markdown fences.",
        [{"role": "user", "parts": [{"text": prompt}]}],
    )
    try:
        summary = json.loads(text)
        legacy_shape = (
            isinstance(summary, dict)
            and set(summary) == {"summary", "positives", "watch_items"}
            and isinstance(summary["summary"], str)
            and isinstance(summary["positives"], list)
            and isinstance(summary["watch_items"], list)
            and all(isinstance(item, str) for item in summary["positives"] + summary["watch_items"])
        )
        structured_shape = isinstance(summary, dict) and set(summary) == {
            "patient_overview",
            "cognitive_summary",
            "alerts_and_flags",
            "recommendations",
        }
        if not legacy_shape and not structured_shape:
            raise ValueError("Unexpected report summary shape.")
    except (json.JSONDecodeError, ValueError, TypeError) as error:
        raise HTTPException(status_code=502, detail="Agent returned an invalid report summary.") from error
    required_ending = "This is not a diagnosis; discuss persistent changes with a doctor."
    if "summary" in summary and not summary["summary"].endswith(required_ending):
        summary["summary"] = f"{summary['summary'].rstrip()} {required_ending}"
    with database() as connection:
        connection.execute(
            """
            INSERT INTO ai_report_summaries (participant_id, summary_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(participant_id) DO UPDATE SET
                summary_json = excluded.summary_json,
                created_at = excluded.created_at
            """,
            (owned_id, json.dumps(summary, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
        )
    return summary


@app.get("/api/reports/{participant_id}/weekly/{week_end}", response_model=ActivityReportResponse)
def weekly_report(
    participant_id: UUID,
    week_end: str,
    account: dict[str, Any] = Depends(_current_account),
) -> ActivityReportResponse:
    try:
        end = date.fromisoformat(week_end)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Week end must be YYYY-MM-DD.") from error
    if end > datetime.now(INDIA_TIMEZONE).date():
        raise HTTPException(status_code=422, detail="Week end cannot be in the future.")
    return _slice_report(activity_report(participant_id, account), end - timedelta(days=6), end)


@app.get("/api/reports/{participant_id}/daily/{report_date}/pdf")
def download_daily_report_pdf(
    participant_id: UUID,
    report_date: str,
    account: dict[str, Any] = Depends(_current_account),
) -> Response:
    try:
        date.fromisoformat(report_date)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Report date must be YYYY-MM-DD.") from error
    return download_report_pdf(
        participant_id,
        account,
        report_start=report_date,
        report_end=report_date,
    )


@app.get("/api/reports/{participant_id}/weekly/{week_end}/pdf")
def download_weekly_report_pdf(
    participant_id: UUID,
    week_end: str,
    account: dict[str, Any] = Depends(_current_account),
) -> Response:
    try:
        end = date.fromisoformat(week_end)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Week end must be YYYY-MM-DD.") from error
    if end > datetime.now(INDIA_TIMEZONE).date():
        raise HTTPException(status_code=422, detail="Week end cannot be in the future.")
    return download_report_pdf(
        participant_id,
        account,
        report_start=(end - timedelta(days=6)).isoformat(),
        report_end=end.isoformat(),
    )


@app.get("/api/reports/{participant_id}/pdf")
def download_report_pdf(
    participant_id: UUID,
    account: dict[str, Any] = Depends(_current_account),
    report_start: str | None = None,
    report_end: str | None = None,
) -> Response:
    owned_id = _require_owned_participant(participant_id, account)
    report = activity_report(participant_id, account)
    if report_start and report_end:
        start_date = date.fromisoformat(report_start)
        end_date = date.fromisoformat(report_end)
        report = _slice_report(report, start_date, end_date)
    with database() as connection:
        profile = connection.execute(
            """
            SELECT name, age, hobbies, health_conditions, concerns, prior_report_notes
            FROM participant_profiles WHERE participant_id = ?
            """,
            (owned_id,),
        ).fetchone()
        summary_row = connection.execute(
            "SELECT summary_json FROM ai_report_summaries WHERE participant_id = ?",
            (owned_id,),
        ).fetchone()

    task_bank = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    task_names = {task["id"]: task["name"] for task in task_bank["tasks"]}
    grouped: dict[str, list[float]] = {}
    for attempt in report.attempts:
        grouped.setdefault(attempt.task_name, []).append(attempt.score / attempt.max_score * 100)

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Cogni-Routine activity report",
        author="Cogni-Routine",
    )
    unicode_font = _register_unicode_report_font()
    report_font = unicode_font or "Helvetica"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName=report_font,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#173a61"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="ReportSection",
        parent=styles["Heading2"],
        fontName=report_font,
        textColor=colors.HexColor("#173a61"),
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontName=report_font,
        leading=14,
        spaceAfter=5,
    ))

    def paragraph(text: str, style: str = "ReportBody") -> Paragraph:
        if unicode_font is None and any(ord(character) > 255 for character in text):
            raise HTTPException(
                status_code=503,
                detail="This server needs a Unicode font to include Hindi or Marathi text in the PDF.",
            )
        escaped_text = html.escape(text).replace("\n", "<br/>")
        return Paragraph(escaped_text, styles[style])

    story = [
        paragraph("Cogni-Routine activity report", "ReportTitle"),
        paragraph(f"Reporting period: {report.period_start} to {report.period_end}"),
        paragraph(
            "Descriptive self-tracking information for discussion with a healthcare professional. "
            "These activities are not validated diagnostic tests."
        ),
        paragraph("Participant-provided context", "ReportSection"),
        paragraph(f"Name: {profile['name']}  |  Age: {profile['age']}"),
    ]
    for label, key in (
        ("Interests", "hobbies"),
        ("Health conditions", "health_conditions"),
        ("Concerns", "concerns"),
        ("Notes from prior reports", "prior_report_notes"),
    ):
        if profile[key]:
            story.append(paragraph(f"{label}: {profile[key]}"))

    summary_table = Table(
        [
            ["Check-in days", "Messages", "Activities", "Complete days", "Current streak"],
            [
                str(report.checkin_days),
                str(report.user_messages),
                str(len(report.attempts)),
                str(report.valid_days),
                str(report.current_streak),
            ],
        ],
        colWidths=[34 * mm, 30 * mm, 30 * mm, 34 * mm, 34 * mm],
        hAlign="LEFT",
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2fa")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173a61")),
        ("FONTNAME", (0, 0), (-1, 0), report_font),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd8e6")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        paragraph("Participation summary", "ReportSection"),
        summary_table,
        paragraph(
            "A complete day means three distinct activity types were recorded. This is an app "
            "tracking definition, not a clinical threshold."
        ),
    ])

    if grouped:
        chart = VerticalBarChart()
        chart.x = 42
        chart.y = 34
        chart.width = 440
        chart.height = 145
        chart.data = [tuple(round(sum(scores) / len(scores), 1) for scores in grouped.values())]
        chart.categoryAxis.categoryNames = [
            task_names.get(task_id, task_id).replace("_", " ").title()
            for task_id in grouped
        ]
        chart.categoryAxis.labels.fontName = "Helvetica"
        chart.categoryAxis.labels.fontSize = 7
        chart.categoryAxis.labels.angle = 25
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 100
        chart.valueAxis.valueStep = 20
        chart.valueAxis.labels.fontSize = 8
        chart.bars[0].fillColor = colors.HexColor("#2c6aa0")
        drawing = Drawing(500, 195)
        drawing.add(chart)
        story.extend([
            paragraph("Average recorded activity scores", "ReportSection"),
            drawing,
            paragraph(
                "Bars show the average recorded score as a percentage of the activity's app-defined "
                "maximum. Different activities are not interchangeable and these values are not "
                "clinical scores."
            ),
        ])

    if report.attempts:
        rows = [["Date", "Activity", "Score", "Duration"]]
        for attempt in report.attempts:
            rows.append([
                attempt.created_at[:10],
                task_names.get(attempt.task_name, attempt.task_name).replace("_", " ").title(),
                f"{attempt.score:g} / {attempt.max_score:g}",
                f"{attempt.duration_seconds:g} sec",
            ])
        activity_table = Table(rows, colWidths=[32 * mm, 68 * mm, 35 * mm, 35 * mm], repeatRows=1)
        activity_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2fa")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173a61")),
            ("FONTNAME", (0, 0), (-1, 0), report_font),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd8e6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([
            paragraph("Recent activity entries", "ReportSection"),
            activity_table,
        ])
    else:
        story.extend([
            paragraph("Recent activity entries", "ReportSection"),
            paragraph("No cognitive activity results were recorded in this reporting period."),
        ])

    if summary_row:
        saved_summary = json.loads(summary_row["summary_json"])
        story.extend([
            paragraph("Agent reflection", "ReportSection"),
            paragraph(saved_summary["summary"]),
        ])
        for label, key in (("Positive observations", "positives"), ("Items to reflect on", "watch_items")):
            values = saved_summary.get(key, [])
            if values:
                story.append(paragraph(label, "Heading3"))
                story.extend(paragraph(f"- {item}") for item in values)

    story.extend([
        Spacer(1, 8),
        paragraph(
            "AI reflections are generated from the consented conversation and activity summaries. "
            "They may be incomplete or inaccurate. This report does not "
            "diagnose, screen for, or rule out any condition."
        ),
    ])
    document.build(story)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="cogni-routine-{report.period_start}-to-{report.period_end}.pdf"'
            ),
            "Cache-Control": "no-store",
        },
    )


@app.delete("/api/conversations/{participant_id}", status_code=204)
def delete_conversation(
    participant_id: UUID,
    account: dict[str, Any] = Depends(_current_account),
) -> None:
    owned_id = _require_owned_participant(participant_id, account)
    with database() as connection:
        connection.execute("DELETE FROM participants WHERE id = ?", (owned_id,))


@app.delete("/api/conversations/{participant_id}/messages", status_code=204)
def clear_conversation_messages(
    participant_id: UUID,
    account: dict[str, Any] = Depends(_current_account),
) -> None:
    owned_id = _require_owned_participant(participant_id, account)
    with database() as connection:
        connection.execute("DELETE FROM messages WHERE participant_id = ?", (owned_id,))
        connection.execute("DELETE FROM cognitive_observations WHERE participant_id = ?", (owned_id,))


initialize_database()
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="frontend")

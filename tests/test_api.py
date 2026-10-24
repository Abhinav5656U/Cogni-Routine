import json
import hashlib
import hmac
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

import main


class ChatApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "test.sqlite3"
        self.db_patcher = patch.object(main, "DB_PATH", self.db_path)
        self.db_patcher.start()
        main.initialize_database()
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.participant_id = self.register()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self.db_patcher.stop()
        self.temp_directory.cleanup()

    def register(
        self,
        email: str | None = None,
        *,
        consented: bool = True,
    ) -> str:
        response = self.client.post(
            "/api/auth/register",
            json={
                "email": email or f"{uuid4()}@example.test",
                "password": "Secure-password-123",
                "name": "Test Participant",
                "age": 68,
                "language": "en",
                "hobbies": "gardening",
                "health_conditions": "optional local note",
                "concerns": "",
                "prior_report_notes": "",
                "consented": consented,
            },
        )
        if response.status_code == 201:
            return response.json()["participant_id"]
        return ""

    def consent_to_agent(self) -> None:
        response = self.client.put("/api/consent/gemini", json={"consented": True})
        self.assertEqual(response.status_code, 200)

    def chat(self, text: str = "I enjoyed gardening today.", language: str = "en"):
        self.consent_to_agent()
        with patch.object(main, "_create_agent_response", return_value="That sounds pleasant."):
            return self.client.post(
                "/api/chat",
                json={
                    "participant_id": self.participant_id,
                    "language": language,
                    "text": text,
                    "consented": True,
                },
            )

    def test_registration_requires_storage_consent(self) -> None:
        response = self.client.post(
            "/api/auth/register",
            json={
                "email": f"{uuid4()}@example.test",
                "password": "Secure-password-123",
                "name": "Participant",
                "age": 65,
                "consented": False,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_liveness_and_readiness_endpoints(self) -> None:
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})
        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})

    def test_agent_workflow_is_consent_gated_and_does_not_expose_keys(self) -> None:
        response = self.client.get("/api/agent/workflow")
        self.assertEqual(response.status_code, 200)
        workflow = response.json()
        self.assertFalse(workflow["consented"])
        self.assertEqual(
            workflow["order"],
            ["conversation-agent", "observation-agent", "reporting-agent"],
        )
        self.assertEqual(workflow["external_actions"], [])
        self.assertNotIn("api_key", json.dumps(workflow))

        self.consent_to_agent()
        consented = self.client.get("/api/agent/workflow").json()
        self.assertTrue(consented["consented"])

    def test_agent_workflow_requires_authentication(self) -> None:
        self.client.post("/api/auth/logout")
        response = self.client.get("/api/agent/workflow")
        self.assertEqual(response.status_code, 401)

    def test_security_headers_and_same_origin_protection(self) -> None:
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("x-request-id", response.headers)
        blocked = self.client.post(
            "/api/auth/logout",
            headers={"Origin": "https://untrusted.example"},
        )
        self.assertEqual(blocked.status_code, 403)

    def test_telegram_init_data_requires_valid_signature_and_consent(self) -> None:
        auth_date = str(int(main.datetime.now(main.timezone.utc).timestamp()))
        fields = {
            "auth_date": auth_date,
            "user": json.dumps({"id": 998877, "first_name": "Telegram"}, separators=(",", ":")),
        }
        bot_token = "telegram-test-token"
        check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        fields["hash"] = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": bot_token}):
            denied = self.client.post(
                "/api/auth/telegram",
                json={"init_data": urlencode(fields)},
            )
            self.assertEqual(denied.status_code, 400)
            signed_in = self.client.post(
                "/api/auth/telegram",
                json={"init_data": urlencode(fields), "consented": True},
            )
        self.assertEqual(signed_in.status_code, 200)
        self.assertEqual(signed_in.json()["name"], "Telegram participant")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        fields["hash"] = "invalid"
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": bot_token}):
            invalid = self.client.post(
                "/api/auth/telegram",
                json={"init_data": urlencode(fields), "consented": True},
            )
        self.assertEqual(invalid.status_code, 401)

    def test_telegram_webhook_requires_secret_and_handles_start(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_BOT_TOKEN": "telegram-test-token",
                "TELEGRAM_WEBHOOK_SECRET": "webhook-secret",
                "COGNI_PUBLIC_URL": "https://demo.example",
            },
        ), patch.object(main, "_telegram_api_call") as telegram_call:
            denied = self.client.post(
                "/api/telegram/webhook",
                json={"message": {"chat": {"id": 123}, "text": "/start"}},
            )
            self.assertEqual(denied.status_code, 403)
            response = self.client.post(
                "/api/telegram/webhook",
                headers={"X-Telegram-Bot-Api-Secret-Token": "webhook-secret"},
                json={"message": {"chat": {"id": 123}, "text": "/start"}},
            )
        self.assertEqual(response.status_code, 200)
        telegram_call.assert_called_once()
        self.assertEqual(telegram_call.call_args.args[0], "sendMessage")
        self.assertEqual(telegram_call.call_args.args[1]["chat_id"], 123)

    def test_oversized_api_request_is_rejected(self) -> None:
        response = self.client.post(
            "/api/auth/logout",
            headers={"Content-Length": str(main.MAX_API_BODY_BYTES + 1)},
        )
        self.assertEqual(response.status_code, 413)

    def test_login_logout_and_invalid_password(self) -> None:
        email = self.client.get("/api/auth/me").json()["email"]
        self.client.post("/api/auth/logout")
        wrong_password = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": "incorrect"},
        )
        self.assertEqual(wrong_password.status_code, 401)
        login = self.client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "Secure-password-123",
            },
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_groq_chat_requires_explicit_ai_consent_and_persists_response(self) -> None:
        request = {
            "participant_id": self.participant_id,
            "language": "hi",
            "text": "आज दिन अच्छा रहा",
            "consented": True,
        }
        denied = self.client.post("/api/chat", json=request)
        self.assertEqual(denied.status_code, 403)
        self.consent_to_agent()
        with patch.object(main, "_create_agent_response", return_value="आपका दिन अच्छा रहा, यह सुनकर खुशी हुई।"):
            response = self.client.post("/api/chat", json=request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("अच्छा रहा", response.json()["assistant_message"]["text"])
        history = self.client.get(f"/api/conversations/{self.participant_id}")
        self.assertEqual([row["sender"] for row in history.json()["messages"]], ["user", "assistant"])

    def test_missing_groq_key_returns_explicit_error_without_saving_message(self) -> None:
        self.consent_to_agent()
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}), patch.object(main, "client", None):
            response = self.client.post(
                "/api/chat",
                json={
                    "participant_id": self.participant_id,
                    "language": "en",
                    "text": "Hello",
                    "consented": True,
                },
            )
        self.assertEqual(response.status_code, 503)
        history = self.client.get(f"/api/conversations/{self.participant_id}")
        self.assertEqual(history.json()["messages"], [])

    def test_groq_chat_completion_uses_configured_model_and_extracts_text(self) -> None:
        create = Mock(
            return_value=SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Groq reply"))]
            )
        )
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=create),
            )
        )
        with patch.dict(
            "os.environ",
            {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "test-model"},
        ), patch.object(main, "client", fake_client):
            text = main._create_model_response(
                "System prompt",
                [
                    {"role": "user", "parts": [{"text": "Hello"}]},
                    {"role": "model", "parts": [{"text": "Earlier reply"}]},
                ],
                model_number=1,
            )
        self.assertEqual(text, "Groq reply")
        self.assertEqual(create.call_args.kwargs["model"], "test-model")
        self.assertEqual(
            create.call_args.kwargs["messages"],
            [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Earlier reply"},
            ],
        )

    def test_account_cannot_access_another_participants_records(self) -> None:
        own_id = self.participant_id
        other_client = TestClient(main.app)
        with other_client:
            other = other_client.post(
                "/api/auth/register",
                json={
                    "email": f"{uuid4()}@example.test",
                    "password": "Another-password-123",
                    "name": "Other Participant",
                    "age": 72,
                    "consented": True,
                },
            ).json()["participant_id"]
        response = self.client.get(f"/api/conversations/{other}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get(f"/api/conversations/{own_id}").status_code, 200)

    def test_profile_fields_are_saved_locally(self) -> None:
        profile = self.client.get("/api/auth/me").json()
        self.assertEqual(profile["hobbies"], "gardening")
        self.assertEqual(profile["health_conditions"], "optional local note")
        self.assertFalse(profile["ai_consented"])
        updated = self.client.put(
            "/api/profile",
            json={
                "name": "Test Participant",
                "age": 68,
                "language": "mr",
                "hobbies": "music",
                "health_conditions": "updated local note",
                "concerns": "",
                "prior_report_notes": "",
            },
        )
        self.assertEqual(updated.status_code, 200)
        refreshed = self.client.get("/api/auth/me").json()
        self.assertEqual(refreshed["language"], "mr")
        self.assertEqual(refreshed["hobbies"], "music")

    def test_task_bank_and_task_results(self) -> None:
        bank = self.client.get("/api/tasks")
        self.assertEqual(bank.status_code, 200)
        task = next(task for task in bank.json()["tasks"] if task["id"] == "symbol_match")
        self.assertEqual(task["max_score"], 8)
        saved = self.client.post(
            "/api/task-results",
            json={
                "task_id": "symbol_match",
                "score": 6,
                "max_score": 8,
                "duration_seconds": 21,
                "metrics": {"correct_matches": 6, "median_response_ms": 720},
                "consented": True,
            },
        )
        self.assertEqual(saved.status_code, 201)
        self.assertEqual(saved.json()["score"], 6)
        invalid = self.client.post(
            "/api/task-results",
            json={
                "task_id": "symbol_match",
                "score": 9,
                "max_score": 8,
                "duration_seconds": 21,
                "metrics": {},
                "consented": True,
            },
        )
        self.assertEqual(invalid.status_code, 422)

    def test_report_counts_chat_and_task_results(self) -> None:
        self.chat()
        self.client.post(
            "/api/task-results",
            json={
                "task_id": "spatial_recall",
                "score": 2,
                "max_score": 3,
                "duration_seconds": 12,
                "metrics": {"correct_positions": 2},
                "consented": True,
            },
        )
        report = self.client.get(f"/api/reports/{self.participant_id}")
        result = report.json()
        self.assertEqual(result["checkin_days"], 1)
        self.assertEqual(result["user_messages"], 1)
        self.assertEqual(result["assistant_responses"], 1)
        self.assertEqual(len(result["attempts"]), 1)
        self.assertEqual(result["attempts"][0]["task_name"], "spatial_recall")
        self.assertEqual(len(result["daily"]), 30)
        self.assertEqual(result["valid_days"], 0)
        self.assertFalse(result["baseline_ready"])
        self.assertIn("baseline_analysis", result)
        self.assertIn("calibration", result["baseline_analysis"])
        self.assertIn("data_quality", result["baseline_analysis"])

    def test_groq_report_uses_chat_and_metrics_but_excludes_profile_notes(self) -> None:
        self.client.put(
            "/api/profile",
            json={
                "name": "Test Participant",
                "age": 68,
                "language": "en",
                "hobbies": "PRIVATE_HOBBY_NOTE",
                "health_conditions": "PRIVATE_HEALTH_NOTE",
                "concerns": "",
                "prior_report_notes": "",
            },
        )
        self.chat("I like to garden in the morning.")
        self.client.post(
            "/api/task-results",
            json={
                "task_id": "symbol_match",
                "score": 7,
                "max_score": 8,
                "duration_seconds": 20,
                "metrics": {"median_response_ms": 700},
                "consented": True,
            },
        )
        response_text = (
            '{"summary":"Your recorded activity varied across this period.",'
            '"positives":["You completed an activity."],"watch_items":[]}'
        )
        with patch.object(main, "_create_agent_response", return_value=response_text) as groq:
            response = self.client.post(
                f"/api/reports/{self.participant_id}/summary",
                json={},
            )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["summary"].endswith(
            "This is not a diagnosis; discuss persistent changes with a doctor."
        ))
        submitted = str(groq.call_args.args[1])
        self.assertIn("I like to garden", submitted)
        self.assertIn("Symbol matching", submitted)
        self.assertNotIn("PRIVATE_HOBBY_NOTE", submitted)
        self.assertNotIn("PRIVATE_HEALTH_NOTE", submitted)
        with main.database() as connection:
            saved_summary = connection.execute(
                "SELECT summary_json FROM ai_report_summaries WHERE participant_id = ?",
                (self.participant_id,),
            ).fetchone()
        self.assertIsNotNone(saved_summary)
        pdf = self.client.get(f"/api/reports/{self.participant_id}/pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.headers["content-type"], "application/pdf")
        self.assertIn("attachment;", pdf.headers["content-disposition"])
        self.assertTrue(pdf.content.startswith(b"%PDF-"))

        self.client.put("/api/consent/gemini", json={"consented": False})
        with main.database() as connection:
            self.assertIsNone(connection.execute(
                "SELECT summary_json FROM ai_report_summaries WHERE participant_id = ?",
                (self.participant_id,),
            ).fetchone())

    def test_daily_session_has_varied_server_plan_and_accepts_events(self) -> None:
        response = self.client.post("/api/sessions/today")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["session"]["game_order"]), 5)
        self.assertEqual(set(payload["session"]["game_order"]), {
            "pattern_recall",
            "symbol_match",
            "reaction_tap",
            "word_recall",
            "category_fluency",
        })
        self.assertEqual(payload["session"]["next"]["type"], "ask")
        message = self.client.post(
            f"/api/sessions/{payload['session']['date']}/messages",
            json={"text": "I feel calm today.", "client_event_id": str(uuid4())},
        )
        self.assertEqual(message.status_code, 200)
        self.assertEqual(message.json()["session"]["next"]["type"], "game")
        self.assertTrue(message.json()["voice_practice_word"])

    def test_daily_session_rejects_activity_until_current_question_is_answered(self) -> None:
        session = self.client.post("/api/sessions/today").json()
        response = self.client.post(
            f"/api/sessions/{session['session']['date']}/games/{session['session']['game_order'][0]}",
            json={"client_event_id": str(uuid4()), "result": {}},
        )
        self.assertEqual(response.status_code, 409)

    def test_incomplete_daily_session_resumes_and_finishes_all_five_activities(self) -> None:
        session = self.client.post("/api/sessions/today").json()
        session_date = session["session"]["date"]
        session = self.client.post(
            f"/api/sessions/{session_date}/messages",
            json={"text": "I feel well today.", "client_event_id": str(uuid4())},
        ).json()
        self.assertEqual(session["session"]["next"]["type"], "game")

        resumed = self.client.post("/api/sessions/today").json()
        self.assertEqual(resumed["session"]["next"]["type"], "game")
        self.assertEqual(resumed["session"]["step_index"], session["session"]["step_index"])

        completed_games = 0
        while session["session"]["next"]["type"] != "complete":
            next_step = session["session"]["next"]
            if next_step["type"] == "ask":
                session = self.client.post(
                    f"/api/sessions/{session_date}/messages",
                    json={"text": "A little more about my day.", "client_event_id": str(uuid4())},
                ).json()
                next_step = session["session"]["next"]
            self.assertEqual(next_step["type"], "game")
            session = self.client.post(
                f"/api/sessions/{session_date}/games/{next_step['game_id']}",
                json={"client_event_id": str(uuid4()), "result": {"synthetic": True}},
            ).json()
            completed_games += 1

        self.assertEqual(completed_games, 5)
        self.assertEqual(session["session"]["tasks_completed"], 5)
        self.assertEqual(session["session"]["status"], "complete")
        self.assertEqual(
            self.client.post("/api/sessions/today").json()["session"]["status"],
            "complete",
        )

    def test_voice_capture_signal_is_saved_as_neutral_observation_metadata(self) -> None:
        self.consent_to_agent()
        with patch.object(main, "_create_agent_response", return_value="Thanks for sharing."):
            response = self.client.post(
                "/api/chat",
                json={
                    "participant_id": self.participant_id,
                    "language": "en",
                    "text": "river",
                    "consented": True,
                    "voice_duration_ms": 1200,
                    "target_word_match": True,
                    "speech_capture_quality": "matched",
                },
            )
        self.assertEqual(response.status_code, 200)
        with main.database() as connection:
            row = connection.execute(
                """
                SELECT observation_json FROM cognitive_observations
                WHERE participant_id = ? ORDER BY id DESC LIMIT 1
                """,
                (self.participant_id,),
            ).fetchone()
        self.assertIsNotNone(row)
        observation = json.loads(row["observation_json"])
        markers = observation["behavioral_markers"]
        self.assertTrue(markers["target_word_match"])
        self.assertEqual(markers["speech_capture_quality"], "matched")
        self.assertEqual(markers["voice_duration_ms"], 1200)

    def test_pdf_report_requires_authenticated_participant(self) -> None:
        unauthenticated = TestClient(main.app)
        with unauthenticated:
            response = unauthenticated.get(f"/api/reports/{self.participant_id}/pdf")
        self.assertEqual(response.status_code, 401)

    def test_weekly_report_is_date_bounded_and_downloadable(self) -> None:
        self.chat()
        report = self.client.get(
            f"/api/reports/{self.participant_id}/weekly/2026-10-23"
        )
        self.assertEqual(report.status_code, 200)
        payload = report.json()
        self.assertEqual(payload["period_start"], "2026-10-17")
        self.assertEqual(payload["period_end"], "2026-10-23")
        self.assertEqual(len(payload["daily"]), 7)
        pdf = self.client.get(
            f"/api/reports/{self.participant_id}/weekly/2026-10-23/pdf"
        )
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF-"))
        future = self.client.get(
            f"/api/reports/{self.participant_id}/weekly/2999-01-01"
        )
        self.assertEqual(future.status_code, 422)
        invalid = self.client.get(
            f"/api/reports/{self.participant_id}/weekly/not-a-date"
        )
        self.assertEqual(invalid.status_code, 422)

    def test_pdf_handles_marathi_profile_notes_without_silently_corrupting_text(self) -> None:
        self.client.put(
            "/api/profile",
            json={
                "name": "Test Participant",
                "age": 68,
                "language": "mr",
                "hobbies": "बागकाम",
                "health_conditions": "",
                "concerns": "",
                "prior_report_notes": "मागील अहवालाची नोंद",
            },
        )
        response = self.client.get(f"/api/reports/{self.participant_id}/pdf")
        if main._register_unicode_report_font() is None:
            self.assertEqual(response.status_code, 503)
            self.assertIn("Unicode font", response.json()["detail"])
        else:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(b"%PDF-"))
            self.assertIn(b"/FontFile2", response.content)

    def test_delete_removes_profile_messages_and_task_history(self) -> None:
        self.client.post(
            "/api/task-results",
            json={
                "task_id": "spatial_recall",
                "score": 2,
                "max_score": 3,
                "duration_seconds": 12,
                "metrics": {},
                "consented": True,
            },
        )
        response = self.client.delete(f"/api/conversations/{self.participant_id}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        with main.database() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM cognitive_task_results WHERE participant_id = ?",
                    (self.participant_id,),
                ).fetchone()[0],
                0,
            )


if __name__ == "__main__":
    unittest.main()

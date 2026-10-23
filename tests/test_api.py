import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
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

    def consent_to_gemini(self) -> None:
        response = self.client.put("/api/consent/gemini", json={"consented": True})
        self.assertEqual(response.status_code, 200)

    def chat(self, text: str = "I enjoyed gardening today.", language: str = "en"):
        self.consent_to_gemini()
        with patch.object(main, "_create_gemini_response", return_value="That sounds pleasant."):
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

    def test_gemini_chat_requires_explicit_ai_consent_and_persists_response(self) -> None:
        request = {
            "participant_id": self.participant_id,
            "language": "hi",
            "text": "आज दिन अच्छा रहा",
            "consented": True,
        }
        denied = self.client.post("/api/chat", json=request)
        self.assertEqual(denied.status_code, 403)
        self.consent_to_gemini()
        with patch.object(main, "_create_gemini_response", return_value="आपका दिन अच्छा रहा, यह सुनकर खुशी हुई।"):
            response = self.client.post("/api/chat", json=request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("अच्छा रहा", response.json()["assistant_message"]["text"])
        history = self.client.get(f"/api/conversations/{self.participant_id}")
        self.assertEqual([row["sender"] for row in history.json()["messages"]], ["user", "assistant"])

    def test_missing_gemini_key_returns_explicit_error_without_saving_message(self) -> None:
        self.consent_to_gemini()
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
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

    def test_gemini_report_uses_chat_and_metrics_but_excludes_profile_notes(self) -> None:
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
        with patch.object(main, "_create_gemini_response", return_value=response_text) as gemini:
            response = self.client.post(
                f"/api/reports/{self.participant_id}/summary",
                json={},
            )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["summary"].endswith(
            "This is not a diagnosis; discuss persistent changes with a doctor."
        ))
        submitted = str(gemini.call_args.args[1])
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

    def test_pdf_report_requires_authenticated_participant(self) -> None:
        unauthenticated = TestClient(main.app)
        with unauthenticated:
            response = unauthenticated.get(f"/api/reports/{self.participant_id}/pdf")
        self.assertEqual(response.status_code, 401)

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

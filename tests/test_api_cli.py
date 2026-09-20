from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from opspreflight import api
from opspreflight.cli import main as cli_main
from opspreflight.storage import Store
from tests.helpers import plan


class ApiTests(unittest.TestCase):
    def setUp(self):
        api.store = Store()
        self.client = TestClient(api.app)

    def create(self, raw_plan=None):
        response = self.client.post(
            "/v1/analyses",
            json={
                "plan": raw_plan or plan("service", {}, {}),
                "owners": {"resource.test": "team"},
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_health(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_create_and_get(self):
        created = self.create()
        fetched = self.client.get(f"/v1/analyses/{created['analysis_id']}")
        self.assertEqual(fetched.json()["verdict"], "PASS")

    def test_not_found(self):
        self.assertEqual(self.client.get("/v1/analyses/missing").status_code, 404)

    def test_api_key_when_configured(self):
        with patch.dict(os.environ, {"OPSPREFLIGHT_API_KEY": "secret"}):
            self.assertEqual(self.client.post("/v1/analyses", json={}).status_code, 401)

    def test_normal_approval(self):
        created = self.create()
        response = self.client.post(
            f"/v1/analyses/{created['analysis_id']}/approvals",
            json={"actor": "alice", "reason": "reviewed"},
        )
        self.assertEqual(response.status_code, 200)

    def test_block_needs_break_glass(self):
        created = self.create(plan("bucket", {}, {"encrypted": False}))
        url = f"/v1/analyses/{created['analysis_id']}/approvals"
        denied = self.client.post(url, json={"actor": "alice", "reason": "urgent"})
        allowed = self.client.post(
            url,
            json={"actor": "alice", "reason": "incident", "break_glass": True},
        )
        self.assertEqual(denied.status_code, 409)
        self.assertEqual(allowed.status_code, 200)

    def test_outcome_brief_and_timeline(self):
        created = self.create()
        base = f"/v1/analyses/{created['analysis_id']}"
        outcome = self.client.post(base + "/outcomes", json={"actor": "bot", "outcome": "success"})
        brief = self.client.post(base + "/brief", json={"audience": "manager"})
        timeline = self.client.get(base + "/timeline")
        self.assertEqual(outcome.status_code, 200)
        self.assertEqual(brief.json()["verdict"], "PASS")
        self.assertGreaterEqual(len(timeline.json()), 2)


class CliTests(unittest.TestCase):
    def write_plan(self, directory: str, raw_plan) -> Path:
        path = Path(directory) / "plan.json"
        path.write_text(json.dumps(raw_plan), encoding="utf-8")
        return path

    def test_cli_safe_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_plan(directory, plan("service", {}, {}))
            argv = ["opspreflight", "analyze", str(path)]
            with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()) as output:
                cli_main()
            self.assertIn('"verdict": "REVIEW"', output.getvalue())

    def test_cli_block_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_plan(directory, plan("bucket", {}, {"encrypted": False}))
            argv = ["opspreflight", "analyze", str(path), "--fail-on", "block"]
            with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    cli_main()
            self.assertEqual(error.exception.code, 2)

    def test_cli_review_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_plan(directory, plan("service", {}, {}))
            argv = ["opspreflight", "analyze", str(path), "--fail-on", "review"]
            with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    cli_main()
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()


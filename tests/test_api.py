import json
import sys
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.app import AppHandler


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 8765), AppHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def request_json(self, method, path, payload=None, headers=None, raw_body=None):
        conn = HTTPConnection("127.0.0.1", 8765, timeout=5)
        body = raw_body if raw_body is not None else (json.dumps(payload) if payload is not None else None)
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        conn.request(method, path, body=body, headers=req_headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()
        return res.status, json.loads(data)

    def test_bootstrap_session_tap_and_finish(self):
        status, boot = self.request_json("POST", "/api/device-session/bootstrap", {})
        self.assertEqual(status, 201)
        token = boot["device_token"]

        status, session = self.request_json("POST", "/api/sessions", {"device_token": token})
        self.assertEqual(status, 201)
        sid = session["session_id"]

        status, tap = self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token})
        self.assertEqual(status, 200)
        self.assertTrue(tap["is_valid"])
        self.assertGreaterEqual(tap["granted_points"], 10)

        status, monster = self.request_json("GET", "/api/device-session/monster", headers={"X-Device-Token": token})
        self.assertEqual(status, 200)
        self.assertIn(monster["state"], ["eat", "idle"])

        status, fin = self.request_json("POST", f"/api/sessions/{sid}/finish", {"device_token": token})
        self.assertEqual(status, 200)
        self.assertEqual(fin["status"], "finished")

        status, result = self.request_json("GET", f"/api/sessions/{sid}/result")
        self.assertEqual(status, 200)
        self.assertEqual(result["session_id"], sid)

        status, history = self.request_json("GET", "/api/sessions/history?limit=1", headers={"X-Device-Token": token})
        self.assertEqual(status, 200)
        self.assertLessEqual(len(history["sessions"]), 1)

    def test_tap_too_fast_is_invalid(self):
        _, boot = self.request_json("POST", "/api/device-session/bootstrap", {})
        token = boot["device_token"]
        _, session = self.request_json("POST", "/api/sessions", {"device_token": token})
        sid = session["session_id"]

        self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token})
        status, tap2 = self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token})
        self.assertEqual(status, 200)
        self.assertFalse(tap2["is_valid"])
        self.assertEqual(tap2["granted_points"], 0)

    def test_health_and_invalid_json(self):
        status, health = self.request_json("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")

        status, err = self.request_json("POST", "/api/sessions", raw_body="{invalid")
        self.assertEqual(status, 400)
        self.assertEqual(err["error"]["code"], "invalid_json")


if __name__ == "__main__":
    unittest.main()

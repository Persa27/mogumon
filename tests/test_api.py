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
from src.app import MEAL_SESSIONS
from src.app import MONSTER_STATES
from src.app import apply_evolution_if_needed
from src.app import level_from_points
from src.app import level_progress_from_points
from src.app import normalize_monster_state


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
        self.assertIn("player_id", boot)

        status, boot_monster = self.request_json("GET", "/api/device-session/monster", headers={"X-Device-Token": token})
        self.assertEqual(status, 200)
        self.assertEqual(boot_monster["monster_type"], "baby")
        self.assertEqual(boot_monster["evolution_stage"], 0)

        status, session = self.request_json("POST", "/api/sessions", {"device_token": token})
        self.assertEqual(status, 201)
        sid = session["session_id"]

        status, tap = self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token, "food_type": "apple"})
        self.assertEqual(status, 200)
        self.assertTrue(tap["is_valid"])
        self.assertGreaterEqual(tap["granted_points"], 10)
        self.assertEqual(tap["combo_continue_seconds"], 30)
        self.assertEqual(tap["combo_seconds_remaining"], 30)

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

        self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token, "food_type": "apple"})
        status, tap2 = self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token, "food_type": "apple"})
        self.assertEqual(status, 200)
        self.assertFalse(tap2["is_valid"])
        self.assertEqual(tap2["granted_points"], 0)
        self.assertGreater(tap2["combo_seconds_remaining"], 0)

    def test_health_and_invalid_json(self):
        status, health = self.request_json("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")

        status, err = self.request_json("POST", "/api/sessions", raw_body="{invalid")
        self.assertEqual(status, 400)
        self.assertEqual(err["error"]["code"], "invalid_json")

    def test_static_png_assets_are_served(self):
        conn = HTTPConnection("127.0.0.1", 8765, timeout=5)
        conn.request("GET", "/static/monsters/baby/baby/idle/frame1.png")
        res = conn.getresponse()
        body = res.read()
        conn.close()

        self.assertEqual(res.status, 200)
        self.assertEqual(res.getheader("Content-Type"), "image/png")
        self.assertGreater(len(body), 1000)

    def test_admin_history_is_available_without_device_token(self):
        _, boot = self.request_json("POST", "/api/device-session/bootstrap", {})
        token = boot["device_token"]
        _, session = self.request_json("POST", "/api/sessions", {"device_token": token})
        sid = session["session_id"]
        self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token, "food_type": "apple"})
        self.request_json("POST", f"/api/sessions/{sid}/finish", {"device_token": token})

        status, history = self.request_json("GET", "/api/admin/history?limit=5")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(history["sessions"]), 1)
        self.assertIn("total_points", history["sessions"][0])

    def test_level_up_requirement_uses_points(self):
        self.assertEqual(level_from_points(0), 1)
        self.assertEqual(level_from_points(49), 1)
        self.assertEqual(level_from_points(50), 2)
        self.assertEqual(level_from_points(119), 2)
        self.assertEqual(level_from_points(120), 3)
        self.assertEqual(level_progress_from_points(49), (1, 49, 50))
        self.assertEqual(level_progress_from_points(50), (2, 0, 70))
        self.assertEqual(level_progress_from_points(119), (2, 69, 70))
        self.assertEqual(level_progress_from_points(120), (3, 0, 90))

    def test_baby_evolves_to_child_at_level_three(self):
        _, boot = self.request_json("POST", "/api/device-session/bootstrap", {})
        token = boot["device_token"]
        _, session = self.request_json("POST", "/api/sessions", {"device_token": token})
        sid = session["session_id"]

        for _ in range(12):
            status, tap = self.request_json("POST", f"/api/sessions/{sid}/taps", {"device_token": token, "food_type": "apple"})
            self.assertEqual(status, 200)
            session_state = MEAL_SESSIONS[sid]
            session_state["last_tap_at"] = None
            if tap["level"] >= 3:
                break

        monster = MONSTER_STATES[token]
        self.assertEqual(monster["evolution_stage"], 1)
        self.assertEqual(monster["evolution_type"], "draup")
        self.assertEqual(monster["base_food"], "apple")
        self.assertEqual(monster["asset_family"], "child/draup")
        self.assertEqual(monster["display_name"], "ドラップ")

    def test_child_and_mature_evolution_asset_families(self):
        # stage 1 → 2: apple base + apple second → flare_drag
        child_state = normalize_monster_state(
            {
                "evolution_stage": 1,
                "evolution_type": "draup",
                "base_food": "apple",
                "growth_points": level_progress_from_points(0)[0],
                "level": 5,
                "stage_food_counts": {"apple": 6, "carrot": 1, "fish": 1, "broccoli": 0},
                "stage_recent_foods": ["apple", "apple", "carrot"],
                "last_evolution_level": 3,
                "state": "idle",
            }
        )
        child_state["level"] = 6
        self.assertTrue(apply_evolution_if_needed(child_state))
        self.assertEqual(child_state["evolution_type"], "flare_drag")
        self.assertEqual(child_state["evolution_stage"], 2)
        self.assertEqual(child_state["asset_family"], "mature/flare_drag")
        self.assertEqual(child_state["asset_ext"], "png")

        # stage 2 → 3: apple base + apple second → prometheus
        mature_state = normalize_monster_state(
            {
                "evolution_stage": 2,
                "evolution_type": "flare_drag",
                "base_food": "apple",
                "evolution_food_family": "apple",
                "growth_points": 0,
                "level": 9,
                "stage_food_counts": {"apple": 4, "carrot": 1, "fish": 1, "broccoli": 0},
                "stage_recent_foods": ["apple", "apple", "apple"],
                "last_evolution_level": 6,
                "state": "idle",
            }
        )
        mature_state["level"] = 10
        self.assertTrue(apply_evolution_if_needed(mature_state))
        self.assertEqual(mature_state["evolution_type"], "prometheus")
        self.assertEqual(mature_state["evolution_stage"], 3)
        self.assertEqual(mature_state["asset_family"], "final/prometheus")
        self.assertEqual(mature_state["asset_ext"], "png")


if __name__ == "__main__":
    unittest.main()

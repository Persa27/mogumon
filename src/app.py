import json
import random
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

DEVICE_SESSIONS = {}
MEAL_SESSIONS = {}
MONSTER_STATES = {}
MONSTER_TYPES = ["momo", "pafu", "gabu", "fuwa"]

STATE_FILE = Path("data/state.json")


def save_state() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "device_sessions": DEVICE_SESSIONS,
        "meal_sessions": MEAL_SESSIONS,
        "monster_states": MONSTER_STATES,
    }
    STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")


def load_state() -> None:
    if not STATE_FILE.exists():
        return
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    DEVICE_SESSIONS.update(payload.get("device_sessions", {}))
    MEAL_SESSIONS.update(payload.get("meal_sessions", {}))
    MONSTER_STATES.update(payload.get("monster_states", {}))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler: BaseHTTPRequestHandler, status: int, code: str, message: str):
    json_response(handler, status, {"error": {"code": code, "message": message}})


def parse_body(handler: BaseHTTPRequestHandler) -> tuple[dict, bool]:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}, True
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8")), True
    except json.JSONDecodeError:
        return {}, False


def require_token(handler: BaseHTTPRequestHandler, payload: dict | None = None) -> str | None:
    token = payload.get("device_token") if payload else None
    token = token or handler.headers.get("X-Device-Token")
    if not token or token not in DEVICE_SESSIONS:
        error_response(handler, 404, "device_session_not_found", "device session not found")
        return None
    return token


def parse_session_id(path: str) -> str | None:
    parts = path.split("/")
    if len(parts) < 4 or not parts[3]:
        return None
    return parts[3]


class AppHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = urlparse(self.path).path
        payload, ok = parse_body(self)
        if not ok:
            error_response(self, 400, "invalid_json", "request body must be valid JSON")
            return

        if path == "/api/device-session/bootstrap":
            token = str(uuid4())
            monster = random.choice(MONSTER_TYPES)
            DEVICE_SESSIONS[token] = {"created_at": now_iso(), "last_seen_at": now_iso()}
            MONSTER_STATES[token] = {
                "monster_type": monster,
                "level": 1,
                "growth_points": 0,
                "state": "idle",
                "state_asset": f"/static/monsters/{monster}/idle/frame1.svg",
                "updated_at": now_iso(),
            }
            save_state()
            json_response(self, 201, {"device_token": token})
            return

        if path == "/api/sessions":
            token = require_token(self, payload)
            if token is None:
                return
            sid = str(uuid4())
            MEAL_SESSIONS[sid] = {
                "device_token": token,
                "started_at": now_iso(),
                "finished_at": None,
                "combo_count": 0,
                "max_combo": 0,
                "total_points": 0,
                "last_tap_at": None,
            }
            save_state()
            json_response(self, 201, {"session_id": sid})
            return

        if path.startswith("/api/sessions/") and path.endswith("/taps"):
            sid = parse_session_id(path)
            if sid is None:
                error_response(self, 400, "invalid_session_id", "session id is required")
                return
            token = require_token(self, payload)
            if token is None:
                return
            s = MEAL_SESSIONS.get(sid)
            if not s or s["device_token"] != token:
                error_response(self, 404, "session_not_found", "session not found")
                return
            if s["finished_at"] is not None:
                error_response(self, 409, "session_finished", "session already finished")
                return

            now = datetime.now(timezone.utc)
            is_valid = True
            combo = 1
            if s["last_tap_at"]:
                prev = datetime.fromisoformat(s["last_tap_at"])
                diff = (now - prev).total_seconds()
                if diff < 1.8:
                    is_valid = False
                    combo = s["combo_count"]
                elif diff <= 12:
                    combo = s["combo_count"] + 1

            granted = 0
            if is_valid:
                mult = 1.0 if combo <= 2 else 1.2 if combo <= 5 else 1.5
                granted = int(10 * mult)
                s["combo_count"] = combo
                s["max_combo"] = max(s["max_combo"], combo)
                s["total_points"] += granted
                s["last_tap_at"] = now.isoformat()
                m = MONSTER_STATES[token]
                m["growth_points"] += granted
                m["level"] = 1 + m["growth_points"] // 200
                m["state"] = "eat"
                m["state_asset"] = f"/static/monsters/{m['monster_type']}/eat/frame1.svg"
                m["updated_at"] = now_iso()

            save_state()
            json_response(
                self,
                200,
                {
                    "is_valid": is_valid,
                    "combo_count": combo,
                    "granted_points": granted,
                    "total_points": s["total_points"],
                },
            )
            return

        if path.startswith("/api/sessions/") and path.endswith("/finish"):
            sid = parse_session_id(path)
            if sid is None:
                error_response(self, 400, "invalid_session_id", "session id is required")
                return
            token = require_token(self, payload)
            if token is None:
                return
            s = MEAL_SESSIONS.get(sid)
            if not s or s["device_token"] != token:
                error_response(self, 404, "session_not_found", "session not found")
                return
            s["finished_at"] = s["finished_at"] or now_iso()
            m = MONSTER_STATES[token]
            m["state"] = "evolve"
            m["state_asset"] = f"/static/monsters/{m['monster_type']}/evolve/frame1.svg"
            m["updated_at"] = now_iso()
            save_state()
            json_response(self, 200, {"status": "finished"})
            return

        error_response(self, 404, "not_found", "not found")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/":
            path = "/static/index.html"
        if path.startswith("/static/"):
            local_path = path.lstrip("/")
            try:
                with open(local_path, "rb") as f:
                    body = f.read()
                ctype = "text/html; charset=utf-8" if local_path.endswith(".html") else "image/svg+xml"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except FileNotFoundError:
                error_response(self, 404, "static_not_found", "static file not found")
                return

        if path.startswith("/api/sessions/") and path.endswith("/result"):
            sid = parse_session_id(path)
            if sid is None:
                error_response(self, 400, "invalid_session_id", "session id is required")
                return
            s = MEAL_SESSIONS.get(sid)
            if not s:
                error_response(self, 404, "session_not_found", "session not found")
                return
            json_response(
                self,
                200,
                {
                    "session_id": sid,
                    "total_points": s["total_points"],
                    "max_combo": s["max_combo"],
                    "finished_at": s["finished_at"],
                },
            )
            return

        if path == "/api/sessions/history":
            token = require_token(self)
            if token is None:
                return
            limit = int(query.get("limit", [20])[0])
            limit = max(1, min(limit, 100))
            rows = []
            for sid, sess in MEAL_SESSIONS.items():
                if sess["device_token"] == token:
                    rows.append(
                        {
                            "session_id": sid,
                            "started_at": sess["started_at"],
                            "finished_at": sess["finished_at"],
                            "total_points": sess["total_points"],
                            "max_combo": sess["max_combo"],
                        }
                    )
            rows.sort(key=lambda x: x["started_at"], reverse=True)
            json_response(self, 200, {"sessions": rows[:limit]})
            return

        if path == "/api/health":
            json_response(self, 200, {"status": "ok", "devices": len(DEVICE_SESSIONS), "sessions": len(MEAL_SESSIONS)})
            return

        if path == "/api/device-session/monster":
            token = require_token(self)
            if token is None:
                return
            m = MONSTER_STATES[token]
            if m["state"] != "idle":
                current = dict(m)
                m["state"] = "idle"
                m["state_asset"] = f"/static/monsters/{m['monster_type']}/idle/frame1.svg"
                save_state()
                json_response(self, 200, current)
                return
            json_response(self, 200, m)
            return

        error_response(self, 404, "not_found", "not found")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    load_state()
    server = HTTPServer((host, port), AppHandler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

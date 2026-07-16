import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "static"

DEVICE_SESSIONS = {}
MEAL_SESSIONS = {}
MONSTER_STATES = {}
PLAYER_REGISTRY: dict[str, dict] = {}  # player_id -> {obtained_monsters}
FOOD_TYPES = ["apple", "carrot", "fish", "broccoli"]
FOOD_BALANCE = "balance"
COMBO_CONTINUE_SECONDS = 30
COMBO_TOO_FAST_SECONDS = 1.8
BASE_EVOLUTION_LEVEL = 3
FIRST_EVOLUTION_LEVEL = 6
SECOND_EVOLUTION_LEVEL = 10
FOOD_PRIORITY = ["apple", "carrot", "fish", "broccoli"]

# stage 0 → 1: 食事傾向 → 子供フォルダ名
CHILD_BY_FOOD: dict[str, str] = {
    "apple":    "draup",
    "carrot":   "garoron",
    "fish":     "fishul",
    "broccoli": "kororon",
    "balance":  "lumina",
}

# stage 1 → 2: (base_food, second_food) → mature フォルダ名
MATURE_BY_FOODS: dict[tuple[str, str], str] = {
    ("apple",    "apple"):    "flare_drag",
    ("apple",    "carrot"):   "bolt_drag",
    ("apple",    "fish"):     "frost_drag",
    ("apple",    "broccoli"): "magma_rock",
    ("apple",    "balance"):  "shine_drag",
    ("carrot",   "apple"):    "burst_garo",
    ("carrot",   "carrot"):   "bolt_garo",
    ("carrot",   "fish"):     "aqua_garo",
    ("carrot",   "broccoli"): "terra_garo",
    ("carrot",   "balance"):  "holy_garo",
    ("fish",     "apple"):    "steam_fin",
    ("fish",     "carrot"):   "plasma_fin",
    ("fish",     "fish"):     "glacies",
    ("fish",     "broccoli"): "coral_guard",
    ("fish",     "balance"):  "angel_fin",
    ("broccoli", "apple"):    "burn_golem",
    ("broccoli", "carrot"):   "pulse_rock",
    ("broccoli", "fish"):     "splash_terra",
    ("broccoli", "broccoli"): "forest_guard",
    ("broccoli", "balance"):  "rune_golem",
    ("balance",  "apple"):    "flare_eterna",
    ("balance",  "carrot"):   "bolt_eterna",
    ("balance",  "fish"):     "crystal_eterna",
    ("balance",  "broccoli"): "leaf_eterna",
    ("balance",  "balance"):  "eterna",
}

# stage 2 → 3: (base_food, second_food) → final フォルダ名
FINAL_BY_FOODS: dict[tuple[str, str], str] = {
    ("apple",    "apple"):    "prometheus",
    ("apple",    "carrot"):   "indra_drag",
    ("apple",    "fish"):     "agniva",
    ("apple",    "broccoli"): "gaia_drag",
    ("apple",    "balance"):  "sol_dragnir",
    ("carrot",   "apple"):    "ifrit_leo",
    ("carrot",   "carrot"):   "raiden_volf",
    ("carrot",   "fish"):     "kelpie_volt",
    ("carrot",   "broccoli"): "yggdra_beast",
    ("carrot",   "balance"):  "sirius_star",
    ("fish",     "apple"):    "levia_burn",
    ("fish",     "carrot"):   "thunder_kaiser",
    ("fish",     "fish"):     "poseidram",
    ("fish",     "broccoli"): "okeanos",
    ("fish",     "balance"):  "seraph_aqua",
    ("broccoli", "apple"):    "titan_magma",
    ("broccoli", "carrot"):   "thor_terra",
    ("broccoli", "fish"):     "neptune_rock",
    ("broccoli", "broccoli"): "yggdrasil",
    ("broccoli", "balance"):  "chronos_terra",
    ("balance",  "apple"):    "phoenix",
    ("balance",  "carrot"):   "astral_rai",
    ("balance",  "fish"):     "diamond_halo",
    ("balance",  "broccoli"): "eden_spirit",
    ("balance",  "balance"):  "zeus_omega",
}

# 旧フォーマット検出用
_OLD_MONSTER_TYPES = {"momo", "pafu", "gabu", "fuwa"}
_VALID_MATURE_NAMES: set[str] = set(MATURE_BY_FOODS.values())
_VALID_FINAL_NAMES:  set[str] = set(FINAL_BY_FOODS.values())

MONSTER_LABELS: dict[str, str] = {
    # stage 0
    "baby":           "ベビー",
    # stage 1（子供）
    "draup":          "ドラップ",
    "garoron":        "ガロロン",
    "fishul":         "フィシュル",
    "kororon":        "コロロン",
    "lumina":         "ルミナ",
    # stage 2（成熟体）
    "flare_drag":     "フレアドラグ",
    "bolt_drag":      "ボルトドラグ",
    "frost_drag":     "フロストドラグ",
    "magma_rock":     "マグマロック",
    "shine_drag":     "シャインドラグ",
    "burst_garo":     "バーストガロ",
    "bolt_garo":      "ボルトガロ",
    "aqua_garo":      "アクアガロ",
    "terra_garo":     "テラガロ",
    "holy_garo":      "ホーリーガロ",
    "steam_fin":      "スチームフィン",
    "plasma_fin":     "プラズマフィン",
    "glacies":        "グラキエス",
    "coral_guard":    "コーラルガルド",
    "angel_fin":      "エンゼルフィン",
    "burn_golem":     "バーンゴレム",
    "pulse_rock":     "パルスロック",
    "splash_terra":   "スプラッシュテラ",
    "forest_guard":   "フォレストガルド",
    "rune_golem":     "ルーンゴーレム",
    "flare_eterna":   "フレアエテルナ",
    "bolt_eterna":    "ボルトエテルナ",
    "crystal_eterna": "クリスタルエテルナ",
    "leaf_eterna":    "リーフエテルナ",
    "eterna":         "エテルナ",
    # stage 3（完全体）
    "prometheus":     "プロメテウス",
    "indra_drag":     "インドラ・ドラグ",
    "agniva":         "アグニヴァ",
    "gaia_drag":      "ガイアドラグ",
    "sol_dragnir":    "ソル・ドラグニル",
    "ifrit_leo":      "イフリート・レオ",
    "raiden_volf":    "ライデンヴォルフ",
    "kelpie_volt":    "ケルピーヴォルト",
    "yggdra_beast":   "ユグドラビースト",
    "sirius_star":    "シリウス・スター",
    "levia_burn":     "レヴィア・バーン",
    "thunder_kaiser": "サンダーカイザー",
    "poseidram":      "ポセイドラム",
    "okeanos":        "オケアノス",
    "seraph_aqua":    "セラフィ・アクア",
    "titan_magma":    "タイタン・マグマ",
    "thor_terra":     "トール・テラ",
    "neptune_rock":   "ネプチュン・ロック",
    "yggdrasil":      "ユグドラシル",
    "chronos_terra":  "クロノス・テラ",
    "phoenix":        "フェニックス",
    "astral_rai":     "アストラル・ライ",
    "diamond_halo":   "ダイアモンド・ハロー",
    "eden_spirit":    "エデン・スピリット",
    "zeus_omega":     "ゼウス・オメガ",
}

STATE_FILE = Path("data/state.json")


def save_state() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "device_sessions": DEVICE_SESSIONS,
        "meal_sessions": MEAL_SESSIONS,
        "monster_states": MONSTER_STATES,
        "player_registry": PLAYER_REGISTRY,
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
    for token, raw_state in payload.get("monster_states", {}).items():
        MONSTER_STATES[token] = normalize_monster_state(raw_state)
    PLAYER_REGISTRY.update(payload.get("player_registry", {}))


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


def guess_content_type(local_path: str) -> str:
    if local_path.endswith(".html"):
        return "text/html; charset=utf-8"
    if local_path.endswith(".svg"):
        return "image/svg+xml"
    if local_path.endswith(".png"):
        return "image/png"
    if local_path.endswith(".js"):
        return "text/javascript; charset=utf-8"
    if local_path.endswith(".css"):
        return "text/css; charset=utf-8"
    return "application/octet-stream"


def recent_sessions(limit: int) -> list[dict]:
    rows = []
    for sid, sess in MEAL_SESSIONS.items():
        rows.append(
            {
                "session_id": sid,
                "started_at": sess["started_at"],
                "finished_at": sess["finished_at"],
                "total_points": sess["total_points"],
                "max_combo": sess["max_combo"],
                "device_token": sess["device_token"],
            }
        )
    rows.sort(key=lambda x: x["started_at"], reverse=True)
    return rows[:limit]


def level_up_requirement(level: int) -> int:
    return (3 + (level * 2)) * 10


def combo_multiplier(combo: int) -> float:
    if combo >= 10:
        return 5.0
    if combo >= 6:
        return 3.5
    if combo >= 3:
        return 2.0
    return 1.0


def empty_food_counts() -> dict[str, int]:
    return {food: 0 for food in FOOD_TYPES}


def normalize_food_counts(raw: dict | None) -> dict[str, int]:
    counts = empty_food_counts()
    if isinstance(raw, dict):
        for food in FOOD_TYPES:
            try:
                counts[food] = int(raw.get(food, 0) or 0)
            except (TypeError, ValueError):
                counts[food] = 0
    return counts


_VALID_CHILD_FAMILIES: set[str] = set(CHILD_BY_FOOD.values())


_STAGE_PREFIXES = {0: "baby", 1: "child", 2: "mature", 3: "final"}


def current_asset_family(monster_state: dict) -> str:
    stage = monster_state.get("evolution_stage", 0)
    evo = monster_state.get("evolution_type") or ""
    if stage <= 0 or not evo or evo in _OLD_MONSTER_TYPES or evo == "baby":
        return "baby/baby"
    prefix = _STAGE_PREFIXES.get(stage, "baby")
    return f"{prefix}/{evo}"


def current_asset_extension(monster_state: dict) -> str:
    asset_family = current_asset_family(monster_state)
    parts = asset_family.split("/")
    png_path = STATIC_DIR.joinpath("monsters", *parts, "idle", "frame1.png")
    return "png" if png_path.exists() else "svg"


def current_display_name(monster_state: dict) -> str:
    family = current_asset_family(monster_state)
    name = family.split("/")[-1]
    return MONSTER_LABELS.get(name, "モンスター")


def normalize_monster_state(monster_state: dict) -> dict:
    normalized = dict(monster_state)
    growth_points = int(normalized.get("growth_points", 0) or 0)
    level = int(normalized.get("level", level_from_points(growth_points)))
    evolution_stage = int(normalized.get("evolution_stage", 0) or 0)

    # マイグレーション: 旧フォーマット（momo/pafu/gabu/fuwa）を検出してリセット
    evo = normalized.get("evolution_type", "") or ""
    old_detected = (
        normalized.get("monster_type") in _OLD_MONSTER_TYPES
        or evo in _OLD_MONSTER_TYPES
        or any(old in evo for old in _OLD_MONSTER_TYPES)
    )
    if old_detected:
        normalized["evolution_stage"] = 0
        normalized["evolution_type"] = "baby"
        normalized["base_food"] = None
        normalized["evolution_food_family"] = None
        normalized["last_evolution_level"] = 0
        normalized["stage_food_counts"] = empty_food_counts()
        normalized["stage_recent_foods"] = []
        evolution_stage = 0

    normalized["level"] = level
    normalized["growth_points"] = growth_points
    normalized["evolution_stage"] = evolution_stage
    normalized["monster_type"] = "baby"
    normalized["stage_food_counts"] = normalize_food_counts(normalized.get("stage_food_counts"))
    stage_recent_foods = normalized.get("stage_recent_foods")
    if not isinstance(stage_recent_foods, list):
        stage_recent_foods = []
    normalized["stage_recent_foods"] = [f for f in stage_recent_foods if f in FOOD_TYPES][-3:]
    normalized["last_evolution_level"] = int(normalized.get("last_evolution_level", 0) or 0)
    normalized["base_food"] = normalized.get("base_food")

    # 入手済みモンスター一覧の正規化
    current_af = current_asset_family(normalized)
    obtained: list[str] = normalized.get("obtained_monsters") if not old_detected else None  # type: ignore[assignment]
    if not isinstance(obtained, list):
        obtained = []
    obtained = [af for af in obtained if isinstance(af, str)]
    for must in ("baby/baby", current_af):
        if must not in obtained:
            obtained.append(must)
    normalized["obtained_monsters"] = obtained

    normalized["asset_family"] = current_af
    normalized["asset_ext"] = current_asset_extension(normalized)
    normalized["display_name"] = current_display_name(normalized)
    state = normalized.get("state", "idle")
    normalized["state"] = state
    normalized["state_asset"] = f"/static/monsters/{normalized['asset_family']}/{state}/frame1.{normalized['asset_ext']}"
    normalized["updated_at"] = normalized.get("updated_at") or now_iso()
    return normalized


def food_ratio(counts: dict[str, int], food_type: str) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return counts.get(food_type, 0) / total


def dominant_food(counts: dict[str, int], recent_foods: list[str]) -> str:
    highest = max(counts.values()) if counts else 0
    tied = [food for food, value in counts.items() if value == highest]
    if not tied:
        return FOOD_PRIORITY[0]
    if len(tied) == 1:
        return tied[0]
    recent_counts = {food: recent_foods.count(food) for food in tied}
    recent_highest = max(recent_counts.values())
    recent_tied = [food for food in tied if recent_counts[food] == recent_highest]
    for food in FOOD_PRIORITY:
        if food in recent_tied:
            return food
    return recent_tied[0]


def foods_over_threshold(counts: dict[str, int], threshold: float) -> int:
    return sum(1 for food in FOOD_TYPES if food_ratio(counts, food) >= threshold)


def record_food_choice(monster_state: dict, food_type: str) -> None:
    monster_state["stage_food_counts"][food_type] = monster_state["stage_food_counts"].get(food_type, 0) + 1
    monster_state["stage_recent_foods"].append(food_type)
    monster_state["stage_recent_foods"] = monster_state["stage_recent_foods"][-3:]


def reset_stage_food_history(monster_state: dict) -> None:
    monster_state["stage_food_counts"] = empty_food_counts()
    monster_state["stage_recent_foods"] = []


def dominant_food_with_balance(counts: dict[str, int], recent_foods: list[str]) -> str:
    """バランス型（3種以上が15%以上）なら FOOD_BALANCE を返す。それ以外は最多食材。"""
    main_food = dominant_food(counts, recent_foods)
    if food_ratio(counts, main_food) < 0.45 and foods_over_threshold(counts, 0.15) >= 3:
        return FOOD_BALANCE
    return main_food


def apply_evolution_if_needed(monster_state: dict) -> bool:
    evolved = False
    level = monster_state["level"]
    stage = monster_state["evolution_stage"]
    counts = monster_state["stage_food_counts"]
    recent_foods = monster_state["stage_recent_foods"]

    # stage 0 → 1（Lv3）: 赤ちゃん → 子供
    if stage == 0 and level >= BASE_EVOLUTION_LEVEL and monster_state["last_evolution_level"] < BASE_EVOLUTION_LEVEL:
        first_food = dominant_food_with_balance(counts, recent_foods)
        child_family = CHILD_BY_FOOD[first_food]
        monster_state["base_food"] = first_food
        monster_state["evolution_type"] = child_family
        monster_state["evolution_stage"] = 1
        monster_state["last_evolution_level"] = BASE_EVOLUTION_LEVEL
        reset_stage_food_history(monster_state)
        _record_obtained(monster_state, f"child/{child_family}")
        evolved = True

    # stage 1 → 2（Lv6）: 子供 → 成熟体
    if monster_state["evolution_stage"] == 1 and level >= FIRST_EVOLUTION_LEVEL and monster_state["last_evolution_level"] < FIRST_EVOLUTION_LEVEL:
        base_food = monster_state.get("base_food") or "apple"
        second_food = dominant_food_with_balance(counts, recent_foods)
        mature_name = MATURE_BY_FOODS.get((base_food, second_food), "flare_drag")
        monster_state["evolution_food_family"] = second_food
        monster_state["evolution_type"] = mature_name
        monster_state["evolution_stage"] = 2
        monster_state["last_evolution_level"] = FIRST_EVOLUTION_LEVEL
        reset_stage_food_history(monster_state)
        _record_obtained(monster_state, f"mature/{mature_name}")
        evolved = True

    # stage 2 → 3（Lv10）: 成熟体 → 完全体
    if monster_state["evolution_stage"] == 2 and level >= SECOND_EVOLUTION_LEVEL and monster_state["last_evolution_level"] < SECOND_EVOLUTION_LEVEL:
        base_food = monster_state.get("base_food") or "apple"
        second_food = monster_state.get("evolution_food_family") or "apple"
        final_name = FINAL_BY_FOODS.get((base_food, second_food), "prometheus")
        monster_state["evolution_type"] = final_name
        monster_state["evolution_stage"] = 3
        monster_state["last_evolution_level"] = SECOND_EVOLUTION_LEVEL
        reset_stage_food_history(monster_state)
        _record_obtained(monster_state, f"final/{final_name}")
        evolved = True

    if evolved:
        monster_state["asset_family"] = current_asset_family(monster_state)
        monster_state["asset_ext"] = current_asset_extension(monster_state)
        monster_state["display_name"] = current_display_name(monster_state)
    return evolved


def _record_obtained(monster_state: dict, asset_family: str) -> None:
    obtained: list[str] = monster_state.setdefault("obtained_monsters", ["baby/baby"])
    if asset_family not in obtained:
        obtained.append(asset_family)
    player_id = monster_state.get("player_id")
    if player_id and player_id in PLAYER_REGISTRY:
        p_obtained: list[str] = PLAYER_REGISTRY[player_id].setdefault("obtained_monsters", ["baby/baby"])
        if asset_family not in p_obtained:
            p_obtained.append(asset_family)


def level_progress_from_points(points: int) -> tuple[int, int, int]:
    level = 1
    remaining = points

    while remaining >= level_up_requirement(level):
        remaining -= level_up_requirement(level)
        level += 1

    return level, remaining, level_up_requirement(level)


def level_from_points(points: int) -> int:
    level, _, _ = level_progress_from_points(points)
    return level


def monster_payload(monster_state: dict) -> dict:
    monster_state = normalize_monster_state(monster_state)
    level, points_into_level, points_needed_for_next_level = level_progress_from_points(monster_state["growth_points"])
    payload = dict(monster_state)
    payload["level"] = level
    payload["points_into_level"] = points_into_level
    payload["points_needed_for_next_level"] = points_needed_for_next_level
    return payload


class AppHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = urlparse(self.path).path
        payload, ok = parse_body(self)
        if not ok:
            error_response(self, 400, "invalid_json", "request body must be valid JSON")
            return

        if path == "/api/device-session/bootstrap":
            player_id = payload.get("player_id") if payload else None
            if player_id and player_id in PLAYER_REGISTRY:
                inherited_obtained = list(PLAYER_REGISTRY[player_id].get("obtained_monsters", ["baby/baby"]))
            else:
                player_id = str(uuid4())
                inherited_obtained = ["baby/baby"]
                PLAYER_REGISTRY[player_id] = {"obtained_monsters": ["baby/baby"]}
            token = str(uuid4())
            DEVICE_SESSIONS[token] = {"created_at": now_iso(), "last_seen_at": now_iso()}
            MONSTER_STATES[token] = normalize_monster_state(
                {
                "monster_type": "baby",
                "level": 1,
                "growth_points": 0,
                "evolution_stage": 0,
                "evolution_type": "baby",
                "base_food": None,
                "evolution_food_family": None,
                "stage_food_counts": empty_food_counts(),
                "stage_recent_foods": [],
                "last_evolution_level": 0,
                "state": "idle",
                "updated_at": now_iso(),
                "player_id": player_id,
                "obtained_monsters": inherited_obtained,
                }
            )
            save_state()
            json_response(self, 201, {"device_token": token, "player_id": player_id})
            return

        if path == "/api/sessions":
            token = require_token(self, payload)
            if token is None:
                return
            sid = str(uuid4())
            MEAL_SESSIONS[sid] = {
                "device_token": token,
                "player_id": MONSTER_STATES.get(token, {}).get("player_id"),
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
            combo_seconds_remaining = 0.0
            if s["last_tap_at"]:
                prev = datetime.fromisoformat(s["last_tap_at"])
                diff = (now - prev).total_seconds()
                combo_seconds_remaining = max(0.0, COMBO_CONTINUE_SECONDS - diff)
                if diff < COMBO_TOO_FAST_SECONDS:
                    is_valid = False
                    combo = s["combo_count"]
                elif diff <= COMBO_CONTINUE_SECONDS:
                    combo = s["combo_count"] + 1

            granted = 0
            leveled_up = False
            evolved = False
            if is_valid:
                food_type = payload.get("food_type") or "apple"
                if food_type not in FOOD_TYPES:
                    error_response(self, 400, "invalid_food_type", "food_type is invalid")
                    return
                mult = combo_multiplier(combo)
                granted = int(10 * mult)
                s["combo_count"] = combo
                s["max_combo"] = max(s["max_combo"], combo)
                s["total_points"] += granted
                s["last_tap_at"] = now.isoformat()
                combo_seconds_remaining = float(COMBO_CONTINUE_SECONDS)
                m = normalize_monster_state(MONSTER_STATES[token])
                previous_level = m["level"]
                record_food_choice(m, food_type)
                m["growth_points"] += granted
                m["level"] = level_from_points(m["growth_points"])
                leveled_up = m["level"] > previous_level
                evolved = apply_evolution_if_needed(m)
                m["state"] = "eat"
                m["state_asset"] = f"/static/monsters/{m['asset_family']}/eat/frame1.{m['asset_ext']}"
                m["updated_at"] = now_iso()
                m["display_name"] = current_display_name(m)
                MONSTER_STATES[token] = m
                _, points_into_level, points_needed_for_next_level = level_progress_from_points(m["growth_points"])
            else:
                m = normalize_monster_state(MONSTER_STATES[token])
                MONSTER_STATES[token] = m
                _, points_into_level, points_needed_for_next_level = level_progress_from_points(m["growth_points"])

            save_state()
            monster_data = monster_payload(m)
            json_response(
                self,
                200,
                {
                    "is_valid": is_valid,
                    "combo_count": combo,
                    "granted_points": granted,
                    "total_points": s["total_points"],
                    "level": m["level"],
                    "growth_points": m["growth_points"],
                    "points_into_level": points_into_level,
                    "points_needed_for_next_level": points_needed_for_next_level,
                    "leveled_up": leveled_up,
                    "evolved": evolved,
                    "combo_seconds_remaining": combo_seconds_remaining,
                    "combo_continue_seconds": COMBO_CONTINUE_SECONDS,
                    "monster": monster_data,
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
            m = normalize_monster_state(MONSTER_STATES[token])
            m["state"] = "evolve"
            m["state_asset"] = f"/static/monsters/{m['asset_family']}/evolve/frame1.{m['asset_ext']}"
            m["updated_at"] = now_iso()
            MONSTER_STATES[token] = m
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
                self.send_response(200)
                self.send_header("Content-Type", guess_content_type(local_path))
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
            player_id = MONSTER_STATES.get(token, {}).get("player_id")
            limit = int(query.get("limit", [20])[0])
            limit = max(1, min(limit, 100))
            rows = []
            for sid, sess in MEAL_SESSIONS.items():
                match = (
                    (player_id and sess.get("player_id") == player_id)
                    or sess["device_token"] == token
                )
                if match:
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

        if path == "/api/admin/history":
            limit = int(query.get("limit", [20])[0])
            limit = max(1, min(limit, 100))
            json_response(self, 200, {"sessions": recent_sessions(limit)})
            return

        if path == "/api/health":
            json_response(self, 200, {"status": "ok", "devices": len(DEVICE_SESSIONS), "sessions": len(MEAL_SESSIONS)})
            return

        if path == "/api/device-session/monster":
            token = require_token(self)
            if token is None:
                return
            m = normalize_monster_state(MONSTER_STATES[token])
            if m["state"] != "idle":
                current = monster_payload(m)
                m["state"] = "idle"
                m["state_asset"] = f"/static/monsters/{m['asset_family']}/idle/frame1.{m['asset_ext']}"
                MONSTER_STATES[token] = m
                save_state()
                json_response(self, 200, current)
                return
            MONSTER_STATES[token] = m
            json_response(self, 200, monster_payload(m))
            return

        error_response(self, 404, "not_found", "not found")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    load_state()
    server = HTTPServer((host, port), AppHandler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(args.host, args.port)

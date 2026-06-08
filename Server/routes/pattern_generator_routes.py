from pathlib import Path
from typing import List, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, request

from PatternGenerator.engine import (
    CS2PULSE_PRESETS,
    append_weapon_data,
    build_recoil_steps,
    detect_points_and_preview,
)
from Recoil.weapon_data import WeaponData

pattern_generator_bp = Blueprint("pattern_generator_bp", __name__, url_prefix="/api/pattern-generator")
MAX_REMOTE_BYTES = 15 * 1024 * 1024
REPO_ROOT = Path(__file__).resolve().parents[2]


def _available_weapons_for_game(game_id: str):
    game_data = WeaponData.get_game_data(game_id)
    weapons = [
        name
        for name in dir(game_data)
        if not name.startswith("_") and isinstance(getattr(game_data, name), list)
    ]
    weapons.sort()
    return weapons


def _download_remote_media(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are supported.")

    req = Request(url, headers={"User-Agent": "AimSync-PatternGenerator/1.0"})
    with urlopen(req, timeout=12) as resp:
        content_type = (resp.headers.get("Content-Type") or "").lower()
        if content_type and not any(x in content_type for x in ("image/", "gif")):
            raise ValueError(f"URL is not an image/GIF (content-type: {content_type}).")

        data = resp.read(MAX_REMOTE_BYTES + 1)
        if len(data) > MAX_REMOTE_BYTES:
            raise ValueError("Remote file is too large (max 15MB).")
        if not data:
            raise ValueError("Remote file is empty.")
        return data


@pattern_generator_bp.route("/weapons/<game_id>", methods=["GET"])
def list_weapons(game_id: str):
    try:
        return jsonify({"ok": True, "weapons": _available_weapons_for_game(game_id)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@pattern_generator_bp.route("/presets", methods=["GET"])
def list_cs2pulse_presets():
    presets = [
        {"id": preset_id, **meta}
        for preset_id, meta in CS2PULSE_PRESETS.items()
    ]
    return jsonify({"ok": True, "presets": presets})


@pattern_generator_bp.route("/detect", methods=["POST"])
def detect_from_media():
    media = request.files.get("spray_file")
    if media is None or not media.filename:
        return jsonify({"ok": False, "error": "No image/GIF file uploaded."}), 400

    detect_style = request.form.get("detect_style", "generic")
    try:
        payload = detect_points_and_preview(media.read(), detect_style=detect_style)
        return jsonify({"ok": True, **payload})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@pattern_generator_bp.route("/detect-url", methods=["POST"])
def detect_from_url():
    body = request.get_json(silent=True) or {}
    media_url = str(body.get("media_url", "")).strip()
    if not media_url:
        return jsonify({"ok": False, "error": "media_url is required."}), 400

    detect_style = str(body.get("detect_style", "generic"))
    try:
        payload = detect_points_and_preview(_download_remote_media(media_url), detect_style=detect_style)
        return jsonify({"ok": True, **payload})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


def _load_reference_pattern(game_id: str, weapon_name: str) -> List[Tuple[float, float, float]]:
    from Recoil.weapon_data import WeaponData

    game_data = WeaponData.get_game_data(game_id)
    pattern = getattr(game_data, weapon_name, None)
    if not pattern or not isinstance(pattern, list):
        raise ValueError(f"Reference weapon '{weapon_name}' not found for game '{game_id}'.")
    normalized: List[Tuple[float, float, float]] = []
    for entry in pattern:
        if isinstance(entry, (list, tuple)) and len(entry) >= 3:
            normalized.append((float(entry[0]), float(entry[1]), float(entry[2])))
    if not normalized:
        raise ValueError(f"Reference weapon '{weapon_name}' has no pattern steps.")
    return normalized


def _build_preview_payload(body: dict) -> dict:
    game_id = str(body.get("game_id", "cs2")).strip()
    reference_weapon = str(body.get("reference_weapon", "")).strip()
    export_mode = str(body.get("export_mode", "canonical"))
    reference_steps = None
    if export_mode.strip().lower() == "laser_fit":
        if not reference_weapon:
            raise ValueError("reference_weapon is required for laser_fit export mode.")
        reference_steps = _load_reference_pattern(game_id, reference_weapon)
    return build_recoil_steps(
        body.get("points") or [],
        delay_ms=int(body.get("delay_ms", 100)),
        scale_x=float(body.get("scale_x", 1.0)),
        scale_y=float(body.get("scale_y", 1.0)),
        invert_x=bool(body.get("invert_x", True)),
        invert_y=bool(body.get("invert_y", True)),
        export_mode=export_mode,
        reference_steps=reference_steps,
        horizontal_strength=float(body.get("horizontal_strength", 1.0)),
    )


@pattern_generator_bp.route("/preview", methods=["POST"])
def preview_recoil_pattern():
    body = request.get_json(silent=True) or {}
    try:
        payload = _build_preview_payload(body)
        return jsonify({"ok": True, **payload})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@pattern_generator_bp.route("/append", methods=["POST"])
def append_weapon_pattern():
    body = request.get_json(silent=True) or {}
    game_id = str(body.get("game_id", "cs2")).strip()
    weapon_name = str(body.get("weapon_name", "")).strip()
    overwrite = bool(body.get("overwrite", True))

    if not weapon_name:
        return jsonify({"ok": False, "error": "weapon_name is required."}), 400

    try:
        preview = _build_preview_payload(body)
        result = append_weapon_data(
            REPO_ROOT,
            game_id,
            weapon_name,
            preview["steps_seconds"],
            overwrite=overwrite,
        )
        from Config.config_manager import load_config, save_config
        from Recoil.recoil import reset_pattern_state

        config = load_config()
        config.setdefault('recoil_game_settings', {})['weapon'] = weapon_name
        config['recoil_mode'] = 'CS2'
        save_config(config)
        reset_pattern_state()
        return jsonify({"ok": True, **result, "steps": len(preview["steps_seconds"])})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

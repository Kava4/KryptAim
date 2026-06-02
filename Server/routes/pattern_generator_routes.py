from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, request

from PatternGenerator.engine import (
    build_recoil_steps,
    detect_points_and_preview,
)
from Recoil.weapon_data import WeaponData

pattern_generator_bp = Blueprint("pattern_generator_bp", __name__, url_prefix="/api/pattern-generator")
MAX_REMOTE_BYTES = 15 * 1024 * 1024


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


@pattern_generator_bp.route("/detect", methods=["POST"])
def detect_from_media():
    media = request.files.get("spray_file")
    if media is None or not media.filename:
        return jsonify({"ok": False, "error": "No image/GIF file uploaded."}), 400

    try:
        payload = detect_points_and_preview(media.read())
        return jsonify({"ok": True, **payload})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@pattern_generator_bp.route("/detect-url", methods=["POST"])
def detect_from_url():
    body = request.get_json(silent=True) or {}
    media_url = str(body.get("media_url", "")).strip()
    if not media_url:
        return jsonify({"ok": False, "error": "media_url is required."}), 400

    try:
        payload = detect_points_and_preview(_download_remote_media(media_url))
        return jsonify({"ok": True, **payload})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@pattern_generator_bp.route("/preview", methods=["POST"])
def preview_recoil_pattern():
    body = request.get_json(silent=True) or {}
    points = body.get("points") or []
    try:
        payload = build_recoil_steps(
            points,
            delay_ms=int(body.get("delay_ms", 90)),
            scale_x=float(body.get("scale_x", 1.0)),
            scale_y=float(body.get("scale_y", 1.0)),
            invert_x=bool(body.get("invert_x", True)),
            invert_y=bool(body.get("invert_y", True)),
            export_mode=str(body.get("export_mode", "canonical")),
        )
        return jsonify({"ok": True, **payload})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@pattern_generator_bp.route("/append", methods=["POST"])
def append_weapon_pattern():
    return jsonify({
        "ok": False,
        "error": "Direct Game Engine writes are disabled. Use generated pattern text in Recoil Lab.",
    }), 410

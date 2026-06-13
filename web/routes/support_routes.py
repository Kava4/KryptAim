"""Feedback and support-code routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.core.feedback import send_support_code, send_user_feedback

support_bp = Blueprint('support', __name__)


def _form_value(*keys: str) -> str:
    data = request.get_json(silent=True) or {}
    for key in keys:
        value = request.form.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
        json_value = data.get(key)
        if json_value is not None and str(json_value).strip():
            return str(json_value).strip()
    return ''


@support_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    message = _form_value('feedback_message', 'message')
    contact = _form_value('contact_info', 'contact')
    bug_type = _form_value('bug_type', 'type') or 'Bug Report'
    result = send_user_feedback(message=message, contact=contact, feedback_type=bug_type)
    code = 200 if result.get('success') else 400
    return jsonify(result), code


@support_bp.route('/api/support/code', methods=['POST'])
def submit_support_code_route():
    provider = _form_value('provider')
    code = _form_value('code', 'support_code')
    contact = _form_value('contact_info', 'contact')
    result = send_support_code(provider=provider, code=code, contact=contact)
    code = 200 if result.get('success') else 400
    return jsonify(result), code

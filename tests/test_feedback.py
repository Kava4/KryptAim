"""Feedback relay to Cloud API."""

from __future__ import annotations

from app.core import feedback as feedback_mod


def test_send_user_feedback_requires_message():
    result = feedback_mod.send_user_feedback(message='   ')
    assert result['success'] is False


def test_send_support_code_maps_provider(monkeypatch):
    captured = {}

    def fake_send(**kwargs):
        captured.update(kwargs)
        return {'success': True}

    monkeypatch.setattr(feedback_mod, 'send_user_feedback', fake_send)
    result = feedback_mod.send_support_code(provider='giftmecrypto', code='ABC-123', contact='user#1')
    assert result['success'] is True
    assert captured['feedback_type'] == 'GiftMeCrypto'
    assert 'ABC-123' in captured['message']


def test_send_user_feedback_forwards_to_cloud(monkeypatch):
    payload = {}

    def fake_cloud(data):
        payload.update(data)
        return {'success': True}, None

    monkeypatch.setattr(feedback_mod, '_cloud_submit_feedback', fake_cloud)
    monkeypatch.setattr(feedback_mod, 'get_hwid', lambda: 'hw-1')
    result = feedback_mod.send_user_feedback(
        message='Test bug',
        contact='discord',
        feedback_type='Bug Report',
    )
    assert result['success'] is True
    assert payload['message'] == 'Test bug'
    assert payload['type'] == 'Bug Report'
    assert payload['hwid'] == 'hw-1'

"""Trigger always on must enable triggerbot without profile Auto Trigger toggle."""


def test_auto_trigger_enabled_with_always_on_flag():
    from AI.Engine.capture import ScreenCapture
    from AI.Engine.settings import AiSettings
    from AI.Engine.trigger import TriggerController

    settings = AiSettings()
    settings.toggles['Auto Trigger'] = False
    ctrl = TriggerController(settings, ScreenCapture())
    assert ctrl._auto_trigger_enabled({'ai_trigger_always_on': True})

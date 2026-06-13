"""Trigger bot logic tests."""

from __future__ import annotations

import time
import unittest
from unittest.mock import patch

from app.ai.trigger import TriggerController, trigger_armed, trigger_weapon_allowed
from app.ai.types import Prediction


class TriggerArmedTests(unittest.TestCase):
    @patch('app.ai.trigger.makcu_manager')
    def test_requires_ai_and_trigger_enabled(self, makcu) -> None:
        makcu.get_button_state.return_value = True
        self.assertFalse(trigger_armed({'ai_enabled': False, 'ai_trigger_enabled': True}))
        self.assertFalse(trigger_armed({'ai_enabled': True, 'ai_trigger_enabled': False}))

    @patch('app.ai.trigger.makcu_manager')
    def test_always_on(self, makcu) -> None:
        makcu.get_button_state.return_value = False
        config = {
            'ai_enabled': True,
            'ai_trigger_enabled': True,
            'ai_trigger_always_on': True,
        }
        self.assertTrue(trigger_armed(config))

    @patch('app.ai.trigger.makcu_manager')
    def test_hold_key(self, makcu) -> None:
        makcu.get_button_state.side_effect = lambda k: k == 'M5'
        config = {
            'ai_enabled': True,
            'ai_trigger_enabled': True,
            'ai_trigger_always_on': False,
            'ai_trigger_keybind': 'M5',
        }
        self.assertTrue(trigger_armed(config))


class TriggerWeaponGateTests(unittest.TestCase):
    def test_blocks_when_recoil_on(self) -> None:
        config = {'ai_trigger_spray_block': True, 'recoil_enabled': True}
        self.assertFalse(trigger_weapon_allowed(config))

    def test_allows_when_recoil_off(self) -> None:
        config = {'ai_trigger_spray_block': True, 'recoil_enabled': False}
        self.assertTrue(trigger_weapon_allowed(config))


class TriggerControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trigger = TriggerController()
        self.config = {
            'ai_enabled': True,
            'ai_trigger_enabled': True,
            'ai_trigger_always_on': True,
            'ai_trigger_radius_px': 8,
            'ai_trigger_delay_ms': 0,
            'ai_trigger_cooldown_ms': 0,
            'ai_trigger_min_conf': 0.35,
            'ai_trigger_click_hold_ms': 20,
        }

    @patch('app.ai.trigger.makcu_manager')
    def test_blocks_when_spray_recoil_on(self, makcu) -> None:
        config = dict(self.config)
        config['recoil_enabled'] = True
        config['ai_trigger_spray_block'] = True
        target = Prediction(confidence=0.9, image_dist=2.0)
        self.trigger.evaluate(config, armed=True, targets=[target])
        makcu.click.assert_not_called()
        self.assertEqual(self.trigger.last_block_reason, 'spray_recoil')

    @patch('app.ai.trigger.makcu_manager')
    def test_fires_when_target_in_zone(self, makcu) -> None:
        target = Prediction(confidence=0.9, image_dist=4.0)
        self.trigger.evaluate(self.config, armed=True, targets=[target])
        makcu.click.assert_called_once_with('LMB', hold_ms=20)

    @patch('app.ai.trigger.makcu_manager')
    def test_skips_outside_radius(self, makcu) -> None:
        target = Prediction(confidence=0.9, image_dist=20.0)
        self.trigger.evaluate(self.config, armed=True, targets=[target])
        makcu.click.assert_not_called()
        self.assertEqual(self.trigger.last_block_reason, 'outside_zone')

    @patch('app.ai.trigger.makcu_manager')
    def test_respects_cooldown(self, makcu) -> None:
        config = dict(self.config)
        config['ai_trigger_cooldown_ms'] = 5000
        target = Prediction(confidence=0.9, image_dist=2.0)
        self.trigger.evaluate(config, armed=True, targets=[target])
        self.trigger.evaluate(config, armed=True, targets=[target])
        self.assertEqual(makcu.click.call_count, 1)
        self.assertEqual(self.trigger.last_block_reason, 'cooldown')

    @patch('app.ai.trigger.makcu_manager')
    def test_delay_before_fire(self, makcu) -> None:
        config = dict(self.config)
        config['ai_trigger_delay_ms'] = 50
        target = Prediction(confidence=0.9, image_dist=2.0)
        self.trigger.evaluate(config, armed=True, targets=[target])
        makcu.click.assert_not_called()
        self.assertEqual(self.trigger.last_block_reason, 'delay')
        self.trigger._in_zone_since_ms = time.perf_counter() * 1000.0 - 100.0
        self.trigger.evaluate(config, armed=True, targets=[target])
        makcu.click.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)

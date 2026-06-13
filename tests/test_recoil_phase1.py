"""Recoil engine tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.recoil import engine as recoil_engine
from app.recoil.weapon_data import WeaponData


class Phase1RecoilTests(unittest.TestCase):
    def setUp(self) -> None:
        recoil_engine.reset_recoil_state()
        recoil_engine.invalidate_config_cache()
        recoil_engine._keybind_was_pressed = False

    @patch('app.recoil.engine.time.sleep')
    @patch('app.recoil.engine.makcu_manager')
    def test_cs2_first_step_ak_at_baseline_sens(self, makcu, _sleep) -> None:
        makcu.get_button_state.side_effect = lambda b: b == 'LMB'
        config = {
            'recoil_enabled': True,
            'recoil_keybind': 'M4',
            'recoil_mode': 'CS2',
            'recoil_require_rmb': False,
            'recoil_return_crosshair': False,
            'recoil_randomisation': False,
            'recoil_x_control': 100,
            'recoil_y_control': 100,
            'recoil_cs2_settings': {
                'cs2_weapon': 'assault_rifle',
                'cs2_sensitivity': 1.25,
            },
        }
        with patch.object(recoil_engine, 'get_config', return_value=config):
            recoil_engine.run_recoil()
        makcu.move_mouse_smoothly.assert_called_once()
        args = makcu.move_mouse_smoothly.call_args[0]
        self.assertEqual(args[0], 0.0)
        self.assertEqual(args[1], 10.0)

    @patch('app.recoil.engine.time.sleep')
    @patch('app.recoil.engine.makcu_manager')
    def test_sensitivity_scales_at_baseline(self, makcu, _sleep) -> None:
        makcu.get_button_state.side_effect = lambda b: b == 'LMB'
        config = {
            'recoil_enabled': True,
            'recoil_keybind': 'M4',
            'recoil_mode': 'CS2',
            'recoil_require_rmb': False,
            'recoil_return_crosshair': False,
            'recoil_randomisation': False,
            'recoil_x_control': 100,
            'recoil_y_control': 100,
            'recoil_cs2_settings': {
                'cs2_weapon': 'assault_rifle',
                'cs2_sensitivity': 2.5,
            },
        }
        with patch.object(recoil_engine, 'get_config', return_value=config):
            recoil_engine.run_recoil()
        _y = makcu.move_mouse_smoothly.call_args[0][1]
        self.assertAlmostEqual(_y, 5.0)

    @patch('app.recoil.engine.time.sleep')
    @patch('app.recoil.engine.makcu_manager')
    def test_rmb_gate_pauses_without_reset(self, makcu, _sleep) -> None:
        makcu.get_button_state.side_effect = lambda b: b == 'LMB'
        config = {
            'recoil_enabled': True,
            'recoil_keybind': 'M4',
            'recoil_mode': 'CS2',
            'recoil_require_rmb': True,
            'recoil_return_crosshair': False,
            'recoil_randomisation': False,
            'recoil_x_control': 100,
            'recoil_y_control': 100,
            'recoil_cs2_settings': {
                'cs2_weapon': 'assault_rifle',
                'cs2_sensitivity': 1.25,
            },
        }
        recoil_engine._shot_count = 3
        recoil_engine._lmb_was_pressed = True
        with patch.object(recoil_engine, 'get_config', return_value=config):
            recoil_engine.run_recoil()
        makcu.move_mouse_smoothly.assert_not_called()
        self.assertEqual(recoil_engine._shot_count, 3)

    def test_smooth_weapon_pattern_lengths(self) -> None:
        data = WeaponData()
        self.assertEqual(len(data.assault_rifle), 29)
        self.assertEqual(len(data.m4a1s), 18)
        self.assertEqual(data.assault_rifle[0], (0, 10, 0.1))


if __name__ == '__main__':
    unittest.main(verbosity=2)

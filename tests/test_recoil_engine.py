import unittest
from unittest.mock import patch

from Recoil import recoil as recoil_module
from Recoil.hotkeys import is_hotkey_binding_active, set_hotkey_binding_active


class RecoilEngineTests(unittest.TestCase):
    def setUp(self):
        set_hotkey_binding_active(False)
        recoil_module.reset_master_toggle_hotkey()
        recoil_module._state.update({
            'step_index': 0,
            'next_step_at': 0.0,
            'compensation_x': 0.0,
            'compensation_y': 0.0,
            'was_active': False,
            'ghub_delay_armed': False,
            'ghub_pending_dx': 0.0,
            'ghub_pending_dy': 0.0,
            'active_weapon': None,
            'active_mode': None,
        })

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil.load_config')
    def test_disabled_recoil_sleeps_without_move(self, load_config, _sleep):
        load_config.return_value = {'recoil_enabled': False}
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_not_called()

    @patch('Recoil.recoil.makcu_manager')
    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_simple_mode_moves_while_lmb_held(self, load_config, button_held, _sleep, makcu_manager):
        makcu_manager.is_hardware.return_value = False
        makcu_manager.is_connected.return_value = False
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'simple',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_simple_settings': {'recoil_x': 0, 'recoil_y': 5, 'recoil_delay': 50},
            'recoil_speed_control': 100,
        }
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_called_once()
        args = move.call_args[0]
        self.assertEqual(args[1], 0)
        self.assertEqual(args[2], 5)

    @patch('Recoil.recoil.save_config')
    @patch('Recoil.recoil.load_config')
    def test_master_toggle_skipped_while_binding_hotkey(self, load_config, save_config):
        load_config.return_value = {
            'recoil_enabled': True,
            'global_toggle_hotkey': 'M5',
            'recoil_keybind': 'M5',
        }
        set_hotkey_binding_active(True)
        with patch.object(recoil_module._toggle_tracker, 'is_pressed_once', return_value=True) as pressed:
            recoil_module._handle_master_toggle_hotkey()
        pressed.assert_not_called()
        save_config.assert_not_called()

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_game_mode_scales_by_sensitivity(self, load_config, button_held, _sleep):
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'CS2',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_game_settings': {'weapon': 'ak47', 'sensitivity': 1.0, 'recoil_loop': False},
            'active_game': 'cs2',
        }
        recoil_module._state['step_index'] = 0
        recoil_module._state['next_step_at'] = 0.0
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_called_once_with(load_config.return_value, 0, 10)

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_famas_uses_standard_game_step_timing(self, load_config, button_held, _sleep):
        from Recoil.weapon_data import WeaponData

        famas_step0 = WeaponData.get_game_data('cs2').famas[0]
        exp_x = int(round(famas_step0[0]))
        exp_y = int(round(famas_step0[1]))
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'CS2',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_game_settings': {
                'weapon': 'famas',
                'sensitivity': 1.0,
                'recoil_loop': False,
                'timing_scale': 1.0,
            },
            'active_game': 'cs2',
        }
        recoil_module._state['next_step_at'] = 0.0
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
            move.assert_called_once_with(load_config.return_value, exp_x, exp_y)
            self.assertFalse(recoil_module._state['ghub_delay_armed'])

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_famas_uses_famas_pattern_not_ak(self, load_config, button_held, _sleep):
        from Recoil.weapon_data import WeaponData

        famas_step0 = WeaponData.get_game_data('cs2').famas[0]
        exp_x = int(round(famas_step0[0]))
        exp_y = int(round(famas_step0[1]))
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'CS2',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_game_settings': {
                'weapon': 'famas',
                'sensitivity': 1.0,
                'recoil_loop': False,
                'timing_scale': 1.0,
            },
            'active_game': 'cs2',
        }
        recoil_module._state['active_weapon'] = 'ak47'
        recoil_module._state['active_mode'] = 'CS2'
        recoil_module._state['step_index'] = 5
        recoil_module._state['next_step_at'] = 0.0
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
            move.assert_called_once_with(load_config.return_value, exp_x, exp_y)
            self.assertEqual(recoil_module._state['step_index'], 1)
            self.assertFalse(recoil_module._state['ghub_delay_armed'])

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_simple_mode_ignores_weapon_dropdown(self, load_config, button_held, _sleep):
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'simple',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_game_settings': {'weapon': 'ak47', 'sensitivity': 1.0},
            'recoil_simple_settings': {'recoil_x': 0, 'recoil_y': 3, 'recoil_delay': 50},
            'recoil_speed_control': 100,
        }
        recoil_module._state['next_step_at'] = 0.0
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_called_once_with(load_config.return_value, 0, 3)

    @patch('Recoil.recoil.time.sleep')
    @patch('Recoil.recoil._fire_button_held')
    @patch('Recoil.recoil.load_config')
    def test_simple_mode_stays_simple_with_non_ak_weapon(self, load_config, button_held, _sleep):
        button_held.side_effect = lambda key: key == 'LMB'
        load_config.return_value = {
            'recoil_enabled': True,
            'recoil_mode': 'simple',
            'recoil_require_rmb': False,
            'recoil_safety_features_enabled': False,
            'recoil_input_method': 'software',
            'recoil_game_settings': {'weapon': 'famas', 'sensitivity': 1.0, 'recoil_loop': False},
            'recoil_simple_settings': {'recoil_x': 0, 'recoil_y': 3, 'recoil_delay': 50},
            'recoil_speed_control': 100,
        }
        recoil_module._state['next_step_at'] = 0.0
        with patch.object(recoil_module, '_move_mouse') as move:
            recoil_module.run_recoil()
        move.assert_called_once_with(load_config.return_value, 0, 3)
        self.assertEqual(recoil_module._state.get('active_mode'), 'simple')


if __name__ == '__main__':
    unittest.main(verbosity=2)

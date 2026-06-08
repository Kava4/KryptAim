import unittest

from AI.Engine.movement.executor import MovementExecutor, scale_in_game_sensitivity, _PATH_TO_MODE
from AI.Engine.movement.windmouse import wind_mouse_path
from AI.Engine.settings import AiSettings


class MovementTests(unittest.TestCase):
    def test_path_mode_mapping(self):
        settings = AiSettings()
        settings.dropdowns['Movement Path'] = 'Cubic Bezier'
        mode = MovementExecutor.resolve_mode({}, settings)
        self.assertEqual(mode, 'bezier')

    def test_config_mode_override(self):
        settings = AiSettings()
        mode = MovementExecutor.resolve_mode({'ai_aim_mode': 'smooth'}, settings)
        self.assertEqual(mode, 'smooth')

    def test_windmouse_generates_steps(self):
        path = wind_mouse_path(80.0, 40.0)
        self.assertGreater(len(path), 0)

    def test_in_game_sens_scales(self):
        dx, dy = scale_in_game_sensitivity(100, 50, {'ai_in_game_sens': 1.3})
        self.assertNotEqual(dx, 0)


if __name__ == '__main__':
    unittest.main()

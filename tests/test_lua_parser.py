import unittest

from Recoil.lua_parser import parse_lua_xyd_table


class LuaXydParserTests(unittest.TestCase):
    def test_parse_famas_table(self):
        sample = (
            'famas = { { x = 0, y = 0, d = 2 }, { x = -1, y = 1, d = 7 }, { x = 2, y = -1, d = 10 } }'
        )
        pattern = parse_lua_xyd_table(sample, weapon_name='famas')
        self.assertEqual(len(pattern), 3)
        self.assertEqual(pattern[0], (0.0, 0.0, 0.002))
        self.assertEqual(pattern[1], (-1.6, 1.6, 0.007))
        self.assertEqual(pattern[2], (3.2, -1.6, 0.01))


if __name__ == '__main__':
    unittest.main(verbosity=2)

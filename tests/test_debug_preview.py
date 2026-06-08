import unittest

import numpy as np

from AI.Engine.debug_preview import DebugFrameStore, render_debug_jpeg
from AI.Engine.settings import AiSettings
from AI.Engine.target import TargetSelector


class DebugPreviewTests(unittest.TestCase):
    def test_store_roundtrip(self):
        store = DebugFrameStore()
        store.set_jpeg(b'fake')
        self.assertEqual(store.get_jpeg(), b'fake')

    def test_render_jpeg_with_cv2(self):
        try:
            import cv2  # noqa: F401
        except ImportError:
            self.skipTest('opencv not installed')
        settings = AiSettings()
        selector = TargetSelector(settings)
        bgr = np.zeros((320, 320, 3), dtype=np.uint8)
        output = np.zeros((1, 5, 10), dtype=np.float32)
        output[0, 0, 0] = 160
        output[0, 1, 0] = 160
        output[0, 2, 0] = 40
        output[0, 3, 0] = 80
        output[0, 4, 0] = 0.9
        jpeg = render_debug_jpeg(
            bgr,
            output,
            image_size=320,
            num_classes=1,
            class_names={0: 'CT'},
            settings=settings,
            selector=selector,
            player_label='',
            head_label='',
            player_y_offset=0,
            min_confidence=0.25,
            active_target=None,
        )
        self.assertIsNotNone(jpeg)
        self.assertTrue(jpeg.startswith(b'\xff\xd8'))


if __name__ == '__main__':
    unittest.main()

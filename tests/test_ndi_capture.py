"""NDI crop math (no cyndilib required)."""

from __future__ import annotations

import unittest

import numpy as np

from app.ai.capture.backend import center_square_crop


class NdiCropTests(unittest.TestCase):
    def test_center_square_crop_maps_region(self) -> None:
        bgr = np.zeros((1080, 1920, 3), dtype=np.uint8)
        ctx = center_square_crop(
            bgr,
            main_pc_width=1920,
            main_pc_height=1080,
            image_size=640,
        )
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.bgr.shape, (640, 640, 3))
        self.assertEqual(ctx.region.width, 1080)
        self.assertEqual(ctx.region.height, 1080)
        self.assertEqual(ctx.region.left, 420)
        self.assertEqual(ctx.region.top, 0)
        self.assertEqual(ctx.crosshair_x, 960)
        self.assertEqual(ctx.crosshair_y, 540)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""PyInstaller import hooks — forces bundling of torch/ultralytics (imported from build_app)."""

import unittest  # noqa: F401 — required by torch/ultralytics in frozen builds

import cv2  # noqa: F401
import matplotlib  # noqa: F401 — required by ultralytics.utils.plotting in frozen builds
import numpy  # noqa: F401
import onnxruntime  # noqa: F401
import torch  # noqa: F401
import torchvision  # noqa: F401
import ultralytics  # noqa: F401
from ultralytics import YOLO  # noqa: F401

import cyndilib  # noqa: F401

import AI.Vendor.yolo_cuda.detection_core  # noqa: F401
import makcu  # noqa: F401
import makcu.errors  # noqa: F401
import Recoil.recoil  # noqa: F401
import Recoil.games.cs2  # noqa: F401

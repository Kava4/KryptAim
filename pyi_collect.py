"""PyInstaller — force heavy deps into the frozen bundle."""

import unittest  # noqa: F401 — torch/ultralytics need it in frozen builds

import cv2  # noqa: F401
import cyndilib  # noqa: F401
import flask  # noqa: F401
import makcu  # noqa: F401
import makcu.errors  # noqa: F401
import matplotlib  # noqa: F401
import numpy  # noqa: F401
import onnxruntime  # noqa: F401
import torch  # noqa: F401
import torchvision  # noqa: F401
import ultralytics  # noqa: F401
from ultralytics import YOLO  # noqa: F401

import app.ai.engine  # noqa: F401
import app.recoil.engine  # noqa: F401
import web.app  # noqa: F401

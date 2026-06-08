import unittest
from unittest.mock import patch

from AI.Engine.inference_backend import (
    backend_for_model,
    normalize_backend,
    resolve_onnx_providers,
    uses_ultralytics,
)


class InferenceBackendTests(unittest.TestCase):
    def test_normalize_backend_default(self):
        with patch('AI.Engine.inference_backend.probe_gpu_status', return_value={'cuda_available': False}):
            self.assertEqual(normalize_backend(None), 'directml')
        with patch('AI.Engine.inference_backend.probe_gpu_status', return_value={'cuda_available': True}):
            self.assertEqual(normalize_backend(None), 'cuda_ultralytics')
        self.assertEqual(normalize_backend('cuda_ultralytics'), 'cuda_ultralytics')

    def test_backend_for_pt(self):
        with patch('AI.Engine.inference_backend._torch_cuda_available', return_value=True):
            self.assertEqual(backend_for_model('model.pt', 'cuda_ultralytics'), 'cuda_ultralytics')

    def test_backend_for_onnx_cuda_ultralytics(self):
        with patch('AI.Engine.inference_backend._torch_cuda_available', return_value=True):
            self.assertEqual(backend_for_model('cs2_640.onnx', 'cuda_ultralytics'), 'cuda_ultralytics')
        with patch('AI.Engine.inference_backend.cuda_inference_available', return_value=False):
            self.assertEqual(backend_for_model('cs2_640.onnx', 'cuda_ultralytics'), 'directml')
        with patch('AI.Engine.inference_backend._torch_cuda_available', return_value=False):
            with patch('AI.Engine.inference_backend._ort_cuda_available', return_value=True):
                self.assertEqual(backend_for_model('cs2_640.onnx', None), 'cuda_ultralytics')

    def test_backend_for_onnx_explicit_cuda_onnx(self):
        with patch('AI.Engine.inference_backend._torch_cuda_available', return_value=True):
            self.assertEqual(backend_for_model('cs2_640.onnx', 'cuda_onnx'), 'cuda_onnx')

    def test_uses_ultralytics(self):
        self.assertTrue(uses_ultralytics('cuda_ultralytics'))
        self.assertFalse(uses_ultralytics('directml'))

    def test_resolve_cpu_providers(self):
        attempts = resolve_onnx_providers('cpu')
        self.assertTrue(attempts)
        self.assertEqual(attempts[0], ['CPUExecutionProvider'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

import numpy as np
from pathlib import Path
from typing import Tuple, Optional

try:
    import tensorflow as tf
    tflite = tf.lite
except ImportError:
    try:
        import tflite_runtime.interpreter as tflite
    except ImportError:
        raise ImportError("Neither tensorflow nor tflite_runtime is installed. Please install tensorflow-cpu or tflite-runtime.")


class Model:
    def __init__(self, model_path: Path):
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.interpreter = tflite.Interpreter(model_path=str(model_path))
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        self.is_quantized = self.input_details['dtype'] in [np.int8, np.uint8]
        
        print(f"Model loaded: {model_path}")
        print(f"Input: {self.input_details['shape']}, dtype: {self.input_details['dtype']}")
        print(f"Output: {self.output_details['shape']}, dtype: {self.output_details['dtype']}")
        print(f"Quantized: {self.is_quantized}")
    
    def _get_output_probs(self, input_data: np.ndarray) -> np.ndarray:
        input_dtype = self.input_details['dtype']
        if input_dtype == np.int8:
            if input_data.dtype == np.uint8:
                input_data = input_data.astype(np.int8) - 128
        elif input_dtype == np.uint8:
            if input_data.dtype != np.uint8:
                input_data = np.clip(input_data, 0, 255).astype(np.uint8)
        elif input_dtype == np.float32:
            if input_data.dtype != np.float32:
                input_data = input_data.astype(np.float32)
        
        self.interpreter.set_tensor(self.input_details['index'], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details['index'])[0]
        
        if self.output_details['dtype'] == np.int8:
            scale = self.output_details['quantization'][0]
            zero_point = self.output_details['quantization'][1]
            output = (output.astype(np.float32) - zero_point) * scale
        elif self.output_details['dtype'] == np.uint8:
            scale = self.output_details['quantization'][0]
            zero_point = self.output_details['quantization'][1]
            output = (output.astype(np.float32) - zero_point) * scale
        
        if output.min() < 0 or output.sum() > 1.1:
            exp_output = np.exp(output - np.max(output))
            output = exp_output / exp_output.sum()
        
        return output
    
    def predict(self, input_data: np.ndarray) -> Tuple[int, float]:
        output = self._get_output_probs(input_data)
        class_idx = int(np.argmax(output))
        confidence = float(output[class_idx])
        return class_idx, confidence
    
    def predict_with_probs(self, input_data: np.ndarray) -> Tuple[int, float, np.ndarray]:
        output = self._get_output_probs(input_data)
        class_idx = int(np.argmax(output))
        confidence = float(output[class_idx])
        return class_idx, confidence, output


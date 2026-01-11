import cv2
import numpy as np
from typing import Tuple, Optional


def preprocess(
    frame: np.ndarray, 
    target_size: Tuple[int, int] = (224, 224),
    quantized: Optional[bool] = None
) -> np.ndarray:
    resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    
    if quantized is True:
        output = rgb.astype(np.uint8)
    elif quantized is False:
        output = rgb.astype(np.float32)
    else:
        output = rgb.astype(np.uint8)
    
    return np.expand_dims(output, axis=0)


def preprocess_mobilenetv2(frame: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) - 127.5) / 127.5
    return np.expand_dims(normalized, axis=0)



"""
Preprocessing functions for training data.
Handles MobileNetV2 normalization: [-1, 1] range.
"""

import numpy as np
import tensorflow as tf


def preprocess_mobilenetv2(image):
    """
    Preprocess image for MobileNetV2.
    Normalizes to [-1, 1] range.
    
    Args:
        image: Image tensor (uint8, 0-255)
    
    Returns:
        Normalized image tensor (float32, -1 to 1)
    """
    # Convert to float32
    image = tf.cast(image, tf.float32)
    
    # Normalize to [-1, 1]: (pixel / 127.5) - 1.0
    image = (image / 127.5) - 1.0
    
    return image



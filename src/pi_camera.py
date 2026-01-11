import cv2
import threading
import time
from queue import Queue, Full, Empty
from typing import Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PiCamera:
    def __init__(
        self,
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        target_fps: int = 10,
        queue_size: int = 2
    ):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.frame_interval = 1.0 / max(1, target_fps)
        self.queue = Queue(maxsize=queue_size)
        self.running = False
        self.capture_thread = None
        
        self.use_picamera2 = False
        self.picam2 = None
        self.cap = None
        
        try:
            from picamera2 import Picamera2
            self.use_picamera2 = True
            logger.info("Using picamera2")
        except ImportError:
            logger.warning("picamera2 not available, falling back to OpenCV")
            self.use_picamera2 = False
        
        self._init_camera()
        logger.info(f"Pi Camera initialized: {width}x{height} @ {target_fps} FPS")
    
    def _init_camera(self):
        if self.use_picamera2:
            try:
                from picamera2 import Picamera2
                self.picam2 = Picamera2()
                
                camera_config = self.picam2.create_preview_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"},
                    controls={"FrameRate": self.target_fps}
                )
                self.picam2.configure(camera_config)
                self.picam2.start()
                logger.info("picamera2 initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize picamera2: {e}")
                logger.info("Falling back to OpenCV")
                self.use_picamera2 = False
                self._init_opencv()
        else:
            self._init_opencv()
    
    def _init_opencv(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.camera_index}")
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info("OpenCV camera initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenCV camera: {e}")
    
    def _capture_loop(self):
        last_frame_time = time.time()
        
        while self.running:
            try:
                elapsed = time.time() - last_frame_time
                if elapsed < self.frame_interval:
                    time.sleep(self.frame_interval - elapsed)
                last_frame_time = time.time()
                
                if self.use_picamera2:
                    frame = self.picam2.capture_array()
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    ret, frame = self.cap.read()
                    if not ret:
                        logger.warning("Failed to read frame from camera")
                        time.sleep(0.1)
                        continue
                
                try:
                    self.queue.put_nowait(frame)
                except Full:
                    try:
                        _ = self.queue.get_nowait()
                        self.queue.put_nowait(frame)
                    except Exception:
                        pass
                        
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Camera capture thread started")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.running:
            self.start()
        
        try:
            frame = self.queue.get(timeout=1.0)
            return True, frame
        except Empty:
            return False, None
    
    def release(self):
        logger.info("Releasing camera...")
        self.running = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        if self.use_picamera2 and self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
            except Exception as e:
                logger.warning(f"Error closing picamera2: {e}")
        elif self.cap:
            try:
                self.cap.release()
            except Exception as e:
                logger.warning(f"Error releasing OpenCV camera: {e}")
        
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Empty:
                break
        
        logger.info("Camera released")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


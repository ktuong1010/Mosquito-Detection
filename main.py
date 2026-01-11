import sys
import time
import signal
import logging
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    MODEL_PATH, DB_PATH, LOG_DIR, CLASSES, CONFIDENCE_THRESHOLD,
    INPUT_SIZE, TARGET_LATENCY_MS, MAX_LATENCY_MS, UPDATE_INTERVAL,
    OLED_ENABLED, DB_ENABLED, LOG_LEVEL,
    PI_CAMERA_INDEX, PI_CAMERA_WIDTH, PI_CAMERA_HEIGHT, PI_CAMERA_TARGET_FPS,
    NO_MOSQUITO_CLASS_IDX, MIN_DETECTION_INTERVAL, MIN_MOSQUITO_CONFIDENCE_MARGIN
)

from src.pi_camera import PiCamera as Camera
from src.preprocessing import preprocess
from src.model import Model
from src.oled_display import OLEDDisplay
from src.database import Database

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "detection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DetectionSystem:
    def __init__(self):
        self.running = False
        
        logger.info("Initializing components...")
        self.model = Model(MODEL_PATH)
        
        logger.info(f"Using Raspberry Pi Camera Module 3 (CSI)")
        self.camera = Camera(
            camera_index=PI_CAMERA_INDEX,
            width=PI_CAMERA_WIDTH,
            height=PI_CAMERA_HEIGHT,
            target_fps=PI_CAMERA_TARGET_FPS
        )
        
        self.display = OLEDDisplay() if OLED_ENABLED else None
        self.database = Database(DB_PATH) if DB_ENABLED else None
        
        self.detections = defaultdict(lambda: {'quantity': 0, 'confidence': 0.0})
        self.current_species = None
        self.current_confidence = 0.0
        self.frame_count = 0
        self.fps_start = time.time()
        self.fps = 0.0
        self.latencies = []
        self.last_update = time.time()
        self.last_detection_time = {species: 0.0 for species in CLASSES}
        
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        
        logger.info("System initialized")
    
    def _shutdown(self, signum, frame):
        logger.info("Shutting down...")
        self.running = False
    
    def _update_fps(self):
        self.frame_count += 1
        elapsed = time.time() - self.fps_start
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start = time.time()
    
    def _update_components(self):
        now = time.time()
        if now - self.last_update < UPDATE_INTERVAL:
            return
        
        if self.display:
            self.display.show_detection_results(
                species=self.current_species,
                confidence=self.current_confidence,
                fps=self.fps,
                stats=None
            )
        
        if self.database:
            self.database.log(self.detections, self.fps)
            if int(now) % 60 == 0:
                self.database.update_summary()
        
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        max_latency = max(self.latencies) if self.latencies else 0
        
        logger.info(f"FPS: {self.fps:.1f} | Latency: {avg_latency:.1f}ms (max: {max_latency:.1f}ms)")
        
        for species in CLASSES:
            qty = self.detections[species]['quantity']
            conf = self.detections[species]['confidence']
            if qty > 0:
                logger.info(f"  {species}: {qty} detections, avg confidence: {conf:.2f}")
        
        for species in CLASSES:
            self.detections[species] = {'quantity': 0, 'confidence': 0.0}
        self.latencies.clear()
        self.last_update = now
    
    def run(self):
        logger.info("Starting detection system...")
        logger.info(f"Target: {PI_CAMERA_TARGET_FPS} FPS, Latency < {TARGET_LATENCY_MS}ms")
        logger.info("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(0.01)
                    continue
                
                start_time = time.time()
                is_quantized = self.model.is_quantized if hasattr(self.model, 'is_quantized') else None
                input_data = preprocess(frame, INPUT_SIZE, quantized=is_quantized)
                
                class_idx, confidence = self.model.predict(input_data)
                latency_ms = (time.time() - start_time) * 1000
                
                self.latencies.append(latency_ms)
                if latency_ms > MAX_LATENCY_MS:
                    logger.warning(f"High latency: {latency_ms:.1f}ms")
                
                species = CLASSES[class_idx]
                current_time = time.time()
                
                if class_idx == NO_MOSQUITO_CLASS_IDX:
                    self.current_species = None
                    self.current_confidence = 0.0
                elif confidence >= CONFIDENCE_THRESHOLD:
                    time_since_last = current_time - self.last_detection_time[species]
                    
                    if time_since_last >= MIN_DETECTION_INTERVAL:
                        self.detections[species]['quantity'] += 1
                        old_conf = self.detections[species]['confidence']
                        count = self.detections[species]['quantity']
                        self.detections[species]['confidence'] = (
                            (old_conf * (count - 1) + confidence) / count if count > 1 else confidence
                        )
                        self.last_detection_time[species] = current_time
                        logger.debug(f"Counted {species} detection (time since last: {time_since_last:.1f}s)")
                    else:
                        logger.debug(f"Skipped {species} detection (only {time_since_last:.1f}s since last)")
                    
                    self.current_species = species
                    self.current_confidence = confidence
                else:
                    self.current_species = None
                    self.current_confidence = confidence
                
                self._update_fps()
                self._update_components()
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        logger.info("Cleaning up...")
        self.camera.release()
        if self.display:
            self.display.clear()
        logger.info("Shutdown complete")


def main():
    try:
        system = DetectionSystem()
        system.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


import sys
import time
import signal
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MODEL_PATH, CLASSES, CONFIDENCE_THRESHOLD,
    INPUT_SIZE,
    PI_CAMERA_INDEX, PI_CAMERA_WIDTH, PI_CAMERA_HEIGHT, PI_CAMERA_TARGET_FPS,
    NO_MOSQUITO_CLASS_IDX, MIN_DETECTION_INTERVAL, MIN_MOSQUITO_CONFIDENCE_MARGIN
)

from src.pi_camera import PiCamera as Camera
from src.preprocessing import preprocess
from src.model import Model
from src.oled_display import OLEDDisplay

class DemoSystem:
    def __init__(self):
        print("=" * 70)
        print("Mosquito Detection System - DEMO MODE")
        print("=" * 70)
        print()
        
        print("Loading model...")
        self.model = Model(MODEL_PATH)
        print(f"  Model: {MODEL_PATH}")
        print(f"  Classes: {', '.join(CLASSES)}")
        print(f"  Threshold: {CONFIDENCE_THRESHOLD:.2f}")
        print()
        
        print("Initializing Pi Camera...")
        self.camera = Camera(
            camera_index=PI_CAMERA_INDEX,
            width=PI_CAMERA_WIDTH,
            height=PI_CAMERA_HEIGHT,
            target_fps=PI_CAMERA_TARGET_FPS
        )
        print(f"  Camera: {PI_CAMERA_WIDTH}x{PI_CAMERA_HEIGHT} @ {PI_CAMERA_TARGET_FPS} FPS")
        print()
        
        print("Initializing OLED...")
        try:
            self.oled = OLEDDisplay()
            if self.oled.oled is not None:
                print("  OLED ready")
            else:
                print("  OLED not available")
        except Exception as e:
            print(f"  OLED: {e}")
            self.oled = None
        print()
        
        self.running = True
        self.stats = defaultdict(lambda: {'count': 0, 'total_confidence': 0.0})
        self.frame_count = 0
        self.start_time = time.time()
        self.last_detection_time = {species: 0.0 for species in CLASSES}
        self.last_display_time = 0.0
        self.last_display_species = None
        self.last_display_confidence = None
        
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        
        print("=" * 70)
        print("Starting detection... Press Ctrl+C to stop")
        print("=" * 70)
        print()
    
    def _shutdown(self, signum, frame):
        self.running = False
    
    def run(self, update_interval=3.0):
        last_update = time.time()
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                start_time = time.time()
                is_quantized = getattr(self.model, 'is_quantized', None)
                input_data = preprocess(frame, INPUT_SIZE, quantized=is_quantized)
                
                # Get all class probabilities
                class_idx, confidence, all_probs = self.model.predict_with_probs(input_data)
                inference_time = (time.time() - start_time) * 1000
                
                current_time = time.time()
                
                # Compare confidence of Aedes and Culex (exclude No_Mosquito)
                aedes_conf = float(all_probs[0])  # Aedes
                culex_conf = float(all_probs[1])  # Culex
                no_mosquito_conf = float(all_probs[2])  # No_Mosquito
                
                # Find species with highest confidence (excluding No_Mosquito)
                if aedes_conf >= culex_conf:
                    best_species = "Aedes"
                    best_confidence = aedes_conf
                    best_class_idx = 0
                else:
                    best_species = "Culex"
                    best_confidence = culex_conf
                    best_class_idx = 1
                
                # Only process if best confidence is above threshold (0.72)
                if best_confidence >= CONFIDENCE_THRESHOLD:
                    time_since_last = current_time - self.last_detection_time[best_species]
                    
                    if time_since_last >= MIN_DETECTION_INTERVAL:
                        self.stats[best_species]['count'] += 1
                        self.stats[best_species]['total_confidence'] += best_confidence
                        self.last_detection_time[best_species] = current_time
                        print(f" {best_species:<15} {best_confidence:.3f} | Aedes:{aedes_conf:.3f} Culex:{culex_conf:.3f} | {inference_time:.1f}ms | COUNTED")
                    else:
                        print(f" {best_species:<15} {best_confidence:.3f} | Aedes:{aedes_conf:.3f} Culex:{culex_conf:.3f} | {inference_time:.1f}ms | (duplicate)")
                    
                    # Update display with best species
                    self.last_display_species = best_species
                    self.last_display_confidence = best_confidence
                    self.last_display_time = current_time
                else:
                    print(f" Best: {best_species} {best_confidence:.3f} | Aedes:{aedes_conf:.3f} Culex:{culex_conf:.3f} (below threshold)")
                    # Keep last display for 1 second
                    if current_time - self.last_display_time < 1.0:
                        # Still show last detection
                        pass
                    else:
                        # Clear display after 1 second
                        self.last_display_species = None
                        self.last_display_confidence = None
                
                self.frame_count += 1
                
                # Update OLED display (keep showing for 1 second)
                if self.oled:
                    elapsed = time.time() - self.start_time
                    fps = self.frame_count / elapsed if elapsed > 0 else 0
                    # Show last detection if within 1 second, otherwise show current
                    if self.last_display_species and (current_time - self.last_display_time < 1.0):
                        self.oled.show_detection_results(
                            species=self.last_display_species,
                            confidence=self.last_display_confidence,
                            fps=fps,
                            stats=self.stats
                        )
                    else:
                        # Show "No detection" or keep last
                        self.oled.show_detection_results(
                            species=None,
                            confidence=None,
                            fps=fps,
                            stats=self.stats
                        )
                
                now = time.time()
                if now - last_update >= update_interval:
                    elapsed = time.time() - self.start_time
                    fps = self.frame_count / elapsed if elapsed > 0 else 0
                    
                    print("\n" + "=" * 70)
                    print(f"{'Species':<15} {'Count':<10} {'Avg Conf':<12} {'Status':<15}")
                    print("-" * 70)
                    
                    for species in CLASSES:
                        if species == "No_Mosquito":
                            continue
                        count = self.stats[species]['count']
                        if count > 0:
                            avg_conf = self.stats[species]['total_confidence'] / count
                            status = "✓ DETECTED" if avg_conf >= CONFIDENCE_THRESHOLD else "✗ LOW"
                            print(f"{species:<15} {count:<10} {avg_conf:<12.3f} {status:<15}")
                        else:
                            print(f"{species:<15} {'0':<10} {'0.000':<12} {'-':<15}")
                    
                    print("-" * 70)
                    print(f"FPS: {fps:.1f} | Frames: {self.frame_count} | Time: {elapsed:.1f}s")
                    print("=" * 70 + "\n")
                    
                    last_update = now
                    for species in CLASSES:
                        self.stats[species] = {'count': 0, 'total_confidence': 0.0}
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        except Exception as e:
            print(f"\n\nError: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        print("\n" + "=" * 70)
        print("Final Statistics:")
        print("=" * 70)
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        print(f"{'Species':<15} {'Total':<10} {'Avg Conf':<12}")
        print("-" * 70)
        
        for species in CLASSES:
            if species == "No_Mosquito":
                continue
            count = self.stats[species]['count']
            if count > 0:
                avg_conf = self.stats[species]['total_confidence'] / count
                print(f"{species:<15} {count:<10} {avg_conf:<12.3f}")
            else:
                print(f"{species:<15} {'0':<10} {'0.000':<12}")
        
        print("-" * 70)
        print(f"Total frames: {self.frame_count} | FPS: {fps:.2f} | Time: {elapsed:.1f}s")
        print("=" * 70)
        
        print("\nReleasing camera...")
        self.camera.release()
        
        if self.oled:
            self.oled.clear()
            print("OLED cleared")
        
        print("Done!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Mosquito Detection Demo")
    parser.add_argument("--interval", type=float, default=3.0, help="Update interval (seconds)")
    
    args = parser.parse_args()
    
    try:
        demo = DemoSystem()
        demo.run(update_interval=args.interval)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

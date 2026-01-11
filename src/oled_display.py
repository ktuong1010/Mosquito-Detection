"""OLED Display module for showing mosquito detection results."""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import board
    import digitalio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_ssd1306
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    logger.warning("OLED libraries not available")

OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_ADDRESS = 0x3C


class OLEDDisplay:
    def __init__(self, width: int = OLED_WIDTH, height: int = OLED_HEIGHT, address: int = OLED_ADDRESS):
        self.width = width
        self.height = height
        self.address = address
        self.oled = None
        self.image = None
        self.draw = None
        self.font = None
        
        if not OLED_AVAILABLE:
            logger.warning("OLED libraries not available, OLED display disabled")
            return
        
        try:
            import board
            from PIL import Image, ImageDraw, ImageFont
            import adafruit_ssd1306
            
            i2c = board.I2C()
            self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=address)
            self.oled.fill(0)
            self.oled.show()
            
            self.image = Image.new("1", (self.oled.width, self.oled.height))
            self.draw = ImageDraw.Draw(self.image)
            self.font = ImageFont.load_default()
            
            logger.info("OLED display initialized successfully")
            self.show_startup_message()
        except Exception as e:
            logger.error(f"Failed to initialize OLED display: {e}")
            logger.warning("Continuing without OLED display...")
            self.oled = None
    
    def _get_font_size(self, text: str) -> tuple:
        if self.font is None:
            return (0, 0)
        left, top, right, bottom = self.font.getbbox(text)
        return (right - left, bottom - top)
    
    def show_startup_message(self):
        if self.oled is None:
            return
        
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        
        text_lines = ["TinyML", "Mosquito", "Detection"]
        y_offset = 10
        
        for line in text_lines:
            font_width, font_height = self._get_font_size(line)
            x = (self.width - font_width) // 2
            self.draw.text((x, y_offset), line, font=self.font, fill=255)
            y_offset += font_height + 5
        
        self.oled.image(self.image)
        self.oled.show()
    
    def show_detection_results(
        self, 
        species: Optional[str] = None,
        confidence: Optional[float] = None,
        fps: float = 0.0,
        stats: Optional[Dict[str, Dict]] = None
    ):
        if self.oled is None:
            return
        
        try:
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            
            y_pos = 0
            line_height = 12
            
            fps_text = f"FPS: {fps:.1f}"
            self.draw.text((0, y_pos), fps_text, font=self.font, fill=255)
            y_pos += line_height
            
            if species and confidence is not None:
                species_short = species[:6]  # Shorten for display
                conf_text = f"{species_short}: {confidence:.0%}"
                self.draw.text((0, y_pos), conf_text, font=self.font, fill=255)
                y_pos += line_height
            else:
                self.draw.text((0, y_pos), "No detection", font=self.font, fill=255)
                y_pos += line_height
            
            if stats:
                total_detected = sum(s.get('count', 0) for s in stats.values())
                if total_detected > 0:
                    summary_text = f"Total: {total_detected}"
                    self.draw.text((0, y_pos), summary_text, font=self.font, fill=255)
                    y_pos += line_height
                    
                    for sp, data in stats.items():
                        count = data.get('count', 0)
                        if count > 0:
                            species_short = sp[:3]  # AED, CUL, etc.
                            text = f"{species_short}:{count}"
                            self.draw.text((0, y_pos), text, font=self.font, fill=255)
                            y_pos += line_height
                            if y_pos >= self.height - line_height:
                                break
            
            self.oled.image(self.image)
            self.oled.show()
            
        except Exception as e:
            logger.error(f"Error updating OLED display: {e}")
    
    def clear(self):
        if self.oled is None:
            return
        try:
            self.oled.fill(0)
            self.oled.show()
        except Exception as e:
            logger.error(f"Error clearing OLED display: {e}")



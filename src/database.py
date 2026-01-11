import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class Database:
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                species TEXT NOT NULL,
                confidence REAL NOT NULL,
                fps REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hourly_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_hour TEXT NOT NULL UNIQUE,
                aedes_count INTEGER DEFAULT 0,
                culex_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                avg_confidence REAL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def log(self, detections: Dict[str, Dict], fps: float):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for species, data in detections.items():
            quantity = data.get('quantity', 0)
            confidence = data.get('confidence', 0.0)
            
            for _ in range(quantity):
                cursor.execute("""
                    INSERT INTO detections (timestamp, species, confidence, fps)
                    VALUES (?, ?, ?, ?)
                """, (timestamp, species, confidence, fps))
        
        conn.commit()
        conn.close()
    
    def update_summary(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00:00")
        
        cursor.execute("""
            SELECT species, COUNT(*) as count, AVG(confidence) as avg_conf
            FROM detections
            WHERE datetime(timestamp) >= datetime(?)
            GROUP BY species
        """, (current_hour,))
        
        results = cursor.fetchall()
        
        counts = {'Aedes': 0, 'Culex': 0}
        total = 0
        total_conf = 0.0
        
        for species, count, avg_conf in results:
            if species in counts:
                counts[species] = count
                total += count
                total_conf += avg_conf * count if avg_conf else 0
        
        avg_confidence = total_conf / total if total > 0 else 0.0
        
        cursor.execute("""
            INSERT OR REPLACE INTO hourly_summary 
            (date_hour, aedes_count, culex_count, total_count, avg_confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (current_hour, counts['Aedes'], counts['Culex'], total, avg_confidence))
        
        conn.commit()
        conn.close()


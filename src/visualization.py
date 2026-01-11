import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class DensityAnalyzer:
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def get_weekly_data(self, days: int = 7) -> Dict[str, List[Tuple[str, int]]]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                species,
                COUNT(*) as count
            FROM detections
            WHERE datetime(timestamp) >= datetime(?)
            GROUP BY DATE(timestamp), species
            ORDER BY date ASC
        """, (start_date.strftime("%Y-%m-%d %H:%M:%S"),))
        
        results = cursor.fetchall()
        conn.close()
        
        data = {
            'Aedes': [],
            'Culex': [],
            'Total': []
        }
        
        daily_totals = {}
        
        for date_str, species, count in results:
            if species in data:
                data[species].append((date_str, count))
            
            if date_str not in daily_totals:
                daily_totals[date_str] = 0
            daily_totals[date_str] += count
        
        for date_str, total in sorted(daily_totals.items()):
            data['Total'].append((date_str, total))
        
        return data
    
    def get_statistics(self, days: int = 7) -> Dict[str, Dict]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                species,
                COUNT(*) as total_count,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence
            FROM detections
            WHERE datetime(timestamp) >= datetime(?)
            GROUP BY species
        """, (start_date.strftime("%Y-%m-%d %H:%M:%S"),))
        
        results = cursor.fetchall()
        conn.close()
        
        stats = {}
        for species, count, avg_conf, min_conf, max_conf in results:
            stats[species] = {
                'total_count': count,
                'avg_confidence': avg_conf or 0.0,
                'min_confidence': min_conf or 0.0,
                'max_confidence': max_conf or 0.0
            }
        
        return stats


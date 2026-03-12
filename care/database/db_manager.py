import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage all database operations"""
    
    def __init__(self, db_path="medical_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Consultations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symptoms TEXT,
                diagnosis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Medication reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                med_name TEXT NOT NULL,
                dosage TEXT NOT NULL,
                time TEXT NOT NULL,
                time_label TEXT,
                duration_days INTEGER,
                duration_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Prescriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                analysis TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Health tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                condition_type TEXT,
                initial_description TEXT,
                initial_image_path TEXT,
                initial_analysis TEXT,
                followup_days TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Tracking follow-ups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracking_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id INTEGER,
                followup_image_path TEXT,
                followup_description TEXT,
                followup_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tracking_id) REFERENCES health_tracking (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        conn.commit()
        conn.close()
    
    def add_reminder(self, user_id: int, med_name: str, dosage: str, 
                    time: str, time_label: str, duration_days: Optional[int], 
                    duration_label: str) -> int:
        """Add a new reminder and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders 
            (user_id, med_name, dosage, time, time_label, duration_days, duration_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, med_name, dosage, time, time_label, duration_days, duration_label))
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added reminder {reminder_id} for user {user_id}")
        return reminder_id
    
    def get_user_reminders(self, user_id: int) -> List[Dict]:
        """Get all active reminders for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, med_name, dosage, time, time_label, 
                   duration_days, duration_label, created_at
            FROM reminders
            WHERE user_id = ? AND is_active = 1
            ORDER BY time
        """, (user_id,))
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                'id': row[0], 'med_name': row[1], 'dosage': row[2],
                'time': row[3], 'time_label': row[4], 'duration_days': row[5],
                'duration_label': row[6], 'created_at': row[7]
            })
        conn.close()
        return reminders
    
    def get_all_active_reminders(self) -> List[Dict]:
        """Get all active reminders"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, med_name, dosage, time, time_label, 
                   duration_days, duration_label
            FROM reminders WHERE is_active = 1
        """)
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                'id': row[0], 'user_id': row[1], 'med_name': row[2],
                'dosage': row[3], 'time': row[4], 'time_label': row[5],
                'duration_days': row[6], 'duration_label': row[7]
            })
        conn.close()
        return reminders
    
    def deactivate_reminder(self, reminder_id: int) -> bool:
        """Deactivate a reminder"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def save_consultation(self, user_id: int, symptoms: str, diagnosis: str):
        """Save a symptom consultation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO consultations (user_id, symptoms, diagnosis)
            VALUES (?, ?, ?)
        """, (user_id, symptoms, diagnosis))
        conn.commit()
        conn.close()
    
    def save_prescription(self, user_id: int, analysis: str, image_path: str = None):
        """Save prescription analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prescriptions (user_id, analysis, image_path)
            VALUES (?, ?, ?)
        """, (user_id, analysis, image_path))
        conn.commit()
        conn.close()
    
    def add_health_tracking(self, user_id: int, condition_type: str, 
                           initial_description: str, initial_image_path: str,
                           initial_analysis: str, followup_days: str) -> int:
        """Add new health tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO health_tracking 
            (user_id, condition_type, initial_description, initial_image_path, 
             initial_analysis, followup_days)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, condition_type, initial_description, initial_image_path,
              initial_analysis, followup_days))
        tracking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return tracking_id
    
    def get_user_trackings(self, user_id: int, active_only: bool = False) -> List[Dict]:
        """Get all health trackings for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, condition_type, initial_analysis, created_at, is_active
            FROM health_tracking WHERE user_id = ?
        """
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        trackings = []
        for row in cursor.fetchall():
            trackings.append({
                'id': row[0], 'condition_type': row[1],
                'initial_analysis': row[2], 'created_at': row[3], 'is_active': row[4]
            })
        conn.close()
        return trackings
    
    def deactivate_tracking(self, tracking_id: int, user_id: int) -> bool:
        """Deactivate a health tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE health_tracking SET is_active = 0
            WHERE id = ? AND user_id = ?
        """, (tracking_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

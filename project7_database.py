import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, date

class Database:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'class_recordings'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.conn_params)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def test_connection(self):
        """Test database connection"""
        conn = self.get_connection()
        if conn:
            conn.close()
            return True
        return False
    
    def create_recording(self, faculty_id, faculty_name, subject):
        """Create new recording entry"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO recordings (faculty_id, faculty_name, subject, date, start_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            now = datetime.now()
            cursor.execute(query, (
                faculty_id,
                faculty_name,
                subject,
                now.date(),
                now.time(),
                'recording'
            ))
            
            recording_id = cursor.fetchone()[0]
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return recording_id
            
        except Exception as e:
            print(f"Error creating recording: {e}")
            return None
    
    def update_recording_status(self, recording_id, status, video_path, duration):
        """Update recording status after completion"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE recordings
                SET status = %s, video_path = %s, duration = %s, end_time = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (
                status,
                video_path,
                duration,
                datetime.now().time(),
                recording_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error updating recording: {e}")
            return False
    
    def update_recording_transcript(self, recording_id, transcript_path, transcript_text):
        """Update recording with transcript"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE recordings
                SET transcript_path = %s, transcript_text = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (transcript_path, transcript_text, recording_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error updating transcript: {e}")
            return False
    
    def update_recording_summary(self, recording_id, summary, key_points):
        """Update recording with AI summary"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE recordings
                SET summary = %s, key_points = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (summary, key_points, recording_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error updating summary: {e}")
            return False
    
    def add_transcript_segment(self, recording_id, start_time, end_time, text, confidence):
        """Add transcript segment"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO transcripts (recording_id, timestamp_start, timestamp_end, text, confidence)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (recording_id, start_time, end_time, text, confidence))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error adding transcript segment: {e}")
            return False
    
    def get_recording(self, recording_id):
        """Get recording by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM recordings WHERE id = %s"
            cursor.execute(query, (recording_id,))
            
            recording = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if recording:
                return dict(recording)
            return None
            
        except Exception as e:
            print(f"Error getting recording: {e}")
            return None
    
    def get_recordings(self, faculty_id=None, subject=None, date_str=None):
        """Get recordings with filters"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM recordings WHERE 1=1"
            params = []
            
            if faculty_id:
                query += " AND faculty_id = %s"
                params.append(faculty_id)
            
            if subject:
                query += " AND subject ILIKE %s"
                params.append(f"%{subject}%")
            
            if date_str:
                query += " AND date = %s"
                params.append(date_str)
            
            query += " ORDER BY date DESC, start_time DESC"
            
            cursor.execute(query, params)
            recordings = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(r) for r in recordings]
            
        except Exception as e:
            print(f"Error getting recordings: {e}")
            return []
    
    def get_transcript_segments(self, recording_id):
        """Get transcript segments for recording"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM transcripts
                WHERE recording_id = %s
                ORDER BY timestamp_start
            """
            
            cursor.execute(query, (recording_id,))
            segments = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(s) for s in segments]
            
        except Exception as e:
            print(f"Error getting segments: {e}")
            return []
    
    def search_recordings(self, query):
        """Search recordings by keywords"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            search_query = """
                SELECT DISTINCT r.* FROM recordings r
                LEFT JOIN transcripts t ON r.id = t.recording_id
                WHERE 
                    r.subject ILIKE %s OR
                    r.summary ILIKE %s OR
                    r.transcript_text ILIKE %s OR
                    t.text ILIKE %s
                ORDER BY r.date DESC
                LIMIT 20
            """
            
            search_pattern = f"%{query}%"
            cursor.execute(search_query, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(r) for r in results]
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def delete_recording(self, recording_id):
        """Delete recording and transcripts"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete transcripts first
            cursor.execute("DELETE FROM transcripts WHERE recording_id = %s", (recording_id,))
            
            # Delete recording
            cursor.execute("DELETE FROM recordings WHERE id = %s", (recording_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error deleting recording: {e}")
            return False
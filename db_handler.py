# db_handler.py
import sqlite3
from datetime import datetime
import json

class DatabaseHandler:
    def __init__(self, db_path="counseling.db"):
        self.db_path = db_path
        self.initialize_database()

    def get_connection(self):
        """데이터베이스 연결 생성"""
        return sqlite3.connect(self.db_path)

    def initialize_database(self):
        """데이터베이스 및 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 대화 세션 테이블 생성
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    session_status TEXT
                )
                ''')

                # 대화 내용 테이블 생성
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    timestamp TIMESTAMP,
                    role TEXT,
                    content TEXT,
                    emotion_detected TEXT,
                    crisis_detected BOOLEAN,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                )
                ''')

                # 감정 분석 결과 테이블 생성
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_analysis (
                    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    emotion_type TEXT,
                    emotion_score FLOAT,
                    analysis_timestamp TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id)
                )
                ''')

                conn.commit()
                
        except sqlite3.Error as e:
            print(f"데이터베이스 초기화 중 오류 발생: {e}")

    def create_session(self, user_id=None):
        """새로운 대화 세션 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now()
                cursor.execute('''
                INSERT INTO chat_sessions (user_id, start_time, session_status)
                VALUES (?, ?, ?)
                ''', (user_id, current_time, 'active'))
                
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"세션 생성 중 오류 발생: {e}")
            return None

    def end_session(self, session_id):
        """대화 세션 종료"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now()
                cursor.execute('''
                UPDATE chat_sessions 
                SET end_time = ?, session_status = ?
                WHERE session_id = ?
                ''', (current_time, 'completed', session_id))
        except sqlite3.Error as e:
            print(f"세션 종료 중 오류 발생: {e}")

    def save_message(self, session_id, role, content, emotion_detected=None, crisis_detected=False):
        """대화 메시지 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now()
                cursor.execute('''
                INSERT INTO chat_messages 
                (session_id, timestamp, role, content, emotion_detected, crisis_detected)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (session_id, current_time, role, content, emotion_detected, crisis_detected))
                
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"메시지 저장 중 오류 발생: {e}")
            return None

    def save_emotion_analysis(self, message_id, emotion_type, emotion_score):
        """감정 분석 결과 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now()
                cursor.execute('''
                INSERT INTO emotion_analysis 
                (message_id, emotion_type, emotion_score, analysis_timestamp)
                VALUES (?, ?, ?, ?)
                ''', (message_id, emotion_type, emotion_score, current_time))
        except sqlite3.Error as e:
            print(f"감정 분석 저장 중 오류 발생: {e}")

    def get_session_history(self, session_id):
        """특정 세션의 대화 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT timestamp, role, content, emotion_detected, crisis_detected
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp
                ''', (session_id,))
                
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"대화 내역 조회 중 오류 발생: {e}")
            return []

    def get_emotion_statistics(self, session_id):
        """특정 세션의 감정 통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT e.emotion_type, AVG(e.emotion_score) as avg_score
                FROM emotion_analysis e
                JOIN chat_messages m ON e.message_id = m.message_id
                WHERE m.session_id = ?
                GROUP BY e.emotion_type
                ''', (session_id,))
                
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"감정 통계 조회 중 오류 발생: {e}")
            return []

    def export_session_data(self, session_id):
        """세션 데이터 JSON 형식으로 내보내기"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 세션 정보 조회
                cursor.execute('''
                SELECT * FROM chat_sessions WHERE session_id = ?
                ''', (session_id,))
                session_data = cursor.fetchone()
                
                if not session_data:
                    return None
                
                # 대화 내용 조회
                cursor.execute('''
                SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp
                ''', (session_id,))
                messages = cursor.fetchall()
                
                # 감정 분석 결과 조회
                cursor.execute('''
                SELECT * FROM emotion_analysis 
                WHERE message_id IN (SELECT message_id FROM chat_messages WHERE session_id = ?)
                ''', (session_id,))
                emotions = cursor.fetchall()
                
                # JSON 형식으로 변환
                export_data = {
                    'session': dict(zip(['session_id', 'user_id', 'start_time', 'end_time', 'status'], session_data)),
                    'messages': [dict(zip(['message_id', 'session_id', 'timestamp', 'role', 'content', 
                                         'emotion_detected', 'crisis_detected'], msg)) for msg in messages],
                    'emotions': [dict(zip(['analysis_id', 'message_id', 'emotion_type', 'emotion_score', 
                                         'timestamp'], emo)) for emo in emotions]
                }
                
                return json.dumps(export_data, default=str, ensure_ascii=False, indent=2)
                
        except sqlite3.Error as e:
            print(f"데이터 내보내기 중 오류 발생: {e}")
            return None
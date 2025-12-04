#!/usr/bin/env python3
"""
Simplified Database Management for AI-Driven English Learning System
"""
import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Any

class SimpleDatabase:
    def __init__(self, db_path: str = "english_learning.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize simplified database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                preferred_level VARCHAR(2) DEFAULT 'B1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                topic VARCHAR(100),
                english_level VARCHAR(2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                overall_score REAL DEFAULT 0.0
            )
        ''')

        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER REFERENCES conversations(conversation_id),
                role VARCHAR(10) NOT NULL,
                content TEXT NOT NULL,
                ai_analysis TEXT,  -- JSON string from AI
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER,
                cefr_estimate VARCHAR(2)
            )
        ''')

        # Errors table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                error_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER REFERENCES messages(message_id),
                error_type VARCHAR(20) NOT NULL,
                severity VARCHAR(10) DEFAULT 'minor',
                original_text TEXT NOT NULL,
                correction TEXT,
                explanation TEXT,
                confidence_score REAL DEFAULT 0.0
            )
        ''')

        # Learning progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                date DATE NOT NULL,
                messages_sent INTEGER DEFAULT 0,
                total_errors INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                unique_words_used INTEGER DEFAULT 0,
                cefr_progress VARCHAR(10) DEFAULT 'stable'
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✅ Simplified database initialized: {self.db_path}")

    def get_or_create_user(self, username: str, preferred_level: str = 'B1') -> int:
        """Get or create user, return user_id"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()

            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                cursor.execute(
                    'UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
                    (user_id,)
                )
            else:
                cursor.execute('''
                    INSERT INTO users (username, preferred_level)
                    VALUES (?, ?)
                ''', (username, preferred_level))
                user_id = cursor.lastrowid

            conn.commit()
            return user_id
        except Exception as e:
            print(f"Database error: {e}")
            return 1  # Return default user ID
        finally:
            if 'conn' in locals():
                conn.close()

    def create_conversation(self, user_id: int, english_level: str, topic: str = None) -> int:
        """Create new conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO conversations (user_id, english_level, topic)
            VALUES (?, ?, ?)
        ''', (user_id, english_level, topic))

        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conversation_id

    def add_message_with_ai_analysis(self, conversation_id: int, role: str,
                                   content: str, ai_analysis: Dict = None) -> int:
        """Add message with AI analysis"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()

            word_count = len(content.split()) if content else 0
            cefr_estimate = ai_analysis.get('vocabulary', {}).get('cefr_level_estimate') if ai_analysis else None
            ai_json = json.dumps(ai_analysis) if ai_analysis else None

            cursor.execute('''
                INSERT INTO messages
                (conversation_id, role, content, ai_analysis, word_count, cefr_estimate)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (conversation_id, role, content, ai_json, word_count, cefr_estimate))

            message_id = cursor.lastrowid

            # Update conversation message count
            cursor.execute('''
                UPDATE conversations
                SET total_messages = total_messages + 1
                WHERE conversation_id = ?
            ''', (conversation_id,))

            conn.commit()

            # Store errors from AI analysis (in separate connection to avoid locking)
            if ai_analysis and 'errors' in ai_analysis:
                self._store_errors_from_ai(message_id, ai_analysis['errors'])

            return message_id

        except Exception as e:
            print(f"Database error in add_message: {e}")
            return 0
        finally:
            if 'conn' in locals():
                conn.close()

    def _store_errors_from_ai(self, message_id: int, errors: List[Dict]):
        """Store errors detected by AI"""
        if not errors or message_id <= 0:
            return

        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()

            for error in errors:
                cursor.execute('''
                    INSERT INTO errors
                    (message_id, error_type, severity, original_text, correction, explanation, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message_id,
                    error.get('error_type', 'unknown'),
                    error.get('severity', 'minor'),
                    error.get('original_text', ''),
                    error.get('correction', ''),
                    error.get('explanation', ''),
                    error.get('confidence', 0.0)
                ))

            conn.commit()
        except Exception as e:
            print(f"Database error in store_errors: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def update_learning_progress(self, user_id: int, message_data: Dict):
        """Update daily learning progress"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()

            today = date.today()

            # Check if today's record exists
            cursor.execute('''
                SELECT progress_id FROM learning_progress
                WHERE user_id = ? AND date = ?
            ''', (user_id, today))

            result = cursor.fetchone()

            if result:
                # Update existing record
                progress_id = result[0]
                cursor.execute('''
                    UPDATE learning_progress
                    SET messages_sent = messages_sent + 1,
                        total_errors = total_errors + ?,
                        avg_score = ?,
                        cefr_progress = ?
                    WHERE progress_id = ?
                ''', (
                    len(message_data.get('errors', [])),
                    message_data.get('score', 0),
                    message_data.get('cefr_estimate', 'stable'),
                    progress_id
                ))
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO learning_progress
                    (user_id, date, messages_sent, total_errors, avg_score, cefr_progress)
                    VALUES (?, ?, 1, ?, ?, ?)
                ''', (
                    user_id,
                    today,
                    len(message_data.get('errors', [])),
                    message_data.get('score', 0),
                    message_data.get('cefr_estimate', 'stable')
                ))

            conn.commit()
        except Exception as e:
            print(f"Database error in update_progress: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def get_user_statistics(self, user_id: int) -> Dict:
        """Get comprehensive user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # User info
        cursor.execute('''
            SELECT username, preferred_level, created_at, last_active
            FROM users WHERE user_id = ?
        ''', (user_id,))
        user_info = cursor.fetchone()

        # Conversation stats
        cursor.execute('''
            SELECT COUNT(*) as total_conversations,
                   AVG(total_messages) as avg_messages,
                   COUNT(DISTINCT english_level) as levels_practiced
            FROM conversations WHERE user_id = ?
        ''', (user_id,))
        conv_stats = cursor.fetchone()

        # Error breakdown
        cursor.execute('''
            SELECT error_type, COUNT(*) as count, AVG(confidence_score) as avg_confidence
            FROM errors e
            JOIN messages m ON e.message_id = m.message_id
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ?
            GROUP BY error_type
        ''', (user_id,))
        error_stats = dict(cursor.fetchall())

        # Recent progress
        cursor.execute('''
            SELECT date, messages_sent, total_errors, avg_score, cefr_progress
            FROM learning_progress
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 7
        ''', (user_id,))
        recent_progress = cursor.fetchall()

        # Vocabulary usage
        cursor.execute('''
            SELECT COUNT(*) as total_messages,
                   SUM(word_count) as total_words,
                   AVG(cefr_estimate) as avg_cefr
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ? AND role = 'user'
        ''', (user_id,))
        vocab_stats = cursor.fetchone()

        conn.close()

        return {
            'user_info': {
                'username': user_info[0] if user_info else 'Unknown',
                'preferred_level': user_info[1] if user_info else 'B1',
                'join_date': user_info[2] if user_info else None,
                'last_active': user_info[3] if user_info else None
            },
            'conversations': {
                'total': conv_stats[0] if conv_stats else 0,
                'avg_messages': round(conv_stats[1], 2) if conv_stats and conv_stats[1] else 0,
                'levels_practiced': conv_stats[2] if conv_stats else 0
            },
            'errors': error_stats,
            'recent_progress': recent_progress,
            'vocabulary': {
                'total_messages': vocab_stats[0] if vocab_stats else 0,
                'total_words': vocab_stats[1] if vocab_stats else 0,
                'avg_cefr': vocab_stats[2] if vocab_stats else 'B1'
            }
        }

    def get_user_errors(self, user_id: int, limit: int = 50, days: int = None) -> List[Dict]:
        """Get user's error history with context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if days:
            cursor.execute('''
                SELECT m.content, e.error_type, e.severity, e.original_text,
                       e.correction, e.explanation, m.timestamp, e.confidence_score
                FROM errors e
                JOIN messages m ON e.message_id = m.message_id
                JOIN conversations c ON m.conversation_id = c.conversation_id
                WHERE c.user_id = ? AND m.timestamp >= datetime('now', '-{} days')
                ORDER BY m.timestamp DESC
                LIMIT ?
            '''.format(days), (user_id, limit))
        else:
            cursor.execute('''
                SELECT m.content, e.error_type, e.severity, e.original_text,
                       e.correction, e.explanation, m.timestamp, e.confidence_score
                FROM errors e
                JOIN messages m ON e.message_id = m.message_id
                JOIN conversations c ON m.conversation_id = c.conversation_id
                WHERE c.user_id = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (user_id, limit))

        errors = []
        for content, error_type, severity, original_text, correction, explanation, timestamp, confidence in cursor.fetchall():
            errors.append({
                'user_message': content,
                'error_type': error_type,
                'severity': severity,
                'original_text': original_text,
                'correction': correction,
                'explanation': explanation,
                'timestamp': timestamp,
                'confidence': confidence
            })

        conn.close()
        return errors

    def get_error_patterns(self, user_id: int, days: int = 30) -> Dict:
        """Analyze error patterns for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Error type distribution
        cursor.execute('''
            SELECT error_type, COUNT(*) as count
            FROM errors e
            JOIN messages m ON e.message_id = m.message_id
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ? AND m.timestamp >= datetime('now', '-{} days')
            GROUP BY error_type
            ORDER BY count DESC
        '''.format(days), (user_id,))

        error_distribution = dict(cursor.fetchall())

        # Most frequent errors
        cursor.execute('''
            SELECT original_text, correction, COUNT(*) as frequency
            FROM errors e
            JOIN messages m ON e.message_id = m.message_id
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ? AND m.timestamp >= datetime('now', '-{} days')
            GROUP BY original_text, correction
            ORDER BY frequency DESC
            LIMIT 10
        '''.format(days), (user_id,))

        frequent_errors = cursor.fetchall()

        # Error trend over time
        cursor.execute('''
            SELECT DATE(m.timestamp) as date, COUNT(*) as error_count
            FROM errors e
            JOIN messages m ON e.message_id = m.message_id
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ? AND m.timestamp >= datetime('now', '-{} days')
            GROUP BY DATE(m.timestamp)
            ORDER BY date DESC
        '''.format(days), (user_id,))

        error_trend = dict(cursor.fetchall())

        conn.close()

        return {
            'distribution': error_distribution,
            'frequent_errors': frequent_errors,
            'trend': error_trend,
            'analysis_period_days': days
        }

    def export_user_data(self, user_id: int) -> Dict:
        """Export all user data for analysis"""
        stats = self.get_user_statistics(user_id)

        # Get detailed recent messages with AI analysis
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT content, ai_analysis, timestamp, word_count, cefr_estimate
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ? AND role = 'user'
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (user_id,))

        recent_messages = []
        for content, ai_analysis, timestamp, word_count, cefr_estimate in cursor.fetchall():
            try:
                analysis_data = json.loads(ai_analysis) if ai_analysis else {}
            except:
                analysis_data = {}

            recent_messages.append({
                'content': content,
                'timestamp': timestamp,
                'word_count': word_count,
                'cefr_estimate': cefr_estimate,
                'errors': analysis_data.get('errors', []),
                'score': analysis_data.get('score', 0)
            })

        conn.close()

        return {
            'statistics': stats,
            'recent_messages': recent_messages,
            'export_timestamp': datetime.now().isoformat()
        }

# Test the database
if __name__ == "__main__":
    db = SimpleDatabase()

    # Test user creation
    user_id = db.get_or_create_user("test_user", "B1")
    print(f"✅ Test user created: {user_id}")

    # Test statistics
    stats = db.get_user_statistics(user_id)
    print("📊 User statistics:", json.dumps(stats, indent=2, default=str))
#!/usr/bin/env python3
"""
Debug database to see what's actually stored
"""
import sqlite3
import json

def debug_database():
    """Debug database contents"""
    conn = sqlite3.connect('english_learning.db')
    cursor = conn.cursor()

    print("🔍 Debugging Database Contents")
    print("=" * 50)

    # Check users
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    print(f"\n👥 Users ({len(users)}):")
    for user_id, username in users:
        print(f"  ID {user_id}: {username}")

    # Check conversations
    cursor.execute("SELECT conversation_id, user_id, topic FROM conversations")
    conversations = cursor.fetchall()
    print(f"\n💬 Conversations ({len(conversations)}):")
    for conv_id, user_id, topic in conversations:
        print(f"  ID {conv_id}: User {user_id}, Topic: {topic}")

    # Check messages for laowang (both user and assistant)
    cursor.execute('''
        SELECT m.message_id, m.role, m.content, m.ai_analysis, m.timestamp
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.conversation_id
        WHERE c.user_id = (SELECT user_id FROM users WHERE username = 'laowang')
        ORDER BY m.timestamp DESC
        LIMIT 10
    ''')
    messages = cursor.fetchall()

    print(f"\n📝 Messages for laowang ({len(messages)} recent):")
    for msg_id, role, content, ai_analysis, timestamp in messages:
        print(f"  Message {msg_id} ({role}): {content[:50]}...")
        if ai_analysis:
            try:
                analysis = json.loads(ai_analysis)
                print(f"    Analysis keys: {list(analysis.keys())}")
                if 'errors' in analysis:
                    print(f"    Errors count: {len(analysis['errors'])}")
                    for i, error in enumerate(analysis['errors']):
                        print(f"      Error {i+1}: {error}")
                else:
                    print(f"    No 'errors' key found")
                    print(f"    Available keys: {list(analysis.keys())}")
                    if 'learning_notes' in analysis:
                        print(f"    Learning notes: {analysis['learning_notes'][:100]}...")
            except Exception as e:
                print(f"    Error parsing JSON: {e}")
                print(f"    Raw analysis: {ai_analysis[:200]}...")
        else:
            print(f"    No AI analysis stored")

    # Check errors table
    cursor.execute('''
        SELECT e.error_id, e.original_text, e.correction, e.explanation, e.message_id
        FROM errors e
        JOIN messages m ON e.message_id = m.message_id
        JOIN conversations c ON m.conversation_id = c.conversation_id
        WHERE c.user_id = (SELECT user_id FROM users WHERE username = 'laowang')
        ORDER BY e.error_id DESC
        LIMIT 10
    ''')
    errors = cursor.fetchall()

    print(f"\n❌ Errors for laowang ({len(errors)} recent):")
    for error_id, original, correction, explanation, msg_id in errors:
        print(f"  Error {error_id}: '{original}' → '{correction}' (Message {msg_id})")

    conn.close()

if __name__ == "__main__":
    debug_database()
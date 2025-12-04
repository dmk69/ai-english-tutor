#!/usr/bin/env python3
"""
Create test error data for testing error viewing functionality
"""
import json
from datetime import datetime, timedelta
from simple_database import SimpleDatabase

def create_test_data():
    """Create test user and conversation with errors"""
    db = SimpleDatabase()

    # Create test user
    user_id = db.get_or_create_user("test_errors_user", "B1")
    print(f"Created user with ID: {user_id}")

    # Create test conversation
    conversation_id = db.create_conversation(user_id, "B1", "General practice")
    print(f"Created conversation with ID: {conversation_id}")

    # Test messages with various errors
    test_messages = [
        {
            'content': "I go to school yesterday and learn many thing.",
            'errors': [
                {
                    'error_type': 'grammar',
                    'severity': 'major',
                    'original_text': 'I go',
                    'correction': 'I went',
                    'explanation': 'Use past tense for yesterday',
                    'confidence': 0.95
                },
                {
                    'error_type': 'grammar',
                    'severity': 'minor',
                    'original_text': 'learn many thing',
                    'correction': 'learned many things',
                    'explanation': 'Use past tense and plural',
                    'confidence': 0.90
                }
            ]
        },
        {
            'content': "My favorite color are blue because it calm.",
            'errors': [
                {
                    'error_type': 'grammar',
                    'severity': 'major',
                    'original_text': 'color are',
                    'correction': 'color is',
                    'explanation': 'Subject-verb agreement',
                    'confidence': 0.95
                },
                {
                    'error_type': 'vocabulary',
                    'severity': 'minor',
                    'original_text': 'it calm',
                    'correction': 'it is calming',
                    'explanation': 'Use adjective form',
                    'confidence': 0.85
                }
            ]
        },
        {
            'content': "She have a beautiful house and nice garden.",
            'errors': [
                {
                    'error_type': 'grammar',
                    'severity': 'major',
                    'original_text': 'She have',
                    'correction': 'She has',
                    'explanation': 'Third person singular',
                    'confidence': 0.95
                }
            ]
        },
        {
            'content': "I am very interesting in science and technology.",
            'errors': [
                {
                    'error_type': 'vocabulary',
                    'severity': 'major',
                    'original_text': 'interesting',
                    'correction': 'interested',
                    'explanation': 'Use -ed form for feelings',
                    'confidence': 0.90
                }
            ]
        },
        {
            'content': "Can you help me with my homeworks please?",
            'errors': [
                {
                    'error_type': 'vocabulary',
                    'severity': 'minor',
                    'original_text': 'homeworks',
                    'correction': 'homework',
                    'explanation': 'Homework is uncountable',
                    'confidence': 0.95
                }
            ]
        }
    ]

    # Add messages to database
    for i, msg_data in enumerate(test_messages):
        # Add user message
        message_id = db.add_message_with_ai_analysis(
            conversation_id,
            'user',
            msg_data['content'],
            {'errors': msg_data['errors'], 'score': 75 - len(msg_data['errors']) * 5}
        )

        # Add errors separately
        db._store_errors_from_ai(message_id, msg_data['errors'])

        # Add AI response
        ai_response = f"Thanks for sharing! I notice you said '{msg_data['content']}'. Let me help you with that."
        db.add_message_with_ai_analysis(
            conversation_id,
            'assistant',
            ai_response,
            {'learning_notes': f'Found {len(msg_data["errors"])} errors to help with', 'score': 85}
        )

        print(f"Added message {i+1}: {msg_data['content'][:50]}...")

    print(f"\n✅ Created test data with {len(test_messages)} messages and errors!")
    print("You can now test the error viewing functions:")
    print("uv run english_tutor.py --username test_errors_user --errors")
    print("uv run english_tutor.py --username test_errors_user --patterns")

if __name__ == "__main__":
    create_test_data()
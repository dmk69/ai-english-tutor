#!/usr/bin/env python3
"""
Generate test conversations with errors to test error tracking
"""
import os
import time
from english_tutor import EnglishTutor

def generate_test_conversations():
    """Generate conversations with typical English errors"""
    if not os.environ.get('DEEPSEEK_API_KEY'):
        print("❌ DEEPSEEK_API_KEY not set!")
        return

    tutor = EnglishTutor("laowang", "B1")
    tutor.start_conversation("English practice with errors")

    test_messages = [
        "I go to school yesterday and learn many thing.",  # Past tense error
        "My favorite color are blue because it calm.",     # Subject-verb agreement
        "She have a beautiful house and nice garden.",     # Third person singular
        "I am very interesting in science.",               # -ed vs -ing confusion
        "Can you help me with my homeworks please?",       # Countable noun error
        "He don't like pizza, but I do.",                  # Don't vs doesn't
        "I have seen him yesterday.",                      # Present perfect vs past
        "The informations are very useful.",               # Information is uncountable
        "I am studying English since three years.",        # For vs since
        "She is more taller than her brother."             # Double comparative
    ]

    print("🚀 Generating test conversations with errors...")
    print("This will create realistic error records for testing.\n")

    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}/{len(test_messages)}: {message}")

        try:
            # Process the message
            stream, response_time = tutor.process_user_message_stream(message)

            # Collect the response
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

            # Parse and display
            parsed = tutor.parse_streaming_response(full_response)
            print(f"  💬 AI: {parsed['conversation'][:100]}...")

            if parsed['errors']:
                print(f"  🔍 Found {len(parsed['errors'])} error(s)")
                for error in parsed['errors']:
                    print(f"     - {error['original_text']} → {error['correction']}")
            else:
                print(f"  ✨ No major errors detected")

            print(f"  ⚡ Time: {response_time_ms:.0f}ms" if 'response_time_ms' in locals() else "  ⚡ Response received")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print("-" * 50)

        # Small delay to avoid overwhelming the API
        time.sleep(1)

    print(f"\n✅ Generated {len(test_messages)} test conversations!")
    print("Now you can check the error records:")
    print("uv run english_tutor.py --username \"laowang\" --errors")
    print("uv run english_tutor.py --username \"laowang\" --patterns")

if __name__ == "__main__":
    generate_test_conversations()
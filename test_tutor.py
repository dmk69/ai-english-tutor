#!/usr/bin/env python3
"""
Simple test of the English tutor with AI error detection
"""
import os
import json
from openai import OpenAI

def test_ai_error_detection():
    """Test AI-based error detection"""
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )

    # Test message with grammar error
    user_message = "I go to school yesterday."

    prompt = f"""
You are an English tutor for a B1 learner. Your task:

1. **Natural Conversation**: Respond naturally to the user's message
2. **Error Analysis**: Analyze the user's message for errors

**Response Format Requirements:**
Return JSON with exactly this structure:
{{
    "conversation_response": "your natural English reply",
    "error_analysis": {{
        "has_errors": true/false,
        "error_count": number,
        "errors": [
            {{
                "error_type": "grammar/vocabulary/spelling/expression/punctuation",
                "severity": "minor/major/critical",
                "original_text": "exact user text",
                "correction": "corrected version",
                "explanation": "brief learning explanation",
                "confidence": 0.0-1.0
            }}
        ],
        "vocabulary_analysis": {{
            "new_words": ["word1", "word2"],
            "word_count": total_words,
            "cefr_level_estimate": "A1/A2/B1/B2/C1/C2"
        }},
        "overall_score": 0-100
    }}
}}

User message: "{user_message}"
"""

    print("🤖 Testing AI error detection...")
    print(f"Input: {user_message}")

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message}
            ],
            stream=False,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # Remove JSON code blocks if present
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

        # Parse JSON
        ai_response = json.loads(content)

        print("\n✅ AI Response Parsed Successfully!")
        print(f"\n🤖 Conversation Response:")
        print(ai_response.get('conversation_response', ''))

        print(f"\n📊 Error Analysis:")
        error_analysis = ai_response.get('error_analysis', {})
        print(f"- Has errors: {error_analysis.get('has_errors', False)}")
        print(f"- Error count: {error_analysis.get('error_count', 0)}")
        print(f"- Overall score: {error_analysis.get('overall_score', 0)}/100")

        errors = error_analysis.get('errors', [])
        if errors:
            print(f"\n🔍 Detected Errors:")
            for i, error in enumerate(errors, 1):
                print(f"  Error {i}:")
                print(f"    - Type: {error.get('error_type', 'unknown')}")
                print(f"    - Original: {error.get('original_text', '')}")
                print(f"    - Correction: {error.get('correction', '')}")
                print(f"    - Explanation: {error.get('explanation', '')}")
                print(f"    - Severity: {error.get('severity', 'minor')}")
                print(f"    - Confidence: {error.get('confidence', 0):.2f}")
        else:
            print("\n✅ No errors detected!")

        vocab_analysis = error_analysis.get('vocabulary_analysis', {})
        if vocab_analysis:
            print(f"\n📚 Vocabulary Analysis:")
            print(f"- Word count: {vocab_analysis.get('word_count', 0)}")
            print(f"- New words: {vocab_analysis.get('new_words', [])}")
            print(f"- CEFR estimate: {vocab_analysis.get('cefr_level_estimate', 'unknown')}")

        return True

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Raw content: {content}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    if not os.environ.get('DEEPSEEK_API_KEY'):
        print("❌ DEEPSEEK_API_KEY not set!")
        exit(1)

    success = test_ai_error_detection()
    if success:
        print("\n🎉 AI error detection test completed successfully!")
    else:
        print("\n💥 AI error detection test failed!")
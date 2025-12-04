#!/usr/bin/env python3
"""
Test the new streaming English tutor with subtle learning
"""
import os
import time
from openai import OpenAI
from rich.console import Console

def test_streaming_conversation():
    """Test the new streaming conversation format"""
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )
    console = Console()

    # Test cases with different types of user messages
    test_messages = [
        ("Hello, how are you today?", "Simple greeting"),
        ("I go to school yesterday. What did you learn?", "Grammar error in past tense"),
        ("What's your opinion about artificial intelligence?", "Complex topic"),
        ("My favorite color are blue. Do you like it?", "Subject-verb agreement error"),
        ("Tell me about quantum physics in simple terms", "Advanced topic request")
    ]

    console.print("🚀 Testing Streaming English Tutor", style="bold green")
    console.print("=" * 50)

    for i, (message, description) in enumerate(test_messages, 1):
        console.print(f"\n📝 Test {i}: {description}", style="bold yellow")
        console.print(f"💬 User: {message}")

        # Create prompt
        prompt = f"""
You are having a natural conversation with a B1 English learner. Your goal is to have an interesting, engaging conversation while subtly providing language learning support.

**Response Format:**
PART 1: Natural conversation response (main focus)
PART 2: Optional brief learning notes (only if there are significant errors)

Format your response as:
```
[NATURAL CONVERSATION RESPONSE]

---
[LEARNING NOTES - Only if there are significant errors]
Error found: "original" → "correction" - brief explanation
```

User message: "{message}"
"""

        try:
            # Get streaming response
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                stream=True,
                temperature=0.7
            )

            # Collect and display streaming response
            console.print("🤖 AI Tutor:", style="bold blue")

            full_response = ""

            # Show "thinking" status
            with console.status("[bold green]Thinking...", spinner="dots"):
                # Collect the full response
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content

            # Parse and display
            if '---' in full_response:
                parts = full_response.split('---')
                conversation_part = parts[0].strip()
                learning_part = parts[1].strip() if len(parts) > 1 else ""
            else:
                conversation_part = full_response.strip()
                learning_part = ""

            # Display conversation with streaming effect
            console.print("\n", end="")
            for char in conversation_part:
                console.print(char, end="", style="blue")
                time.sleep(0.005)

            console.print()  # New line

            # Display learning notes subtly
            if learning_part:
                console.print("\n💡 Quick tip:", style="dim cyan")
                for line in learning_part.split('\n'):
                    if line.strip():
                        console.print(f"   {line}", style="dim cyan")
            else:
                console.print("\n✨ No corrections needed - great English!", style="dim green")

        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")

        console.print("\n" + "-" * 50)

    console.print("\n🎉 Streaming tutor test completed!", style="bold green")
    console.print("Key improvements:")
    console.print("• Natural conversation flow")
    console.print("• Subtle learning support")
    console.print("• Only major errors are corrected")
    console.print("• Seamless streaming experience")

if __name__ == "__main__":
    if not os.environ.get('DEEPSEEK_API_KEY'):
        print("❌ DEEPSEEK_API_KEY not set!")
        exit(1)

    test_streaming_conversation()
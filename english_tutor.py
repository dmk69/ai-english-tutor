#!/usr/bin/env python3
"""
AI-Driven English Learning Tutor
Simplified version with AI-based error detection
"""
import os
import json
import sys
import time
import argparse
import sqlite3
from datetime import datetime
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from typing import Dict, List, Any

from simple_database import SimpleDatabase

class EnglishTutor:
    def __init__(self, username: str = None, level: str = 'B1'):
        self.client = OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        self.db = SimpleDatabase()
        self.console = Console()

        # Initialize user and conversation
        self.username = username or f"user_{int(time.time())}"
        self.preferred_level = level.upper()
        self.user_id = self.db.get_or_create_user(self.username, self.preferred_level)
        self.conversation_id = None
        self.conversation_history = []

        # CEFR level prompts
        self.level_prompts = {
            'A1': "You are talking to an English beginner. Use simple words (CEFR A1), short sentences, and basic grammar.",
            'A2': "You are talking to an elementary English learner. Use common vocabulary (CEFR A2) and simple compound sentences.",
            'B1': "You are talking to an intermediate English learner. Use moderate vocabulary (CEFR B1) and some complex sentences.",
            'B2': "You are talking to an upper-intermediate learner. Use rich vocabulary (CEFR B2) and varied sentence structures.",
            'C1': "You are talking to an advanced English learner. Use sophisticated vocabulary (CEFR C1) and complex grammar.",
            'C2': "You are talking to a proficient English speaker. Use native-level vocabulary and natural expressions."
        }

    def _create_ai_prompt(self, user_message: str) -> str:
        """Create AI prompt with seamless conversation and optional error guidance"""
        return f"""
You are having a natural conversation with a {self.preferred_level} English learner. Your goal is to have an interesting, engaging conversation while subtly providing language learning support.

**Conversation Style:**
- Be natural, friendly, and conversational
- Focus on the topic/content the user wants to discuss
- Use {self.preferred_level} level English that's accessible but slightly challenging
- Ask follow-up questions to keep the conversation flowing

**Learning Support (Subtle):**
- If the user makes major errors that seriously hinder communication, you can gently provide minimal correction
- Focus on conversation flow over grammar perfection
- Only highlight errors that truly matter for comprehension
- Provide corrections as gentle suggestions, not strict corrections

**Response Format:**
PART 1: Natural conversation response (main focus)
PART 2: Optional brief learning notes (only if there are significant errors)

Format your response as:
```
[NATURAL CONVERSATION RESPONSE - This should be your main response, focusing on the topic]

---
[LEARNING NOTES - Only include this section if there are 1-2 significant errors that affect communication. Keep it very brief and encouraging. If no significant errors, don't include this section.]
Error found: "original text" → "correction" - brief explanation
```

**Guidelines for Learning Notes:**
- Only include for major errors (not minor typos or grammar slips)
- Maximum 1-2 learning notes per response
- Keep explanations very brief and encouraging
- Focus on communication effectiveness
- If the user's English is perfectly understandable, skip the learning section entirely

**Remember:** The goal is natural conversation with minimal learning interruptions. Don't overwhelm with corrections.

User message: "{user_message}"
"""

    def start_conversation(self, topic: str = None):
        """Start a new conversation session"""
        self.conversation_id = self.db.create_conversation(
            self.user_id, self.preferred_level, topic
        )
        self.conversation_history = []

        self.console.print(Panel.fit(
            f"🎓 English Tutor Started\n"
            f"👤 User: {self.username}\n"
            f"📚 Level: {self.preferred_level}\n"
            f"🎯 Topic: {topic or 'General conversation'}",
            title="Welcome"
        ))

    def process_user_message_stream(self, user_message: str):
        """Process user message with streaming AI response"""
        if not user_message.strip():
            return {'conversation': 'Please enter a message.', 'errors': [], 'score': 0}

        # Store user message
        self.db.add_message_with_ai_analysis(
            self.conversation_id, 'user', user_message
        )

        # Get streaming AI response
        start_time = time.time()

        stream = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self._create_ai_prompt(user_message)},
                {"role": "user", "content": user_message}
            ],
            stream=True,
            temperature=0.7
        )

        response_time = (time.time() - start_time) * 1000

        return stream, response_time

    def parse_streaming_response(self, full_response: str) -> Dict:
        """Parse the AI response to separate conversation and learning parts"""
        parts = full_response.split('---')

        conversation_part = parts[0].strip()
        learning_part = parts[1].strip() if len(parts) > 1 else ""

        # Parse learning notes if present
        errors = []
        score = 85  # Default good score

        if learning_part and "Error found:" in learning_part:
            lines = learning_part.split('\n')

            for line in lines:
                if "Error found:" in line:
                    try:
                        # Extract error information using regex-like parsing
                        # Format: Error found: "original" → "correction" - explanation
                        import re

                        # Try to match the error pattern
                        match = re.search(r'Error found:\s*"([^"]+)"\s*→\s*"([^"]+)"\s*-\s*(.+)', line)
                        if match:
                            original_text = match.group(1).strip()
                            correction = match.group(2).strip()
                            explanation = match.group(3).strip()

                            # Create error entry in database format
                            errors.append({
                                'error_type': 'grammar',  # Default type
                                'severity': 'major',      # Default severity
                                'original_text': original_text,
                                'correction': correction,
                                'explanation': explanation,
                                'confidence': 0.9
                            })

                            score = 75  # Lower score if there are errors
                    except Exception as e:
                        # If parsing fails, still indicate there's an error
                        score = 75
                        # Add a generic error entry
                        errors.append({
                            'error_type': 'general',
                            'severity': 'minor',
                            'original_text': 'parsing_error',
                            'correction': 'see_full_response',
                            'explanation': f'Could not parse error details: {str(e)}',
                            'confidence': 0.5
                        })

        return {
            'conversation': conversation_part,
            'learning_notes': learning_part,
            'errors': errors,
            'score': score
        }

    def display_streaming_response(self, stream, response_time_ms: float):
        """Display streaming AI response with subtle learning notes"""
        self.console.print("\n🤖 AI Tutor:", style="bold blue")

        # Streaming display of conversation
        full_response = ""
        self.console.print("", end="")

        with self.console.status("[bold green]Thinking...", spinner="dots"):
            # Collect the full response first
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

        # Parse the response
        parsed = self.parse_streaming_response(full_response)

        # Display conversation part with streaming effect
        self.console.print("\n", end="")
        conversation_text = parsed['conversation']

        for char in conversation_text:
            self.console.print(char, end="", style="blue")
            time.sleep(0.01)  # Small delay for streaming effect

        self.console.print()  # New line after conversation

        # Display learning notes subtly (if present)
        if parsed['learning_notes']:
            self.console.print("\n💡 Quick tip:", style="dim cyan")
            # Display learning notes in a subtle way
            for line in parsed['learning_notes'].split('\n'):
                if line.strip():
                    self.console.print(f"   {line}", style="dim cyan")

        # First, get the last user message ID to associate errors with it
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message_id FROM messages
            WHERE conversation_id = ? AND role = 'user'
            ORDER BY message_id DESC LIMIT 1
        ''', (self.conversation_id,))
        result = cursor.fetchone()
        user_message_id = result[0] if result else None
        conn.close()

        # Store errors associated with the user message
        if parsed['errors'] and user_message_id:
            self.db._store_errors_from_ai(user_message_id, parsed['errors'])

        # Store the AI response in database
        self.db.add_message_with_ai_analysis(
            self.conversation_id, 'assistant', parsed['conversation'],
            {'learning_notes': parsed['learning_notes'], 'errors': parsed['errors'], 'score': parsed['score']}
        )

        # Update learning progress
        self.db.update_learning_progress(self.user_id, {
            'errors': parsed['errors'],
            'score': parsed['score'],
            'cefr_estimate': self.preferred_level
        })

        # Show minimal stats
        self.console.print(f"\n⚡ Response time: {response_time_ms:.0f}ms", style="dim green")

    def display_ai_response(self, response_data: Dict):
        """Legacy method for backward compatibility"""
        self.console.print("\n🤖 AI Tutor:", style="bold blue")
        self.console.print(Panel(response_data['conversation'], border_style="blue"))

    def show_error_history(self, days: int = 7, limit: int = 20):
        """Display user's error history"""
        errors = self.db.get_user_errors(self.user_id, limit, days)

        if not errors:
            self.console.print("🎉 No errors found in the specified period!", style="bold green")
            return

        self.console.print(f"\n🔍 Error History (Last {days} days):", style="bold yellow")
        self.console.print(f"Found {len(errors)} errors\n", style="dim cyan")

        for i, error in enumerate(errors, 1):
            # Create error panel
            error_content = (
                f"[bold]Message:[/bold] {error['user_message'][:80]}{'...' if len(error['user_message']) > 80 else ''}\n\n"
                f"[bold red]Error:[/bold red] {error['original_text']}\n"
                f"[bold green]Correction:[/bold green] {error['correction']}\n\n"
                f"[bold]Explanation:[/bold] {error['explanation']}\n\n"
                f"[dim]Type: {error['error_type']} | Severity: {error['severity']} | "
                f"Time: {error['timestamp']} | Confidence: {error['confidence']:.1f}[/dim]"
            )

            panel = Panel(
                error_content,
                title=f"Error #{i}",
                border_style="red" if error['severity'] == 'critical' else "yellow" if error['severity'] == 'major' else "blue"
            )
            self.console.print(panel)
            self.console.print()  # Add spacing

    def show_error_patterns(self, days: int = 30):
        """Display error pattern analysis"""
        patterns = self.db.get_error_patterns(self.user_id, days)

        self.console.print(f"\n📊 Error Pattern Analysis (Last {days} days):", style="bold cyan")

        # Error type distribution
        if patterns['distribution']:
            self.console.print("\n📈 Error Type Distribution:", style="bold yellow")
            for error_type, data in patterns['distribution'].items():
                if isinstance(data, tuple):  # Handle (count, avg_confidence) format
                    count = data[0]
                    avg_conf = data[1] if len(data) > 1 else 0
                else:  # Handle simple count format
                    count = data
                    avg_conf = 0

                bar_length = min(int(count / 2), 20)  # Scale bar to max 20 chars
                bar = "█" * bar_length
                self.console.print(f"  {error_type:15} {bar:20} {count:3d} errors")

        # Most frequent errors
        if patterns['frequent_errors']:
            self.console.print("\n🔥 Most Frequent Errors:", style="bold red")
            for i, (original, correction, frequency) in enumerate(patterns['frequent_errors'][:5], 1):
                self.console.print(f"  {i}. \"{original}\" → \"{correction}\" ({frequency} times)")

        # Error trend
        if patterns['trend']:
            self.console.print("\n📉 Daily Error Trend:", style="bold green")
            sorted_trend = sorted(patterns['trend'].items(), key=lambda x: x[0], reverse=True)
            for date, count in sorted_trend[:7]:  # Last 7 days
                bar_length = min(int(count), 15)
                bar = "▓" * bar_length
                self.console.print(f"  {date}: {bar:15} {count}")

        if not patterns['distribution'] and not patterns['frequent_errors'] and not patterns['trend']:
            self.console.print("✨ No error patterns detected yet!", style="bold green")

    def show_statistics(self):
        """Display user learning statistics"""
        stats = self.db.get_user_statistics(self.user_id)

        table = Table(title=f"📈 Learning Statistics for {stats['user_info']['username']}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Preferred Level", stats['user_info']['preferred_level'])
        table.add_row("Total Conversations", str(stats['conversations']['total']))
        table.add_row("Avg Messages/Conversation", str(stats['conversations']['avg_messages']))
        table.add_row("Levels Practiced", str(stats['conversations']['levels_practiced']))
        table.add_row("Total Words", str(stats['vocabulary']['total_words']))

        self.console.print(table)

        # Error breakdown
        if stats['errors']:
            self.console.print("\n🔍 Error Breakdown:", style="bold yellow")
            for error_type, count in stats['errors'].items():
                if isinstance(count, tuple):
                    actual_count = count[0]
                else:
                    actual_count = count
                self.console.print(f"  • {error_type}: {actual_count}")

    def export_data(self, format_type: str = 'json'):
        """Export user learning data"""
        data = self.db.export_user_data(self.user_id)

        if format_type == 'json':
            filename = f"english_learning_export_{self.username}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            self.console.print(f"📁 Data exported to: {filename}", style="green")
        else:
            self.console.print("❌ Only JSON export is currently supported", style="red")

    def run_interactive(self):
        """Run interactive conversation session"""
        self.console.print("🚀 Starting English Learning Session")
        self.console.print("Commands: 'quit', 'stats', 'errors', 'patterns', 'export', 'help'")

        while True:
            try:
                user_input = Prompt.ask("\n💬 You").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.console.print("👋 Goodbye! Keep practicing English!", style="bold green")
                    break

                elif user_input.lower() == 'stats':
                    self.show_statistics()
                    continue

                elif user_input.lower().startswith('errors'):
                    # Parse errors command with optional parameters
                    parts = user_input.split()
                    days = 7
                    limit = 20
                    if len(parts) > 1:
                        try:
                            days = int(parts[1])
                        except:
                            pass
                    if len(parts) > 2:
                        try:
                            limit = int(parts[2])
                        except:
                            pass
                    self.show_error_history(days, limit)
                    continue

                elif user_input.lower().startswith('patterns'):
                    # Parse patterns command with optional days parameter
                    parts = user_input.split()
                    days = 30
                    if len(parts) > 1:
                        try:
                            days = int(parts[1])
                        except:
                            pass
                    self.show_error_patterns(days)
                    continue

                elif user_input.lower() == 'export':
                    self.export_data()
                    continue

                elif user_input.lower() == 'help':
                    self.console.print(Panel.fit(
                        "Commands:\n"
                        "• quit/exit/q - Exit the program\n"
                        "• stats - Show your learning statistics\n"
                        "• errors [days] [limit] - Show error history (default: 7 days, 20 errors)\n"
                        "• patterns [days] - Show error pattern analysis (default: 30 days)\n"
                        "• export - Export your learning data\n"
                        "• help - Show this help message",
                        title="Help"
                    ))
                    continue

                elif not user_input:
                    continue

                # Process message with streaming AI response
                stream, response_time = self.process_user_message_stream(user_input)
                self.display_streaming_response(stream, response_time)

            except KeyboardInterrupt:
                self.console.print("\n👋 Session ended. Goodbye!", style="bold green")
                break
            except Exception as e:
                self.console.print(f"\n❌ Error: {e}", style="red")

def main():
    parser = argparse.ArgumentParser(description='AI-Driven English Learning Tutor')
    parser.add_argument('--username', '-u', help='Your username')
    parser.add_argument('--level', '-l', default='B1',
                       choices=['A1', 'A2', 'B1', 'B2', 'C1', 'C2'],
                       help='English proficiency level (default: B1)')
    parser.add_argument('--topic', '-t', help='Conversation topic')
    parser.add_argument('--stats', action='store_true', help='Show statistics and exit')
    parser.add_argument('--errors', action='store_true', help='Show error history and exit')
    parser.add_argument('--patterns', action='store_true', help='Show error patterns and exit')
    parser.add_argument('--export', action='store_true', help='Export data and exit')
    parser.add_argument('--error-days', type=int, default=7, help='Days for error history (default: 7)')
    parser.add_argument('--pattern-days', type=int, default=30, help='Days for error patterns (default: 30)')

    args = parser.parse_args()

    # Check API key
    if not os.environ.get('DEEPSEEK_API_KEY'):
        print("❌ Error: DEEPSEEK_API_KEY environment variable not set")
        print("Please set it with: export DEEPSEEK_API_KEY=your_api_key")
        sys.exit(1)

    tutor = EnglishTutor(args.username, args.level)

    if args.stats:
        tutor.show_statistics()
        return

    if args.errors:
        tutor.show_error_history(args.error_days)
        return

    if args.patterns:
        tutor.show_error_patterns(args.pattern_days)
        return

    if args.export:
        tutor.export_data()
        return

    # Start conversation
    tutor.start_conversation(args.topic)
    tutor.run_interactive()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import sys
from openai import OpenAI

class DeepSeekChat:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        self.conversation_history = []

    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []

    def stream_chat(self, user_message: str):
        """流式传输对话"""
        # 添加用户消息
        self.add_message("user", user_message)

        try:
            # 创建流式响应
            stream = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.conversation_history,
                stream=True,
                max_tokens=2000,
                temperature=0.7
            )

            print("🤖 DeepSeek: ", end="", flush=True)
            assistant_response = ""

            # 逐块接收响应
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    assistant_response += content

            print()  # 换行

            # 添加助手回复到历史
            if assistant_response:
                self.add_message("assistant", assistant_response)

        except Exception as e:
            print(f"\n❌ 错误: {e}")

    def run_interactive(self):
        """运行交互式对话"""
        print("🚀 DeepSeek 流式对话程序")
        print("输入 'quit' 或 'exit' 退出程序")
        print("输入 'clear' 清空对话历史")
        print("-" * 50)

        while True:
            try:
                # 获取用户输入
                user_input = input("\n👤 您: ").strip()

                # 处理命令
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
                    break
                elif user_input.lower() in ['clear', '清空']:
                    self.clear_history()
                    print("🧹 对话历史已清空")
                    continue
                elif not user_input:
                    print("❗ 请输入消息内容")
                    continue

                # 发送消息并获取流式响应
                self.stream_chat(user_input)

            except KeyboardInterrupt:
                print("\n👋 程序已终止")
                break
            except EOFError:
                print("\n👋 再见！")
                break

def main():
    # 检查 API Key
    if not os.environ.get('DEEPSEEK_API_KEY'):
        print("❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请设置环境变量: export DEEPSEEK_API_KEY=your_api_key")
        sys.exit(1)

    # 创建聊天实例并运行
    chat = DeepSeekChat()
    chat.run_interactive()

if __name__ == "__main__":
    main()
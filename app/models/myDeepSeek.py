from dotenv import load_dotenv
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 默认加载项目根目录的 .env 文件
load_dotenv()

class DeepSeekChat:
    def __init__(self):
        self.model = None
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 OPENAI_API_KEY，请检查 .env 文件")
        self.base_url = os.getenv("BASE_URL")
        self.model_name = os.getenv("MODEL_NAME")
        self.md_filename = None

    def init_model(self):
        """初始化 DeepSeek 模型"""
        try:
            self.model = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url,
            )
            if self.model is None:
                raise ValueError("模型初始化失败：返回了 None")
            return True
        except Exception as e:
            print(f"模型初始化失败: {e}")
            return False

    def start_conversation(self):
        """开始对话并记录到 Markdown 文件"""
        if self.model is None:
            if not self.init_model():
                return

        # 生成带时间戳的 Markdown 文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.md_filename = f"deepseek_chat_{timestamp}.md"

        # 写入文件标题
        with open(self.md_filename, "w", encoding="utf-8") as f:
            f.write(f"# DeepSeek 对话记录 ({timestamp})\n\n")

        print(f"对话将保存到: {self.md_filename}")
        user_input = input("请输入你的问题（输入 'exit' 退出）：\n")

        while user_input.strip().lower() != "exit":
            try:
                # 调用模型并获取回答
                response = self._get_response(user_input)
                print("DeepSeek 的回答：", response)

                # 记录到 Markdown
                self._log_to_markdown(user_input, response)

            except Exception as e:
                print(f"调用失败: {e}")
                self._log_to_markdown(user_input, f"错误: {e}")

            user_input = input("\n请输入下一个问题（输入 'exit' 退出）：\n")

        print(f"对话结束！记录已保存到 {self.md_filename}")

    def _get_response(self, user_input):
        """私有方法：获取模型回答"""
        if not self.model:
            raise RuntimeError("模型未初始化，请先调用 init_model()")

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个技术助手。"),
                ("user", "{input}")
            ])
            parser = StrOutputParser()

            # 分步执行链式操作
            formatted_prompt = prompt.invoke({"input": user_input})
            model_response = self.model.invoke(formatted_prompt)
            return parser.invoke(model_response)
        except Exception as e:
            print(f"调用失败: {e}")
            raise

    def _log_to_markdown(self, question, answer):
        """私有方法：写入 Markdown 文件"""
        with open(self.md_filename, "a", encoding="utf-8") as f:
            f.write(f"## 用户提问\n{question}\n\n")
            f.write(f"## AI 回答\n{answer}\n\n")

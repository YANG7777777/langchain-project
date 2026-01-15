from dotenv import load_dotenv
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class DeepDeekServer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 OPENAI_API_KEY，请检查 .env 文件")
        self.base_url = os.getenv("BASE_URL")
        self.model_name = os.getenv("MODEL_NAME")
        self.model = None
        self.prompt = None
        self.parser = None
        self._initialize()

    def _initialize(self):
        try:
            self.model = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url,
            )
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个技术助手。"),
                ("user", "{input}")
            ])
            self.parser = StrOutputParser()
        except Exception as e:
            print(f"模型初始化失败: {e}")
            raise

    async def query(self, question: str, stream: bool = False):
        if not self.model:
            raise RuntimeError("模型未初始化")
        
        try:
            if stream:
                chain = self.prompt | self.model | self.parser
                return chain.astream({"input": question})
            else:
                formatted_prompt = self.prompt.invoke({"input": question})
                model_response = self.model.invoke(formatted_prompt)
                return self.parser.invoke(model_response)
        except Exception as e:
            print(f"调用失败: {e}")
            raise

    def query_stream(self, question: str):
        if not self.model:
            raise RuntimeError("模型未初始化")
        
        try:
            formatted_prompt = self.prompt.invoke({"input": question})
            for chunk in self.model.stream(formatted_prompt):
                content = chunk.content
                if content:
                    yield content
        except Exception as e:
            print(f"调用失败: {e}")
            raise

    async def query_astream(self, question: str):
        if not self.model:
            raise RuntimeError("模型未初始化")
        
        try:
            formatted_prompt = self.prompt.invoke({"input": question})
            async for chunk in self.model.astream(formatted_prompt):
                content = chunk.content
                if content:
                    yield content
        except Exception as e:
            print(f"调用失败: {e}")
            raise
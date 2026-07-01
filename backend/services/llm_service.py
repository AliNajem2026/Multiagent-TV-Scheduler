import os

from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic

load_dotenv()

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    temperature=0.3,
    anthropic_api_key=os.getenv(
        "ANTHROPIC_API_KEY"
    )
)
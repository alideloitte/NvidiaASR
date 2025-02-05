from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import AzureChatOpenAI
import yaml
from dotenv import load_dotenv
import os

load_dotenv("config/.env")

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class BaseAgent:
    def __init__(self, temperature=0.3, **kwargs) -> None:
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-35-turbo",
            model_name="gpt-35-turbo",
            azure_endpoint=AZURE_ENDPOINT,
            openai_api_version=OPENAI_API_VERSION,
            openai_api_key=OPENAI_API_KEY,
            temperature=temperature,
            **kwargs
        )
        self._get_env()

    def _get_env(self):
        with open("./config/workflows.yml", "r") as file:
            self.workflows_description = yaml.safe_load(file)
        with open("./config/parameters_helpers.yml", "r") as file:
            self.parameters_helpers = yaml.safe_load(file)

    def update_history(self, user_input, assistant_response, history: list | None):
        if history is None:
            history = []
        history += [
            {"role": "user", "content": user_input},
            {"role": "ai", "content": assistant_response},
        ]
        return history
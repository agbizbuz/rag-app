from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Resolve .env relative to this file's directory, so the app works
# regardless of whether Streamlit is launched from project root or src/ragapp/.
_ENV_PATH = Path(__file__).resolve().parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    db_path: str = Field(default="./chroma_db", validation_alias="CHROMA_DB_PATH")
    collection_name: str = Field(default="my_rag_collection", validation_alias="COLLECTION_NAME")
    default_llm: str = Field(default="gpt-4o-mini", validation_alias="DEFAULT_LLM")

    groq_api_key: str = ""
    huggingface_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    lm_studio_base_url: str = "http://localhost:1234/v1"
    llm_temperature: float = Field(default=0.2, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, validation_alias="LLM_MAX_TOKENS")
    model_config = {"env_file": str(_ENV_PATH), "env_file_encoding": "utf-8"}


settings = Settings()

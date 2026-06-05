from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()


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
    class Config:
        env_file = ".env"


settings = Settings()


from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# --------------------------------------------------------------------------- #
# .env loading                                                                #
# --------------------------------------------------------------------------- #

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
    ollama_base_url: str = "http://localhost:11434"
    lm_studio_base_url: str = "http://localhost:1234"
    llm_temperature: float = Field(default=0.2, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, validation_alias="LLM_MAX_TOKENS")
    max_file_size_bytes: int = Field(default=50 * 1024 * 1024, validation_alias="MAX_FILE_SIZE")

    chunk_size: int = Field(default=1000, validation_alias="CHUNK_SIZE")
    n_results: int = Field(default=3, validation_alias="N_RESULTS")
    system_prompt: str = Field(
        default=(
            "You are a highly capable research assistant. "
            "Answer the user's query strictly based on the provided context. "
            "If the context does not contain sufficient information to answer "
            "the question, respectfully state that the information is not found in "
            "the documents. Provide the answer clearly and concisely."
        ),
        validation_alias="SYSTEM_PROMPT",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="EMBEDDING_MODEL",
    )
    discovery_timeout: int = Field(default=3, validation_alias="DISCOVERY_TIMEOUT")

    retrieval_mode: str = Field(default="hybrid", validation_alias="RETRIEVAL_MODE")
    # model_config = {"env_file": str(_ENV_PATH), "env_file_encoding": "utf-8"}


settings = Settings()

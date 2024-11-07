import os
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from anthropic import AsyncAnthropic

class Settings(BaseSettings):
    # OpenAI Configuration
    ANTHROPIC_API_KEY: str = Field(..., env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field("claude-3-5-sonnet-latest", env="ANTHROPIC_MODEL")

    # Serper API Configuration
    SERPER_API_KEY: str = Field(..., env="SERPER_API_KEY")

    # GitHub API Configuration
    GITHUB_API_KEY: str = Field(..., env="GITHUB_API_KEY")

    # Application Configuration
    DEBUG: bool = Field(False, env="DEBUG")
    LOGFIRE_TOKEN: str = Field(..., env="LOGFIRE_TOKEN")

    # File Upload Configuration
    UPLOAD_DIR: str = Field("uploads", env="UPLOAD_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_llm_client(self) -> AsyncAnthropic:
        client = AsyncAnthropic(api_key=self.ANTHROPIC_API_KEY)
        return client


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Function to load configuration
def load_config():
    return get_settings()


# Create upload directory if it doesn't exist
os.makedirs(get_settings().UPLOAD_DIR, exist_ok=True)

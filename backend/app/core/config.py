"""
Configuration settings for the RAG application
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = "RAG Microservice API"
    VERSION: str = "1.0.0"
    
    # Model Settings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    LLM_MODEL: str = "Qwen/Qwen2.5-0.5B-Instruct"
    
    # Qdrant Settings
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    COLLECTION_NAME: str = "documents"
    EMBEDDING_DIM: int = 384  # bge-small dimension
    
    # Text Processing Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_LENGTH: int = 512
    
    # Generation Settings
    MAX_NEW_TOKENS: int = 256
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    
    class Config:
        case_sensitive = True

settings = Settings()
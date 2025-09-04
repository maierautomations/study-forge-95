"""Application configuration using Pydantic Settings"""

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_version: str = Field(default="0.1.0", description="API version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # CORS Configuration
    allowed_origins: str = Field(
        default="http://localhost:3000", 
        description="CORS allowed origins (comma-separated)"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/postgres", 
        description="PostgreSQL connection URL"
    )
    
    # Supabase Configuration
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_anon_key: str = Field(default="", description="Supabase anon key for client")
    supabase_service_role_key: str = Field(default="", description="Supabase service role key")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key for embeddings/LLM")
    
    # Document Processing
    max_file_size_mb: int = Field(default=50, description="Max file size in MB")
    chunk_size: int = Field(default=500, description="Default chunk size in tokens")
    chunk_overlap: float = Field(default=0.12, description="Chunk overlap percentage")
    
    # Search Configuration
    bm25_weight: float = Field(default=0.4, description="BM25 weight in hybrid search")
    vector_weight: float = Field(default=0.6, description="Vector weight in hybrid search")
    max_search_results: int = Field(default=20, description="Max results per search method")
    max_context_chunks: int = Field(default=10, description="Max chunks for RAG context")
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings
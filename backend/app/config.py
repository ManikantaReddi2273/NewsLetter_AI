"""Configuration settings for the Newsletter AI application."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "newsletter_db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # API Keys
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    GOOGLE_FACT_CHECK_API_KEY: str = ""
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "newsletter-faiss-index"
    
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # FAISS
    FAISS_INDEX_PATH: str = "./data/faiss_index.pkl"
    FAISS_DIMENSION: int = 384
    FAISS_TOP_K: int = 5
    
    # Cache
    CACHE_TTL: int = 3600
    
    @property
    def database_url(self) -> str:
        """Get MySQL database URL."""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

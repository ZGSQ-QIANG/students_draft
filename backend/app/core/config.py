from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Student Resume Portrait System"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 720
    admin_username: str = "admin"
    admin_password: str = "admin123"
    database_url: str = "sqlite:///./student_portrait.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: str = "./storage"
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://chat.ecnu.edu.cn/open/api/v1 "
    llm_model: str = "ecnu-max"
    llm_timeout_seconds: int = 60
    llm_temperature: float = 0.2
    embedding_provider: str = "huggingface"
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_model_path: str = "/Users/zgsq/models/Qwen3-Embedding-0.6B"
    embedding_device: str = "cpu"
    embedding_normalize: bool = True
    embedding_query_instruction: str = (
        "任务：根据学生简历搜索需求，检索最相关的学生简历片段，"
        "重点关注教育背景、项目经历、科研成果、实习经历、实操技能和发展方向。"
    )
    embedding_timeout_seconds: int = 60
    embedding_batch_size: int = 32
    embedding_dimension: int = 8
    chroma_persist_directory: str = "./storage/chroma"
    semantic_search_top_k: int = 5
    hybrid_search_enabled: bool = True
    bm25_top_k: int = 20
    dense_top_k_multiplier: int = 3
    rrf_k: int = 60
    rrf_dense_weight: float = 1.0
    rrf_keyword_weight: float = 1.0
    rerank_enabled: bool = True
    rerank_provider: str = "qwen3_local"
    rerank_model_path: str = "/Users/zgsq/models/Qwen3-Reranker-0.6B"
    rerank_device: str = "cpu"
    rerank_batch_size: int = 4
    rerank_max_length: int = 8192
    rerank_candidate_multiplier: int = 3
    rerank_max_candidates: int = 8
    rerank_instruction: str = "Given a student resume search query, judge whether the resume chunk is relevant to the query."

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_root).resolve()

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_directory).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

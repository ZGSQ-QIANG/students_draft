from __future__ import annotations

import httpx

from app.core.config import Settings

try:
    from langchain_core.embeddings import Embeddings
except ImportError:  # pragma: no cover - runtime dependency is validated when indexing/searching.
    class Embeddings:  # type: ignore[no-redef]
        pass


class EmbeddingsProvider(Embeddings):
    model_name = ""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class HuggingFaceLocalEmbeddingsProvider(EmbeddingsProvider):
    def __init__(self, settings: Settings) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("sentence-transformers is required for local Hugging Face embeddings.") from exc

        if not settings.embedding_model_path.strip():
            raise ValueError("EMBEDDING_MODEL_PATH is required when using huggingface embedding provider.")
        self.model_name = settings.embedding_model_path
        self.model = SentenceTransformer(settings.embedding_model_path, device=settings.embedding_device)
        self.normalize_embeddings = settings.embedding_normalize
        self.query_instruction = settings.embedding_query_instruction.strip()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        query = f"{self.query_instruction}\n查询：{text}" if self.query_instruction else text
        return self.embed_documents([query])[0]


class OpenAICompatibleEmbeddingsProvider(EmbeddingsProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.embedding_api_key.strip():
            raise ValueError("EMBEDDING_API_KEY is required when using real embedding provider.")
        self.model_name = settings.embedding_model
        self.base_url = settings.embedding_base_url.rstrip("/")
        self.api_key = settings.embedding_api_key
        self.timeout_seconds = settings.embedding_timeout_seconds
        self.batch_size = settings.embedding_batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        with httpx.Client(timeout=self.timeout_seconds) as client:
            for start in range(0, len(texts), self.batch_size):
                batch = texts[start : start + self.batch_size]
                response = client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model_name, "input": batch},
                )
                if response.status_code >= 400:
                    raise RuntimeError(f"Embedding request failed: {response.status_code} {response.text[:300]}")
                payload = response.json()
                data = sorted(payload.get("data", []), key=lambda item: item.get("index", 0))
                if len(data) != len(batch):
                    raise RuntimeError("Embedding response size does not match request batch size.")
                embeddings.extend([item.get("embedding", []) for item in data])
        return embeddings


def build_embeddings_provider(settings: Settings) -> EmbeddingsProvider:
    provider_name = settings.embedding_provider.strip().lower()
    if provider_name in {"huggingface", "local"}:
        return HuggingFaceLocalEmbeddingsProvider(settings)
    if provider_name in {"openai", "real"}:
        return OpenAICompatibleEmbeddingsProvider(settings)
    raise ValueError(f"Unsupported embedding_provider: {settings.embedding_provider}")

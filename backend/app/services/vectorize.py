from __future__ import annotations

import hashlib

from app.core.config import get_settings


class Vectorizer:
    def embed(self, text: str) -> list[float]:
        dimension = get_settings().embedding_dimension
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for index in range(dimension):
            chunk = digest[index * 2 : index * 2 + 2]
            values.append(round(int.from_bytes(chunk, "big") / 65535, 6))
        return values


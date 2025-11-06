import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer

from src.domain.ports.memory import MemoryStore


class FaissMemoryStore(MemoryStore):
    """FAISS-based semantic memory store with per-user indices."""

    def __init__(
        self,
        base_path: str = "./memory",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def _user_dir(self, user_id: str) -> Path:
        d = self.base_path / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _index_path(self, user_id: str) -> Path:
        return self._user_dir(user_id) / "index.faiss"

    def _meta_path(self, user_id: str) -> Path:
        return self._user_dir(user_id) / "metadata.json"

    def _load_index(self, user_id: str) -> faiss.Index:
        idx_path = self._index_path(user_id)
        if idx_path.exists():
            index = faiss.read_index(str(idx_path))
        else:
            # Cosine similarity via inner product on normalized vectors
            index = faiss.IndexFlatIP(self.dim)
        return index

    def _save_index(self, user_id: str, index: faiss.Index) -> None:
        faiss.write_index(index, str(self._index_path(user_id)))

    def _load_metadata(self, user_id: str) -> List[Dict[str, Any]]:
        meta_path = self._meta_path(user_id)
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_metadata(self, user_id: str, data: List[Dict[str, Any]]) -> None:
        self._meta_path(user_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _embed(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        )
        return embeddings.astype(np.float32)

    def add_memory(
        self, user_id: str, text: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        index = self._load_index(user_id)
        vec = self._embed([text])
        index.add(vec)
        self._save_index(user_id, index)

        metadatas = self._load_metadata(user_id)
        metadatas.append({"text": text, "metadata": metadata or {}})
        self._save_metadata(user_id, metadatas)

    def search(self, user_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        index = self._load_index(user_id)
        if index.ntotal == 0:
            return []
        qvec = self._embed([query])
        scores, idxs = index.search(qvec, min(k, max(1, index.ntotal)))
        scores = scores[0].tolist()
        idxs = idxs[0].tolist()

        metadatas = self._load_metadata(user_id)
        results: List[Dict[str, Any]] = []
        for i, score in zip(idxs, scores):
            if i == -1 or i >= len(metadatas):
                continue
            item = metadatas[i]
            results.append(
                {
                    "text": item.get("text", ""),
                    "metadata": item.get("metadata", {}),
                    "score": float(score),
                }
            )
        return results

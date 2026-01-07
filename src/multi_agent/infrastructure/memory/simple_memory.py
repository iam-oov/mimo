import json
import os
from pathlib import Path
from typing import Any, Dict, List

from src.multi_agent.domain.ports.memory import MemoryStore


class SimpleMemoryStore(MemoryStore):
    """Simple in-memory/file-based memory store without heavy ML dependencies.

    Uses simple keyword matching instead of semantic embeddings.
    Lighter alternative to FAISS for Railway deployments.
    """

    def __init__(self, base_path: str = "./memory"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, user_id: str) -> Path:
        d = self.base_path / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _data_path(self, user_id: str) -> Path:
        return self._user_dir(user_id) / "memories.json"

    def _load_memories(self, user_id: str) -> List[Dict[str, Any]]:
        data_path = self._data_path(user_id)
        if data_path.exists():
            try:
                return json.loads(data_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_memories(self, user_id: str, memories: List[Dict[str, Any]]) -> None:
        self._data_path(user_id).write_text(
            json.dumps(memories, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_memory(self, user_id: str, text: str, metadata: Dict[str, Any] | None = None) -> None:
        memories = self._load_memories(user_id)
        memories.append(
            {"text": text, "metadata": metadata or {}, "keywords": self._extract_keywords(text)}
        )
        self._save_memories(user_id, memories)

    def search(self, user_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        memories = self._load_memories(user_id)
        if not memories:
            return []

        query_keywords = self._extract_keywords(query)

        # Score each memory by keyword overlap
        scored_memories = []
        for memory in memories:
            memory_keywords = set(memory.get("keywords", []))
            score = len(query_keywords & memory_keywords)
            if score > 0:
                scored_memories.append(
                    {
                        "text": memory["text"],
                        "metadata": memory.get("metadata", {}),
                        "score": float(score),
                    }
                )

        # Sort by score descending and return top k
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:k]

    def _extract_keywords(self, text: str) -> set:
        """Extract simple keywords from text (lowercase, split by spaces)."""
        # Remove common Spanish stopwords
        stopwords = {
            "el",
            "la",
            "de",
            "en",
            "y",
            "a",
            "los",
            "las",
            "del",
            "al",
            "un",
            "una",
            "por",
            "para",
            "con",
            "sin",
            "sobre",
            "que",
            "se",
            "es",
            "son",
            "como",
            "más",
            "pero",
            "su",
            "sus",
            "me",
            "mi",
            "te",
            "tu",
            "le",
            "lo",
        }
        words = text.lower().split()
        # Keep words with 3+ characters and not in stopwords
        keywords = {w for w in words if len(w) >= 3 and w not in stopwords}
        return keywords

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """Port for semantic memory storage and retrieval."""

    @abstractmethod
    def add_memory(self, user_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a memory item for a user."""
        raise NotImplementedError

    @abstractmethod
    def search(self, user_id: str, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search top-k relevant memories for a user.

        Returns list of items with keys: {"text": str, "metadata": dict, "score": float}
        """
        raise NotImplementedError

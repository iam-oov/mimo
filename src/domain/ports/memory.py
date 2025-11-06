from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MemoryStore(ABC):
    """Port for semantic memory storage and retrieval."""

    @abstractmethod
    def add_memory(
        self, user_id: str, text: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        """Add a memory item for a user."""
        raise NotImplementedError

    @abstractmethod
    def search(self, user_id: str, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search top-k relevant memories for a user.

        Returns list of items with keys: {"text": str, "metadata": dict, "score": float}
        """
        raise NotImplementedError

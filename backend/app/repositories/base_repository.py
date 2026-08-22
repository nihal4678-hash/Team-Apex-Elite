from abc import ABC, abstractmethod
from typing import Any


class BaseRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[Any]:
        pass

    @abstractmethod
    def get_by_id(self, item_id: str) -> Any | None:
        pass

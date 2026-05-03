import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    name: str = "base_connector"

    @abstractmethod
    async def search(self, **kwargs) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def enrich(self, **kwargs) -> dict[str, Any] | None:
        pass

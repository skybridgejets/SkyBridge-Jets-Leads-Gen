import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import AgentRun

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, db: AsyncSession, search_id: uuid.UUID):
        self.db = db
        self.search_id = search_id
        self.run_id: uuid.UUID | None = None

    async def _log_start(self):
        run = AgentRun(
            id=uuid.uuid4(),
            search_id=self.search_id,
            agent_name=self.name,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        await self.db.flush()
        self.run_id = run.id
        return run

    async def _log_complete(self, summary: str = ""):
        if self.run_id:
            from sqlalchemy import update
            stmt = (
                update(AgentRun)
                .where(AgentRun.id == self.run_id)
                .values(
                    status="complete",
                    completed_at=datetime.now(timezone.utc),
                    output_summary=summary,
                )
            )
            await self.db.execute(stmt)
            await self.db.flush()

    async def _log_error(self, error: str):
        if self.run_id:
            from sqlalchemy import update
            stmt = (
                update(AgentRun)
                .where(AgentRun.id == self.run_id)
                .values(
                    status="failed",
                    completed_at=datetime.now(timezone.utc),
                    error_message=error,
                )
            )
            await self.db.execute(stmt)
            await self.db.flush()

    async def run(self, input_data: Any) -> Any:
        await self._log_start()
        try:
            result = await self.execute(input_data)
            await self._log_complete(f"Processed {len(result) if isinstance(result, list) else 1} items")
            return result
        except Exception as e:
            logger.exception(f"Agent {self.name} failed: {e}")
            await self._log_error(str(e))
            raise

    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        pass

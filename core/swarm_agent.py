import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import config

logger = logging.getLogger(__name__)

class SwarmAgent:
    """A single worker agent capable of executing async tasks."""

    def __init__(self, agent_id: str, agent_type: str = "general") -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = "idle"
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.started_at: Optional[datetime] = None

    async def execute(self, task_func: Callable, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute an async task function, returning a result dict."""
        self.status = "working"
        self.started_at = datetime.now()
        try:
            result = await task_func(*args, **kwargs)
            self.tasks_completed += 1
            self.status = "idle"
            return {"status": "success", "result": result, "agent": self.agent_id}
        except Exception as e:
            self.tasks_failed += 1
            self.status = "error"
            logger.error(f"[SwarmAgent:{self.agent_id}] Task failed: {e}")
            return {"status": "error", "error": str(e), "agent": self.agent_id}

    def get_stats(self) -> Dict[str, Any]:
        """Return current agent statistics."""
        return {
            "agent_id": self.agent_id,
            "type": self.agent_type,
            "status": self.status,
            "completed": self.tasks_completed,
            "failed": self.tasks_failed,
        }

class SwarmOrchestrator:
    """Orchestrates parallel execution across a pool of SwarmAgents."""

    def __init__(self, max_agents: int = 200) -> None:
        self.max_agents = max_agents
        self.agents: Dict[str, SwarmAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Any] = []
        self.semaphore = asyncio.Semaphore(max_agents)
        self._active = 0
        self._completed = 0
        self._failed = 0

    async def initialize(self) -> None:
        """Pre-create all agents in the pool."""
        for i in range(self.max_agents):
            agent_type = self._get_agent_type(i)
            self.agents[f"agent_{i}"] = SwarmAgent(f"agent_{i}", agent_type)
        logger.info(f"Swarm initialized: {len(self.agents)} agents ({self.max_agents} max)")

    def _get_agent_type(self, index: int) -> str:
        """Map agent index to a role type using round-robin."""
        types = {
            0: "search", 1: "search", 2: "search", 3: "search", 4: "search",
            5: "research", 6: "research", 7: "research", 8: "research", 9: "research",
            10: "apply", 11: "apply", 12: "apply", 13: "apply", 14: "apply",
            15: "followup", 16: "followup", 17: "followup", 18: "followup", 19: "followup",
            20: "ai", 21: "ai", 22: "ai", 23: "ai", 24: "ai",
        }
        return types.get(index % 25, "general")

    async def run_parallel(
        self,
        tasks: List[Tuple[Callable, tuple, dict]],
        max_concurrent: Optional[int] = None,
    ) -> List[Any]:
        """Run a list of (func, args, kwargs) tuples concurrently."""
        if not tasks:
            return []

        max_concurrent = max_concurrent or min(len(tasks), self.max_agents)
        sem = asyncio.Semaphore(max_concurrent)

        async def limited_task(task_func: Callable, *args: Any, **kwargs: Any) -> Any:
            async with sem:
                self._active += 1
                try:
                    result = await task_func(*args, **kwargs)
                    self._completed += 1
                    return result
                except Exception as e:
                    self._failed += 1
                    logger.warning(f"[SwarmOrchestrator] Task failed: {e}")
                    return {"status": "error", "error": str(e)}
                finally:
                    self._active -= 1

        coros = [limited_task(func, *args, **kwargs) for func, args, kwargs in tasks]
        results = await asyncio.gather(*coros, return_exceptions=True)
        return list(results)

    async def run_search_swarm(
        self, search_funcs: List[Callable], max_concurrent: int = 10
    ) -> List[Any]:
        """Run multiple search functions concurrently."""
        tasks = [(func, (), {}) for func in search_funcs]
        return await self.run_parallel(tasks, max_concurrent)

    async def run_apply_swarm(
        self, apply_funcs: List[Callable], max_concurrent: int = 20
    ) -> List[Any]:
        """Run multiple apply functions concurrently."""
        tasks = [(func, (), {}) for func in apply_funcs]
        return await self.run_parallel(tasks, max_concurrent)

    async def run_research_swarm(
        self, research_funcs: List[Callable], max_concurrent: int = 10
    ) -> List[Any]:
        """Run multiple research functions concurrently."""
        tasks = [(func, (), {}) for func in research_funcs]
        return await self.run_parallel(tasks, max_concurrent)

    def get_stats(self) -> Dict[str, Any]:
        """Return current orchestrator statistics."""
        return {
            "total_agents": len(self.agents),
            "active": self._active,
            "completed": self._completed,
            "failed": self._failed,
            "by_type": self._count_by_type(),
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count agents by type."""
        counts: Dict[str, int] = {}
        for agent in self.agents.values():
            t = agent.agent_type
            counts[t] = counts.get(t, 0) + 1
        return counts

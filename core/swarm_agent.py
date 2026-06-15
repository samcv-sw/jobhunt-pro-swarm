import asyncio
import logging
import time
from datetime import datetime
import config

logger = logging.getLogger(__name__)

class SwarmAgent:
    def __init__(self, agent_id, agent_type="general"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = "idle"
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.started_at = None

    async def execute(self, task_func, *args, **kwargs):
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
            return {"status": "error", "error": str(e), "agent": self.agent_id}

    def get_stats(self):
        return {
            "agent_id": self.agent_id,
            "type": self.agent_type,
            "status": self.status,
            "completed": self.tasks_completed,
            "failed": self.tasks_failed,
        }

class SwarmOrchestrator:
    def __init__(self, max_agents=200):
        self.max_agents = max_agents
        self.agents = {}
        self.task_queue = asyncio.Queue()
        self.results = []
        self.semaphore = asyncio.Semaphore(max_agents)
        self._active = 0
        self._completed = 0
        self._failed = 0

    async def initialize(self):
        for i in range(self.max_agents):
            agent_type = self._get_agent_type(i)
            self.agents[f"agent_{i}"] = SwarmAgent(f"agent_{i}", agent_type)
        logger.info(f"Swarm initialized: {len(self.agents)} agents ({self.max_agents} max)")

    def _get_agent_type(self, index):
        types = {
            0: "search", 1: "search", 2: "search", 3: "search", 4: "search",
            5: "research", 6: "research", 7: "research", 8: "research", 9: "research",
            10: "apply", 11: "apply", 12: "apply", 13: "apply", 14: "apply",
            15: "followup", 16: "followup", 17: "followup", 18: "followup", 19: "followup",
            20: "ai", 21: "ai", 22: "ai", 23: "ai", 24: "ai",
        }
        return types.get(index % 25, "general")

    async def run_parallel(self, tasks, max_concurrent=None):
        if not tasks:
            return []

        max_concurrent = max_concurrent or min(len(tasks), self.max_agents)
        sem = asyncio.Semaphore(max_concurrent)
        results = []

        async def limited_task(task_func, *args, **kwargs):
            async with sem:
                self._active += 1
                try:
                    result = await task_func(*args, **kwargs)
                    self._completed += 1
                    return result
                except Exception as e:
                    self._failed += 1
                    return {"status": "error", "error": str(e)}
                finally:
                    self._active -= 1

        coros = [limited_task(func, *args, **kwargs) for func, args, kwargs in tasks]
        results = await asyncio.gather(*coros, return_exceptions=True)
        return results

    async def run_search_swarm(self, search_funcs, max_concurrent=10):
        tasks = [(func, (), {}) for func in search_funcs]
        return await self.run_parallel(tasks, max_concurrent)

    async def run_apply_swarm(self, apply_funcs, max_concurrent=20):
        tasks = [(func, (), {}) for func in apply_funcs]
        return await self.run_parallel(tasks, max_concurrent)

    async def run_research_swarm(self, research_funcs, max_concurrent=10):
        tasks = [(func, (), {}) for func in research_funcs]
        return await self.run_parallel(tasks, max_concurrent)

    def get_stats(self):
        return {
            "total_agents": len(self.agents),
            "active": self._active,
            "completed": self._completed,
            "failed": self._failed,
            "by_type": self._count_by_type(),
        }

    def _count_by_type(self):
        counts = {}
        for agent in self.agents.values():
            t = agent.agent_type
            counts[t] = counts.get(t, 0) + 1
        return counts

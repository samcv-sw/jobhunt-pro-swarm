"""
JobHunt Pro v13 — Agent Pool Manager
Manages virtual async agents across 9 types (7 worker + 2 hierarchy).
Queue system, rate limiting, health monitoring, and smart dispatch.
Supports 20,000 hierarchical agent swarms with Team Managers and Squad Leaders.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """9 agent types — 7 worker types + 2 hierarchy levels."""

    # Worker types
    SCRAPER = "scraper"
    AI_SCORER = "ai_scorer"
    COVER_LETTER = "cover_letter"
    EMAIL_SENDER = "email_sender"
    DATA_COLLECTOR = "data_collector"
    ANALYZER = "analyzer"
    FOLLOW_UP = "follow_up"
    # Hierarchy types
    SQUAD_LEADER = "squad_leader"
    TEAM_MANAGER = "team_manager"


# Agent type distribution: total = 200
AGENT_DISTRIBUTION: dict[AgentType, int] = {
    AgentType.SCRAPER: 50,
    AgentType.AI_SCORER: 30,
    AgentType.COVER_LETTER: 20,
    AgentType.EMAIL_SENDER: 40,
    AgentType.DATA_COLLECTOR: 20,
    AgentType.ANALYZER: 20,
    AgentType.FOLLOW_UP: 20,
}

# Rate limits per agent type (tasks per minute)
AGENT_RATE_LIMITS: dict[AgentType, int] = {
    AgentType.SCRAPER: 10,
    AgentType.AI_SCORER: 30,
    AgentType.COVER_LETTER: 15,
    AgentType.EMAIL_SENDER: 5,  # Email-sending rate-limited to avoid bans
    AgentType.DATA_COLLECTOR: 20,
    AgentType.ANALYZER: 30,
    AgentType.FOLLOW_UP: 10,
    AgentType.SQUAD_LEADER: 50,  # Squad leaders handle coordination
    AgentType.TEAM_MANAGER: 100,  # Team managers handle high-level dispatch
}


@dataclass
class AgentStats:
    agent_id: str
    agent_type: AgentType
    status: str = "idle"  # idle | working | paused | error | dead
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_runtime_seconds: float = 0.0
    current_task_start: float | None = None
    last_heartbeat: float = field(default_factory=time.time)
    errors: list[str] = field(default_factory=list)


class VirtualAgent:
    """A single virtual agent — a coroutine that waits on a type-specific queue."""

    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.stats = AgentStats(agent_id=agent_id, agent_type=agent_type)
        self._task: asyncio.Task | None = None
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # not paused initially
        logger.debug(f"Agent {agent_id} ({agent_type.value}) created")

    @property
    def is_busy(self) -> bool:
        return self.stats.status == "working"

    async def run(self, job_distributor_ref: Any):
        """Main loop: wait for work, do it, report results."""
        while True:
            await self._pause_event.wait()  # block if paused

            try:
                task_data = await asyncio.wait_for(self._queue.get(), timeout=30.0)
            except TimeoutError:
                self.stats.last_heartbeat = time.time()
                if self.stats.status != "idle":
                    self.stats.status = "idle"
                continue

            task_func, args, kwargs, result_callback = task_data
            self.stats.status = "working"
            self.stats.current_task_start = time.time()

            try:
                result = await task_func(*args, **kwargs)
                self.stats.tasks_completed += 1
                self.stats.total_runtime_seconds += (
                    time.time() - self.stats.current_task_start
                )
                self.stats.status = "idle"
                self.stats.last_heartbeat = time.time()
                if result_callback:
                    result_callback(self.agent_id, result, None)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.stats.tasks_failed += 1
                err_msg = f"{type(e).__name__}: {str(e)[:200]}"
                self.stats.errors.append(err_msg)
                if len(self.stats.errors) > 50:
                    self.stats.errors = self.stats.errors[-50:]
                self.stats.status = "idle"
                self.stats.last_heartbeat = time.time()
                logger.warning(f"Agent {self.agent_id} task failed: {err_msg}")
                if result_callback:
                    result_callback(self.agent_id, None, e)
            finally:
                self._queue.task_done()
                self.stats.current_task_start = None

    def assign_task(
        self,
        task_func: Callable[..., Coroutine],
        args: tuple = (),
        kwargs: dict[str, Any] = None,
        result_callback: Callable = None,
    ) -> bool:
        """Assign a task to this agent. Returns True if queued successfully."""
        try:
            self._queue.put_nowait((task_func, args, kwargs or {}, result_callback))
            return True
        except asyncio.QueueFull:
            logger.warning(f"Agent {self.agent_id} queue full, task rejected")
            return False

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    def pause(self):
        self._pause_event.clear()
        self.stats.status = "paused"
        logger.info(f"Agent {self.agent_id} paused")

    def resume(self):
        self._pause_event.set()
        self.stats.status = "idle"
        logger.info(f"Agent {self.agent_id} resumed")

    def get_stats(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "type": self.agent_type.value,
            "status": self.stats.status,
            "completed": self.stats.tasks_completed,
            "failed": self.stats.tasks_failed,
            "queue_depth": self.queue_size,
            "total_runtime_sec": round(self.stats.total_runtime_seconds, 2),
            "last_heartbeat": datetime.fromtimestamp(
                self.stats.last_heartbeat
            ).isoformat(),
            "errors_last_50": len(self.stats.errors),
        }


class AgentPool:
    """
    Manages the full pool of 200 virtual agents.
    Provides queue-based dispatch per agent type with rate limiting.
    """

    def __init__(self):
        self.agents: dict[str, VirtualAgent] = {}
        self._by_type: dict[AgentType, list[VirtualAgent]] = {t: [] for t in AgentType}
        self._round_robin_index: dict[AgentType, int] = {t: 0 for t in AgentType}
        self._rate_limit_semaphores: dict[AgentType, asyncio.Semaphore] = {}
        self._rate_limit_intervals: dict[AgentType, float] = {}
        self._tasks: list[asyncio.Task] = []
        self._background_tasks = set()
        self._health_task: asyncio.Task | None = None
        self._global_semaphore = asyncio.Semaphore(200)

    def build(self, distributor: Any) -> "AgentPool":
        """Create all 200 agents and their run tasks."""
        agent_id = 0
        for agent_type, count in AGENT_DISTRIBUTION.items():
            for _ in range(count):
                aid = f"agent_{agent_id:03d}"
                a = VirtualAgent(aid, agent_type)
                self.agents[aid] = a
                self._by_type[agent_type].append(a)
                task = asyncio.create_task(a.run(distributor))
                self._tasks.append(task)
                agent_id += 1

        # Rate-limit semaphores (allow burst, then throttle)
        for atype in AgentType:
            limit = AGENT_RATE_LIMITS[atype]
            # Allow 2x burst then restrict to limit/min
            self._rate_limit_semaphores[atype] = asyncio.Semaphore(limit * 2)
            self._rate_limit_intervals[atype] = 60.0 / max(limit, 1)

        logger.info(
            f"AgentPool built: {len(self.agents)} agents"
            f" ({', '.join(f'{t.value}={len(v)}' for t, v in self._by_type.items())})"
        )
        return self

    def get_agent(self, agent_type: AgentType) -> VirtualAgent | None:
        """Get next available agent of given type (round-robin)."""
        pool = self._by_type[agent_type]
        if not pool:
            return None

        idx = self._round_robin_index[agent_type]
        for _ in range(len(pool)):
            agent = pool[idx % len(pool)]
            idx += 1
            self._round_robin_index[agent_type] = idx % len(pool)
            if not agent.is_busy and agent.queue_size < 10:
                return agent

        # All busy — return least-loaded
        return min(pool, key=lambda a: a.queue_size)

    def get_agents_of_type(self, agent_type: AgentType) -> list[VirtualAgent]:
        return self._by_type.get(agent_type, [])

    async def dispatch(
        self,
        agent_type: AgentType,
        task_func: Callable[..., Coroutine],
        args: tuple = (),
        kwargs: dict[str, Any] = None,
        result_callback: Callable = None,
        timeout: float = 30.0,
    ) -> bool:
        """Dispatch a task to an agent of given type. Returns True on success."""
        # Rate limiting
        sem = self._rate_limit_semaphores[agent_type]
        if not sem.locked():
            await sem.acquire()
            # Release after interval
            task = asyncio.create_task(self._release_after(agent_type, sem))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        else:
            logger.debug(f"Rate limit hit for {agent_type.value}, waiting...")
            await asyncio.wait_for(sem.acquire(), timeout=timeout)
            task = asyncio.create_task(self._release_after(agent_type, sem))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        async with self._global_semaphore:
            agent = self.get_agent(agent_type)
            if agent is None:
                logger.error(f"No agents available for type {agent_type.value}")
                return False
            return agent.assign_task(task_func, args, kwargs, result_callback)

    async def _release_after(self, agent_type: AgentType, sem: asyncio.Semaphore):
        await asyncio.sleep(self._rate_limit_intervals[agent_type])
        sem.release()

    async def broadcast(
        self,
        agent_type: AgentType,
        task_func: Callable[..., Coroutine],
        args_list: list[tuple],
    ) -> int:
        """Dispatch same task func with different args to ALL agents of a type."""
        dispatched = 0
        agents = self._by_type[agent_type]
        for i, agent in enumerate(agents):
            args = args_list[i] if i < len(args_list) else ()
            if agent.assign_task(task_func, args, {}):
                dispatched += 1
        return dispatched

    async def health_monitor(self, interval: float = 30.0, distributor: Any = None):
        """Periodically check all agents and revive stuck ones by restarting their coroutine."""
        while True:
            await asyncio.sleep(interval)
            now = time.time()
            revived = 0
            for agent in self.agents.values():
                age = now - agent.stats.last_heartbeat
                # If agent hasn't responded in 300s, it's deadlocked.
                if age > 300 and agent.stats.status == "working":
                    logger.critical(
                        f"🔥 SWARM AUTO-HEAL: Agent {agent.agent_id} deadlocked for {age:.0f}s. Nuking and restarting."
                    )

                    # 1. Find and cancel the existing task
                    for t in self._tasks:
                        if (
                            not t.done()
                            and t.get_coro().cr_code.co_name == "run"
                            and getattr(t, "_agent_id", None) == agent.agent_id
                        ):
                            t.cancel()

                    # 2. Reset agent state
                    agent.stats.status = "idle"
                    agent.stats.current_task_start = None
                    agent.stats.last_heartbeat = time.time()

                    # 3. Spawn a fresh task
                    if distributor:
                        new_task = asyncio.create_task(agent.run(distributor))
                        new_task._agent_id = agent.agent_id  # Tag for future tracking
                        self._tasks.append(new_task)

                    revived += 1
            if revived:
                logger.info(
                    f"Health monitor revived {revived} deadlocked agents via Auto-Heal"
                )

    def start_health_monitor(self, distributor: Any = None):
        self._health_task = asyncio.create_task(
            self.health_monitor(distributor=distributor)
        )
        logger.info("Health monitor started (30s interval)")

    def stop_all(self):
        for t in self._tasks:
            t.cancel()
        if self._health_task:
            self._health_task.cancel()
        logger.info("All agent tasks cancelled")

    async def get_pool_stats(self) -> dict[str, Any]:
        by_type = {}
        for atype in AgentType:
            agents = self._by_type[atype]
            by_type[atype.value] = {
                "total": len(agents),
                "busy": sum(1 for a in agents if a.is_busy),
                "idle": sum(1 for a in agents if a.stats.status == "idle"),
                "paused": sum(1 for a in agents if a.stats.status == "paused"),
                "total_completed": sum(a.stats.tasks_completed for a in agents),
                "total_failed": sum(a.stats.tasks_failed for a in agents),
                "queue_depth": sum(a.queue_size for a in agents),
            }

        return {
            "total_agents": len(self.agents),
            "total_completed": sum(
                a.stats.tasks_completed for a in self.agents.values()
            ),
            "total_failed": sum(a.stats.tasks_failed for a in self.agents.values()),
            "active_agents": sum(
                1 for a in self.agents.values() if a.stats.status == "working"
            ),
            "by_type": by_type,
            "timestamp": datetime.now().isoformat(),
        }

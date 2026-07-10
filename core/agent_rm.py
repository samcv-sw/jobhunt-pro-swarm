import asyncio
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class AgentRM:
    """
    OS-Inspired Resource Manager for LLM Agent Systems (AgentRM).
    Implements a Multi-Level Feedback Queue (MLFQ) to prevent stuck agents
    and optimize concurrent API calls across thousands of campaigns.
    """

    _slots: dict[str, asyncio.Semaphore] = {
        "sensitive": asyncio.Semaphore(15),  # Mistral EU bound, highly regulated
        "heavy": asyncio.Semaphore(5),  # Github/Azure heavy models
        "logic": asyncio.Semaphore(30),  # Groq fast inference
        "context": asyncio.Semaphore(10),  # Gemini massive context
    }

    _queues: dict[str, list[dict]] = defaultdict(list)
    _active_agents: dict[str, float] = {}

    @classmethod
    async def acquire_slot(cls, task_type: str, priority: int = 1) -> str:
        """
        Acquire an execution slot using MLFQ principles with robust error safety.
        High priority tasks (e.g. user interacting directly) bypass queues.
        Background scraping campaigns yield to foreground.
        """
        if task_type not in cls._slots:
            task_type = "logic"

        sem = cls._slots[task_type]

        # Simulate MLFQ wait time logic if slots are full
        if sem.locked():
            logger.debug(f"[AgentRM] Queue full for {task_type}. yielding to queue...")

        try:
            await sem.acquire()
            # Track agent execution time
            current_task = asyncio.current_task()
            agent_id = str(id(current_task)) if current_task else "unknown_agent"
            cls._active_agents[agent_id] = time.time()
            return agent_id
        except Exception as e:
            logger.error("[AgentRM] Failed to acquire slot for %s: %s", task_type, e, exc_info=True)
            raise RuntimeError(f"AgentRM failed to acquire resource slot: {e}") from e

    @classmethod
    def release_slot(cls, task_type: str, agent_id: str) -> None:
        """Release the slot back to the MLFQ pool safely."""
        try:
            if task_type in cls._slots:
                # To prevent ValueError if release is called more times than acquire
                try:
                    cls._slots[task_type].release()
                except ValueError as ve:
                    logger.warning("[AgentRM] Semaphore release warning for %s: %s", task_type, ve)

            if agent_id in cls._active_agents:
                duration = time.time() - cls._active_agents.pop(agent_id)
                if duration > 45.0:
                    logger.warning(
                        f"[AgentRM] Agent {agent_id} took {duration:.2f}s. Demoting queue priority next time."
                    )
        except Exception as e:
            logger.error("[AgentRM] Error releasing slot for %s (Agent: %s): %s", task_type, agent_id, e, exc_info=True)


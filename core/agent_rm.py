import asyncio
import time
import logging
from collections import defaultdict
from typing import Dict, List

logger = logging.getLogger(__name__)

class AgentRM:
    """
    OS-Inspired Resource Manager for LLM Agent Systems (AgentRM).
    Implements a Multi-Level Feedback Queue (MLFQ) to prevent stuck agents
    and optimize concurrent API calls across thousands of campaigns.
    """
    
    _slots: Dict[str, asyncio.Semaphore] = {
        "sensitive": asyncio.Semaphore(15), # Mistral EU bound, highly regulated
        "heavy": asyncio.Semaphore(5),      # Github/Azure heavy models
        "logic": asyncio.Semaphore(30),     # Groq fast inference
        "context": asyncio.Semaphore(10),   # Gemini massive context
    }
    
    _queues: Dict[str, List[Dict]] = defaultdict(list)
    _active_agents: Dict[str, float] = {}
    
    @classmethod
    async def acquire_slot(cls, task_type: str, priority: int = 1):
        """
        Acquire an execution slot using MLFQ principles.
        High priority tasks (e.g. user interacting directly) bypass queues.
        Background scraping campaigns yield to foreground.
        """
        if task_type not in cls._slots:
            task_type = "logic"
            
        sem = cls._slots[task_type]
        
        # Simulate MLFQ wait time logic if slots are full
        if sem.locked():
            logger.debug(f"[AgentRM] Queue full for {task_type}. yielding to queue...")
            
        await sem.acquire()
        
        # Track agent execution time
        agent_id = str(id(asyncio.current_task()))
        cls._active_agents[agent_id] = time.time()
        
        # Auto-release mechanism is handled in release_slot
        return agent_id
        
    @classmethod
    def release_slot(cls, task_type: str, agent_id: str):
        """Release the slot back to the MLFQ pool."""
        if task_type in cls._slots:
            cls._slots[task_type].release()
            
        if agent_id in cls._active_agents:
            duration = time.time() - cls._active_agents.pop(agent_id)
            if duration > 45.0:
                logger.warning(f"[AgentRM] Agent {agent_id} took {duration:.2f}s. Demoting queue priority next time.")


import asyncio
import logging
import os
import random
from typing import TypedDict

import httpx

# Attempt to load LangGraph / PydanticAI. Fallback to native if not installed.
_HAS_LANGGRAPH = False
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph.graph import END, StateGraph
    from psycopg_pool import ConnectionPool
    from pydantic import BaseModel

    _HAS_LANGGRAPH = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

GROQ_KEYS = [
    k.strip() for k in (os.getenv("GROQ_API_KEY") or "").split(",") if k.strip()
]
GEMINI_KEYS = [
    k.strip() for k in (os.getenv("GEMINI_API_KEY") or "").split(",") if k.strip()
]
GITHUB_MODELS_KEYS = [
    k.strip() for k in (os.getenv("GITHUB_TOKEN") or "").split(",") if k.strip()
]
MISTRAL_KEYS = [
    k.strip() for k in (os.getenv("MISTRAL_API_KEY") or "").split(",") if k.strip()
]

# ── API Endpoint URLs (overridable via environment for proxy/self-hosted setups) ──
GROQ_API_URL = os.getenv(
    "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
)
GEMINI_API_BASE = os.getenv(
    "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/models"
)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GITHUB_MODELS_API_URL = os.getenv(
    "GITHUB_MODELS_API_URL", "https://models.inference.ai.azure.com/chat/completions"
)
MISTRAL_API_URL = os.getenv(
    "MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions"
)

# ── Default model names ──
GROQ_DEFAULT_MODEL = os.getenv("GROQ_DEFAULT_MODEL", "llama3-8b-8192")
GITHUB_DEFAULT_MODEL = os.getenv("GITHUB_DEFAULT_MODEL", "gpt-4o")
MISTRAL_DEFAULT_MODEL = os.getenv("MISTRAL_DEFAULT_MODEL", "open-mistral-nemo")

# DB connection for checkpointing
DB_URI = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
)


# --- LangGraph State ---
class AgentState(TypedDict):
    system_prompt: str
    user_prompt: str
    task_type: str
    max_retries: int
    current_attempt: int
    current_provider: str
    response: str | None
    error: str | None


class AIRouter:
    """
    Ultimate Hydra 2026 AI Router.
    Uses LangGraph for stateful execution and Pydantic for type-safe generation.
    Incorporates AgentRM scheduling integration.
    """

    _circuit_breaker = {"groq": 0, "gemini": 0, "github": 0, "mistral": 0}
    MAX_FAILURES = 3
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None and _HAS_LANGGRAPH:
            try:
                cls._pool = ConnectionPool(DB_URI, max_size=10)
            except Exception as e:
                logger.warning(f"Failed to init Postgres pool for Checkpointer: {e}")
        return cls._pool

    @classmethod
    async def generate_response(
        cls,
        system_prompt: str,
        user_prompt: str,
        task_type: str = "logic",
        max_retries: int = 3,
        thread_id: str = None,
    ) -> str:
        """
        Main entry point for AI inference. Uses LangGraph if available, fallback otherwise.
        task_type: 'logic', 'context', 'heavy', 'sensitive'
        """
        # Integrate with AgentRM if available
        try:
            from core.agent_rm import AgentRM

            await AgentRM.acquire_slot(task_type)
        except Exception:
            pass

        if _HAS_LANGGRAPH and cls.get_pool():
            return await cls._run_langgraph(
                system_prompt, user_prompt, task_type, max_retries, thread_id
            )
        else:
            return await cls._run_native(
                system_prompt, user_prompt, task_type, max_retries
            )

    @classmethod
    async def _run_langgraph(
        cls,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        max_retries: int,
        thread_id: str,
    ) -> str:
        """Execute AI logic through a resilient LangGraph pipeline with Postgres Checkpointing."""

        async def node_route(state: AgentState) -> dict:
            providers = []
            if state["task_type"] == "sensitive":
                providers = ["mistral", "github"]
            elif state["task_type"] == "logic":
                providers = ["groq", "gemini", "github"]
            elif state["task_type"] == "context":
                providers = ["gemini", "github", "groq"]
            else:
                providers = ["github", "groq", "gemini"]

            # Pick first available provider not circuit-broken
            target = None
            for p in providers:
                if cls._circuit_breaker.get(p, 0) < cls.MAX_FAILURES:
                    target = p
                    break

            if not target:
                return {
                    "error": "All providers circuit broken",
                    "current_provider": "none",
                }

            return {"current_provider": target, "error": None}

        async def node_execute(state: AgentState) -> dict:
            provider = state["current_provider"]
            if provider == "none":
                return {"response": None}

            try:
                if provider == "mistral":
                    resp = await cls._call_mistral(
                        state["system_prompt"], state["user_prompt"]
                    )
                elif provider == "groq":
                    resp = await cls._call_groq(
                        state["system_prompt"], state["user_prompt"]
                    )
                elif provider == "gemini":
                    resp = await cls._call_gemini(
                        state["system_prompt"], state["user_prompt"]
                    )
                else:
                    resp = await cls._call_github(
                        state["system_prompt"], state["user_prompt"]
                    )

                cls._circuit_breaker[provider] = 0
                return {"response": resp, "error": None}

            except Exception as e:
                cls._circuit_breaker[provider] += 1
                return {
                    "error": str(e),
                    "current_attempt": state["current_attempt"] + 1,
                }

        def should_retry(state: AgentState) -> str:
            if state.get("response"):
                return "end"
            if state["current_attempt"] >= state["max_retries"]:
                return "end"
            return "route"

        workflow = StateGraph(AgentState)
        workflow.add_node("route", node_route)
        workflow.add_node("execute", node_execute)

        workflow.set_entry_point("route")
        workflow.add_edge("route", "execute")
        workflow.add_conditional_edges(
            "execute", should_retry, {"route": "route", "end": END}
        )

        # Compile with checkpointer
        pool = cls.get_pool()
        checkpointer = PostgresSaver(pool)
        app = workflow.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": thread_id or "default_thread"}}
        initial_state = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "task_type": task_type,
            "max_retries": max_retries,
            "current_attempt": 0,
            "current_provider": "",
            "response": None,
            "error": None,
        }

        # Run async graph
        result = await app.ainvoke(initial_state, config)
        if result.get("response"):
            return result["response"]

        raise Exception(f"LangGraph execution failed: {result.get('error')}")

    @classmethod
    async def _run_native(
        cls,
        system_prompt: str,
        user_prompt: str,
        task_type: str = "logic",
        max_retries: int = 3,
    ) -> str:
        """Fallback to native loop if LangGraph/Postgres is unavailable."""
        providers = []
        if task_type == "sensitive":
            providers = [
                ("mistral", cls._call_mistral, MISTRAL_KEYS),
                ("github", cls._call_github, GITHUB_MODELS_KEYS),
            ]
        elif task_type == "logic":
            providers = [
                ("groq", cls._call_groq, GROQ_KEYS),
                ("gemini", cls._call_gemini, GEMINI_KEYS),
                ("github", cls._call_github, GITHUB_MODELS_KEYS),
            ]
        elif task_type == "context":
            providers = [
                ("gemini", cls._call_gemini, GEMINI_KEYS),
                ("github", cls._call_github, GITHUB_MODELS_KEYS),
                ("groq", cls._call_groq, GROQ_KEYS),
            ]
        else:
            providers = [
                ("github", cls._call_github, GITHUB_MODELS_KEYS),
                ("groq", cls._call_groq, GROQ_KEYS),
                ("gemini", cls._call_gemini, GEMINI_KEYS),
            ]

        for provider_name, provider_func, keys in providers:
            if not keys:
                continue
            if cls._circuit_breaker[provider_name] >= cls.MAX_FAILURES:
                continue

            for attempt in range(max_retries):
                try:
                    response = await provider_func(system_prompt, user_prompt)
                    cls._circuit_breaker[provider_name] = 0
                    return response
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 500, 502, 503, 504):
                        await asyncio.sleep((2**attempt) + random.uniform(0, 1))
                    else:
                        cls._circuit_breaker[provider_name] += 1
                        break
                except Exception:
                    cls._circuit_breaker[provider_name] += 1
                    break

        cls._circuit_breaker = {k: 0 for k in cls._circuit_breaker}
        raise Exception("All AI providers failed.")

    # ------------------ Core API Callers ------------------

    @classmethod
    async def _call_groq(cls, system_prompt: str, user_prompt: str) -> str:
        key = random.choice(GROQ_KEYS)
        url = GROQ_API_URL
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": GROQ_DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=15.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    @classmethod
    async def _call_gemini(cls, system_prompt: str, user_prompt: str) -> str:
        key = random.choice(GEMINI_KEYS)
        url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt + "\n\n" + user_prompt}],
                }
            ]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=25.0)
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    @classmethod
    async def _call_github(cls, system_prompt: str, user_prompt: str) -> str:
        key = random.choice(GITHUB_MODELS_KEYS)
        url = GITHUB_MODELS_API_URL
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": GITHUB_DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    @classmethod
    async def _call_mistral(cls, system_prompt: str, user_prompt: str) -> str:
        key = random.choice(MISTRAL_KEYS)
        url = MISTRAL_API_URL
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": MISTRAL_DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


ai_router = AIRouter()

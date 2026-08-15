"""
JobHunt Pro v16.2 — Unified Router Facade
=========================================
Consolidation facade that unifies the fragmented AI routing and email dispatch
layers behind a single, clean, backward-compatible interface.

This module does NOT delete or rewrite the underlying engines. Instead it:
  1. Exposes a single `UnifiedAIRouter` that delegates to the best available
     router (DynamicAIRouter for latency-aware routing, AIRouter for the
     LangGraph/native pipeline) with automatic fallback.
  2. Exposes a single `UnifiedEmailDispatcher` that unifies the
     EmailRotatorPool (quota-aware SMTP pool) and CascadingSmtpEngine
     (multi-provider failover + spintax) behind one `send()` API.
  3. Provides module-level singletons for drop-in usage.

All existing imports (`core.ai_router`, `core.ai_router_dynamic`,
`core.email_rotator_pool`, `core.cascading_smtp_engine`) remain fully
functional — this facade simply gives new code a single entry point.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Unified AI Router
# ---------------------------------------------------------------------------
class UnifiedAIRouter:
    """Single entry point for all LLM routing.

    Delegates to the latency-aware DynamicAIRouter when available, otherwise
    falls back to the classic AIRouter pipeline. Provides a uniform async
    `generate()` API with complexity classification and failover.
    """

    def __init__(self) -> None:
        self._dynamic: Any = None
        self._classic: Any = None
        self._loaded = False

    def _load(self) -> None:
        """Lazily import the underlying routers to avoid circular imports."""
        if self._loaded:
            return
        try:
            from core.ai_router_dynamic import DynamicAIRouter, TaskComplexity  # noqa: F401
            self._dynamic = DynamicAIRouter()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("DynamicAIRouter unavailable: %s", exc)
        try:
            from core.ai_router import AIRouter
            self._classic = AIRouter
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("AIRouter unavailable: %s", exc)
        self._loaded = True

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: str = "logic",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        complexity_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a response using the best available router.

        Returns a dict with keys: success, response, provider, latency_ms,
        and (when dynamic routing is used) complexity.
        """
        self._load()
        start = time.time()

        # 1) Prefer the latency-aware dynamic router.
        if self._dynamic is not None:
            try:
                result = await self._dynamic.route_and_execute(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    complexity_override=complexity_override,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if result and result.get("success"):
                    result["latency_ms"] = round((time.time() - start) * 1000, 2)
                    return result
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Dynamic router failed, falling back: %s", exc)

        # 2) Fall back to the classic AIRouter pipeline.
        if self._classic is not None:
            try:
                response = await self._classic.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    task_type=task_type,
                )
                return {
                    "success": True,
                    "response": response,
                    "provider": "classic",
                    "latency_ms": round((time.time() - start) * 1000, 2),
                    "complexity": complexity_override or "standard",
                }
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Classic router failed: %s", exc)

        return {
            "success": False,
            "response": "",
            "provider": None,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "error": "No AI router available",
        }

    async def generate_text(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Convenience wrapper returning just the response string."""
        result = await self.generate(system_prompt, user_prompt, **kwargs)
        return result.get("response", "")


# ---------------------------------------------------------------------------
# Unified Email Dispatcher
# ---------------------------------------------------------------------------
class UnifiedEmailDispatcher:
    """Single entry point for all email sending.

    Delegates to the quota-aware EmailRotatorPool for bulk sending, and to the
    CascadingSmtpEngine for spintax + multi-provider failover. Provides a
    uniform `send()` API that returns (success, info).
    """

    def __init__(self) -> None:
        self._rotator: Any = None
        self._cascading: Any = None
        self._loaded = False

    def _load(self) -> None:
        """Lazily import the underlying email engines."""
        if self._loaded:
            return
        try:
            from core.email_rotator_pool import EmailRotatorPool
            self._rotator = EmailRotatorPool().load_config()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("EmailRotatorPool unavailable: %s", exc)
        try:
            from core.cascading_smtp_engine import CascadingSmtpEngine
            self._cascading = CascadingSmtpEngine()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("CascadingSmtpEngine unavailable: %s", exc)
        self._loaded = True

    async def send(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        from_email: Optional[str] = None,
        use_spintax: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """Send an email via the best available engine.

        Returns (success, info_dict). Tries the rotator pool first, then the
        cascading engine, then reports failure.
        """
        self._load()

        # 1) Prefer the quota-aware rotator pool.
        if self._rotator is not None:
            try:
                success, info = await self._rotator.send_email(
                    to_email=to_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                )
                if success:
                    return True, {"engine": "rotator", **info}
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Rotator send failed: %s", exc)

        # 2) Fall back to the cascading engine (with optional spintax).
        if self._cascading is not None:
            try:
                body = body_html or body_text
                if use_spintax:
                    from core.cascading_smtp_engine import SpintaxGenerator
                    body = SpintaxGenerator.spin(body)
                result = await self._cascading.dispatch_with_failover(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    from_email=from_email or "",
                )
                if result and result.get("success"):
                    return True, {"engine": "cascading", **result}
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Cascading send failed: %s", exc)

        return False, {"engine": None, "error": "No email engine available"}

    async def send_batch(
        self,
        recipients: list[dict[str, Any]],
        subject: str,
        body_template: str,
        use_spintax: bool = False,
        concurrency: int = 5,
    ) -> dict[str, Any]:
        """Send a batch of emails with bounded concurrency."""
        sem = asyncio.Semaphore(concurrency)
        results: list[tuple[bool, dict[str, Any]]] = []

        async def _send_one(rec: dict[str, Any]) -> None:
            async with sem:
                to_email = rec.get("to_email") or rec.get("email")
                if not to_email:
                    results.append((False, {"error": "missing recipient"}))
                    return
                body = body_template
                if rec.get("name"):
                    body = body.replace("{name}", rec["name"])
                if rec.get("company"):
                    body = body.replace("{company}", rec["company"])
                if rec.get("role"):
                    body = body.replace("{role}", rec["role"])
                ok, info = await self.send(
                    to_email=to_email,
                    subject=subject,
                    body_html=body,
                    use_spintax=use_spintax,
                )
                results.append((ok, info))

        await asyncio.gather(*(_send_one(r) for r in recipients))
        successes = sum(1 for ok, _ in results if ok)
        return {
            "total": len(recipients),
            "success": successes,
            "failed": len(recipients) - successes,
            "results": results,
        }


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
unified_ai_router = UnifiedAIRouter()
unified_email_dispatcher = UnifiedEmailDispatcher()


__all__ = [
    "UnifiedAIRouter",
    "UnifiedEmailDispatcher",
    "unified_ai_router",
    "unified_email_dispatcher",
]

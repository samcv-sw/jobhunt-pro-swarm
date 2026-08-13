"""
JobHunt Pro SaaS — Multi-LLM Dynamic Router (v2026.1)
Dynamic complexity classification, latency metrics, token cost optimization,
and 18-provider failover routing.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from core.llm_provider_pool import LLMProvider, llm_pool

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    LIGHTWEIGHT = "lightweight"    # Fast responses, low cost (Groq, Cerebras, SambaNova)
    STANDARD = "standard"          # Balanced tasks (Gemini 2.5, Llama 3.3, Qwen)
    DEEP_REASONING = "deep_reasoning" # Complex reasoning, coding, strategy (DeepSeek, Claude, GPT-4o)


class ProviderLatencyTracker:
    """Tracks latency (ms) and success rates for LLM providers in real-time."""

    def __init__(self):
        self._latencies: Dict[str, List[float]] = {}
        self._successes: Dict[str, int] = {}
        self._failures: Dict[str, int] = {}

    def record_response(self, provider_name: str, latency_ms: float, success: bool = True):
        if provider_name not in self._latencies:
            self._latencies[provider_name] = []
            self._successes[provider_name] = 0
            self._failures[provider_name] = 0

        self._latencies[provider_name].append(latency_ms)
        if len(self._latencies[provider_name]) > 50:
            self._latencies[provider_name].pop(0)

        if success:
            self._successes[provider_name] += 1
        else:
            self._failures[provider_name] += 1

    def get_avg_latency(self, provider_name: str) -> float:
        records = self._latencies.get(provider_name, [])
        if not records:
            return 9999.0
        return sum(records) / len(records)

    def get_health_score(self, provider_name: str) -> float:
        succ = self._successes.get(provider_name, 0)
        fail = self._failures.get(provider_name, 0)
        total = succ + fail
        if total == 0:
            return 100.0
        return (succ / total) * 100.0


latency_tracker = ProviderLatencyTracker()


class DynamicAIRouter:
    @property
    def provider_pool(self):
        try:
            from core.llm_provider_pool import get_llm_pool
            return get_llm_pool()
        except Exception:
            class DummyPool:
                async def complete(self, *args, **kwargs):
                    return "Fallback Text"
            return DummyPool()

    def classify_complexity(self, prompt: str, system_prompt: Optional[str] = None) -> TaskComplexity:
        """Classifies prompt complexity based on length, key terms, and intent."""
        full_text = f"{system_prompt or ''} {prompt}".lower()
        length = len(full_text)

        deep_keywords = [
            "code", "algorithm", "architecture", "refactor", "debug", "math",
            "reasoning", "complex", "strategy", "ats_analysis", "resume_parse", "optimize_cv"
        ]

        light_keywords = [
            "short", "greeting", "quick", "yes/no", "headline", "tagline", "bullet_point"
        ]

        if any(kw in full_text for kw in deep_keywords) or length > 2500:
            return TaskComplexity.DEEP_REASONING
        elif any(kw in full_text for kw in light_keywords):
            return TaskComplexity.LIGHTWEIGHT
        elif length < 50:
            return TaskComplexity.LIGHTWEIGHT
        return TaskComplexity.STANDARD

    def get_provider_priority(self, complexity: TaskComplexity) -> List[LLMProvider]:
        """Returns prioritized provider list matching task complexity."""
        if complexity == TaskComplexity.LIGHTWEIGHT:
            return [
                LLMProvider.GROQ,
                LLMProvider.CEREBRAS,
                LLMProvider.SAMBANOVA,
                LLMProvider.CLOUDFLARE,
                LLMProvider.GEMINI,
                LLMProvider.MISTRAL,
            ]
        elif complexity == TaskComplexity.DEEP_REASONING:
            return [
                LLMProvider.DEEPSEEK_API,
                LLMProvider.ANTHROPIC,
                LLMProvider.GITHUB_MODELS,
                LLMProvider.OPENROUTER,
                LLMProvider.QWEN,
                LLMProvider.NVIDIA,
                LLMProvider.GEMINI,
            ]
        else:
            return [
                LLMProvider.GEMINI,
                LLMProvider.GROQ,
                LLMProvider.MISTRAL,
                LLMProvider.DEEPINFRA,
                LLMProvider.TOGETHER,
                LLMProvider.FIREWORKS,
                LLMProvider.XAI,
            ]

    async def route_and_execute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        complexity_override: Optional[TaskComplexity] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Dynamically routes request to optimal LLM provider with failover and latency tracking.
        """
        complexity = complexity_override or self.classify_complexity(prompt, system_prompt)
        providers = self.get_provider_priority(complexity)

        providers_sorted = sorted(
            providers,
            key=lambda p: latency_tracker.get_avg_latency(p.value)
        )

        last_error = None
        sys_prompt = system_prompt or "You are a helpful AI assistant."
        for provider in providers_sorted:
            start_time = time.time()
            try:
                response_text = await self.provider_pool.complete(
                    system_prompt=sys_prompt,
                    user_prompt=prompt,
                    preferred_provider=provider,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                latency_ms = (time.time() - start_time) * 1000.0
                if response_text is not None:
                    latency_tracker.record_response(provider.value, latency_ms, success=True)
                    return {
                        "success": True,
                        "provider": provider.value,
                        "complexity": complexity.value,
                        "latency_ms": round(latency_ms, 2),
                        "response": response_text,
                    }
                else:
                    latency_tracker.record_response(provider.value, latency_ms, success=False)
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000.0
                latency_tracker.record_response(provider.value, latency_ms, success=False)
                logger.warning(f"DynamicAIRouter: Provider {provider.value} failed: {e}")
                last_error = str(e)

        start_time = time.time()
        try:
            fallback_text = await self.provider_pool.complete(
                system_prompt=sys_prompt,
                user_prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency_ms = (time.time() - start_time) * 1000.0
            return {
                "success": True,
                "provider": "fallback_pool",
                "complexity": complexity.value,
                "latency_ms": round(latency_ms, 2),
                "response": fallback_text or "No response",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"All dynamic routing providers failed. Last error: {last_error} | Fallback error: {e}",
                "complexity": complexity.value,
            }


dynamic_ai_router = DynamicAIRouter()

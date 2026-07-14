"""
JobHunt Pro v17.1 — Multi-Provider LLM Pool (17 providers, $0 cost!)
Rotates across 17 free-tier AI providers to avoid rate limits.
Supports: Groq, Gemini, HuggingFace, OpenRouter, DeepInfra, Together, Fireworks,
         Cerebras, SambaNova, Cloudflare Workers AI, Cohere, xAI/Grok,
         DeepSeek API, GitHub Models, Qwen (Alibaba), +2 backup.
ALL FREE TIERS — $0 permanent cost.
"""

import asyncio
import contextlib
import logging
import os
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

from core import semantic_cache
from core.edge_cache import edge_cache

logger = logging.getLogger(__name__)


class LLMRateLimitError(Exception):
    """Raised when an LLM provider hits a rate limit (429) or is exhausted."""
    def __init__(self, message: str, reset_time: float, provider: str):
        super().__init__(message)
        self.reset_time = reset_time
        self.provider = provider


def parse_groq_reset_time(reset_str: str) -> float:
    """
    Parses Groq's x-ratelimit-reset string format (e.g., '1.2s', '15ms', '6m15s')
    and returns the duration in float seconds.
    """
    if not reset_str:
        return 0.0

    reset_str = reset_str.strip().lower()

    try:
        return float(reset_str)
    except ValueError:
        pass

    if reset_str.endswith('ms'):
        val = reset_str[:-2]
        try:
            return float(val) / 1000.0
        except ValueError:
            return 0.0

    total_seconds = 0.0
    current_num = ""
    for char in reset_str:
        if char.isdigit() or char == '.':
            current_num += char
        elif char in ('h', 'm', 's'):
            multiplier = {'h': 3600, 'm': 60, 's': 1}.get(char, 1)
            if current_num:
                with contextlib.suppress(ValueError):
                    total_seconds += float(current_num) * multiplier
                current_num = ""
    return total_seconds


class LLMProvider(Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    DEEPINFRA = "deepinfra"
    TOGETHER = "together"
    FIREWORKS = "fireworks"
    CEREBRAS = "cerebras"
    SAMBANOVA = "sambanova"
    CLOUDFLARE = "cloudflare"
    COHERE = "cohere"
    XAI = "xai"
    DEEPSEEK_API = "deepseek_api"
    GITHUB_MODELS = "github_models"
    QWEN = "qwen"
    ANTHROPIC = "anthropic"
    DUMMY = "dummy"


@dataclass
class ProviderConfig:
    name: LLMProvider
    api_key_env: str
    base_url: str
    models: list[str]
    rate_limit_rpm: int  # requests per minute
    weight: int = 1  # higher = preferred
    daily_limit: int = 0  # 0 = unlimited

    def get_api_key(self) -> str:
        keys_str = os.getenv(self.api_key_env, "")
        if "," in keys_str:
            keys = [k.strip() for k in keys_str.split(",") if k.strip()]
            return random.choice(keys) if keys else ""
        return keys_str.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.get_api_key())


PROVIDER_CONFIGS = [
    # ═══ GROQ (free, 14 keys rotation) ═══
    ProviderConfig(
        name=LLMProvider.GROQ,
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1/chat/completions",
        models=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "deepseek-r1-distill-llama-70b",
        ],
        rate_limit_rpm=30,
        weight=3,
        daily_limit=14400,
    ),
    # ═══ GEMINI (free) ═══
    ProviderConfig(
        name=LLMProvider.GEMINI,
        api_key_env="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        models=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"],
        rate_limit_rpm=60,
        weight=10,
        daily_limit=1500,
    ),
    # ═══ HUGGINGFACE (free inference API) ═══
    ProviderConfig(
        name=LLMProvider.HUGGINGFACE,
        api_key_env="HUGGINGFACE_API_KEY",
        base_url="https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
        models=["meta-llama/Llama-3.2-3B-Instruct"],
        rate_limit_rpm=30,
        weight=1,
        daily_limit=1000,
    ),
    # ═══ OPENROUTER (free + community models) ═══
    ProviderConfig(
        name=LLMProvider.OPENROUTER,
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        models=[
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "deepseek/deepseek-r1:free",
            "mistralai/mistral-7b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
        ],
        rate_limit_rpm=30,
        weight=2,
        daily_limit=0,
    ),
    # ═══ DEEPINFRA (free tier — signup at deepinfra.com) ═══
    ProviderConfig(
        name=LLMProvider.DEEPINFRA,
        api_key_env="DEEPINFRA_API_KEY",
        base_url="https://api.deepinfra.com/v1/openai/chat/completions",
        models=[
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "google/gemma-2-9b-it",
        ],
        rate_limit_rpm=30,
        weight=2,
        daily_limit=0,
    ),
    # ═══ TOGETHER AI (free $1 credit, generous rate limits) ═══
    ProviderConfig(
        name=LLMProvider.TOGETHER,
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1/chat/completions",
        models=[
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x22B-Instruct-v0.1",
            "deepseek-ai/deepseek-llm-67b-chat",
        ],
        rate_limit_rpm=60,
        weight=2,
        daily_limit=0,
    ),
    # ═══ FIREWORKS AI (free tier) ═══
    ProviderConfig(
        name=LLMProvider.FIREWORKS,
        api_key_env="FIREWORKS_API_KEY",
        base_url="https://api.fireworks.ai/inference/v1/chat/completions",
        models=[
            "accounts/fireworks/models/llama-v3p1-70b-instruct",
            "accounts/fireworks/models/mixtral-8x22b-instruct",
        ],
        rate_limit_rpm=30,
        weight=2,
        daily_limit=0,
    ),
    # ═══ CEREBRAS (30 RPM FREE — fastest inference) ═══
    ProviderConfig(
        name=LLMProvider.CEREBRAS,
        api_key_env="CEREBRAS_API_KEY",
        base_url="https://api.cerebras.ai/v1/chat/completions",
        models=["llama3.1-70b", "llama-3.3-70b"],
        rate_limit_rpm=30,
        weight=5,
        daily_limit=14400,
    ),
    # ═══ SAMBANOVA (free tier — Llama 405B!) ═══
    ProviderConfig(
        name=LLMProvider.SAMBANOVA,
        api_key_env="SAMBANOVA_API_KEY",
        base_url="https://api.sambanova.ai/v1/chat/completions",
        models=[
            "Meta-Llama-3.1-405B-Instruct",
            "Meta-Llama-3.1-70B-Instruct",
            "Meta-Llama-3.1-8B-Instruct",
        ],
        rate_limit_rpm=20,
        weight=4,
        daily_limit=0,
    ),
    # ═══ CLOUDFLARE WORKERS AI (on your existing CF account — FREE) ═══
    ProviderConfig(
        name=LLMProvider.CLOUDFLARE,
        api_key_env="CLOUDFLARE_AI_GATEWAY_URL",
        base_url="https://gateway.ai.cloudflare.com/v1/{account_id}/jobhunt/workers-ai/chat/completions",
        models=[
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        ],
        rate_limit_rpm=30,
        weight=3,
        daily_limit=10000,
    ),
    # ═══ COHERE (free trial — 100 calls/min) ═══
    ProviderConfig(
        name=LLMProvider.COHERE,
        api_key_env="COHERE_API_KEY",
        base_url="https://api.cohere.ai/v1/chat",
        models=["command-r-plus", "command-r"],
        rate_limit_rpm=100,
        weight=2,
        daily_limit=0,
    ),
    # ═══ XAI / GROK (free tier) ═══
    ProviderConfig(
        name=LLMProvider.XAI,
        api_key_env="XAI_API_KEY",
        base_url="https://api.x.ai/v1/chat/completions",
        models=["grok-beta"],
        rate_limit_rpm=30,
        weight=1,
        daily_limit=0,
    ),
    # ═══ DEEPSEEK API (free tier — DeepSeek-V3, R1) ═══
    ProviderConfig(
        name=LLMProvider.DEEPSEEK_API,
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1/chat/completions",
        models=["deepseek-chat", "deepseek-reasoner"],
        rate_limit_rpm=30,
        weight=4,
        daily_limit=0,
    ),
    # ═══ GITHUB MODELS (free tier — Azure-hosted) ═══
    ProviderConfig(
        name=LLMProvider.GITHUB_MODELS,
        api_key_env="GITHUB_TOKEN",
        base_url="https://models.inference.ai.azure.com/chat/completions",
        models=["gpt-4o-mini", "Phi-3.5-mini-instruct", "Llama-3.3-70B-Instruct"],
        rate_limit_rpm=15,
        weight=3,
        daily_limit=0,
    ),
    # ═══ QWEN (Alibaba Cloud Model Studio — free tier) ═══
    ProviderConfig(
        name=LLMProvider.QWEN,
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        models=["qwen-turbo", "qwen-plus", "qwen-max"],
        rate_limit_rpm=60,
        weight=2,
        daily_limit=0,
    ),
    # ═══ ANTHROPIC (Claude 3.5 Sonnet) ═══
    ProviderConfig(
        name=LLMProvider.ANTHROPIC,
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1/messages",
        models=["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-latest"],
        rate_limit_rpm=5,
        weight=9,  # High weight for high-quality generation
        daily_limit=0,
    ),
    # ═══ DUMMY (for testing) ═══
    ProviderConfig(
        name=LLMProvider.DUMMY,
        api_key_env="",
        base_url="",
        models=["dummy"],
        rate_limit_rpm=1000,
        weight=-1,  # Lowest priority
        daily_limit=0,
    ),
]

# Pre-built weight lookup to avoid O(N) scan in sort_key lambdas
_PROVIDER_WEIGHT: dict = {cfg.name: cfg.weight for cfg in PROVIDER_CONFIGS}


class ProviderInstance:
    """Manages a single provider with rate limiting and quota tracking."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._request_times: list[float] = []
        self._daily_count = 0
        self._daily_reset = time.time()
        self._consecutive_failures = 0
        self._last_error: str | None = None
        self._available = True
        self._client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"Provider {config.name.value} initialized ({config.models[0]})")

    def _check_rate_limit(self) -> float:
        """Return seconds to wait before next request, 0 if OK."""
        now = time.time()
        # Clean old entries (older than 60s)
        cutoff = now - 60
        self._request_times = [t for t in self._request_times if t > cutoff]

        if len(self._request_times) >= self.config.rate_limit_rpm:
            wait = self._request_times[0] + 60 - now
            return max(wait, 1.0)

        return 0.0

    def _check_daily_limit(self) -> bool:
        """Check if daily quota is exhausted."""
        now = time.time()
        if now - self._daily_reset > 86400:
            self._daily_count = 0
            self._daily_reset = now
        return not (self.config.daily_limit > 0 and self._daily_count >= self.config.daily_limit)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str | None:
        """Send a completion request, respecting rate/daily limits."""
        if not self._available:
            return None
        if not self._check_daily_limit():
            self._available = False
            logger.warning(f"Provider {self.config.name.value} daily limit reached")
            return None

        if self.config.name == LLMProvider.DUMMY:
            return "I am very interested in this position and believe my skills make me an excellent fit. Please see my attached CV."

        # Rate limit wait
        wait = self._check_rate_limit()
        if wait > 0:
            if wait > 15:
                logger.debug(
                    f"Provider {self.config.name.value} rate limited, waiting {wait:.1f}s"
                )
                return None  # Don't block, let caller try another provider
            await asyncio.sleep(wait)

        model = model or self.config.models[0]
        url = self.config.base_url.format(model=model)
        api_key = self.config.get_api_key()

        if self.config.name == LLMProvider.GEMINI:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }
            if system_prompt:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_prompt}]
                }
            headers = {"Content-Type": "application/json"}
        elif self.config.name == LLMProvider.ANTHROPIC:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system_prompt:
                payload["system"] = system_prompt
        else:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

        try:
            response = await self._client.post(url, json=payload, headers=headers)
            self._request_times.append(time.time())

            # Parse and track Groq rate limit headers on successful response
            if self.config.name == LLMProvider.GROQ:
                remaining = response.headers.get("x-ratelimit-remaining")
                reset_str = response.headers.get("x-ratelimit-reset")
                groq_remaining = None
                if remaining is not None:
                    with contextlib.suppress(ValueError):
                        groq_remaining = int(remaining)
                if reset_str:
                    reset_time = parse_groq_reset_time(reset_str)
                    reset_at = time.time() + reset_time
                    # If remaining requests is 0, proactively cache the rate limit reset time
                    if remaining == "0" or groq_remaining == 0:
                        logger.warning(
                            f"Groq rate limit exhausted (remaining=0). Reset in {reset_time}s."
                        )
                        if edge_cache.enabled:
                            await edge_cache.set("groq_rate_limit_reset", str(reset_at), ex=int(reset_time) + 2)

            if response.status_code == 429:
                retry_after_sec = 5.0
                retry_after_header = response.headers.get("retry-after")
                if retry_after_header:
                    with contextlib.suppress(ValueError):
                        retry_after_sec = float(retry_after_header)

                # If Groq, prioritize x-ratelimit-reset
                if self.config.name == LLMProvider.GROQ:
                    reset_str = response.headers.get("x-ratelimit-reset")
                    if reset_str:
                        retry_after_sec = parse_groq_reset_time(reset_str)

                logger.warning(
                    f"Provider {self.config.name.value} 429, rate limited. Reset in {retry_after_sec}s."
                )

                # Store Groq rate limit in edge cache
                if self.config.name == LLMProvider.GROQ:
                    reset_at = time.time() + retry_after_sec
                    if edge_cache.enabled:
                        await edge_cache.set("groq_rate_limit_reset", str(reset_at), ex=int(retry_after_sec) + 2)

                # Temporarily add fake requests to trigger the rate limit wait logic for next calls
                for _ in range(self.config.rate_limit_rpm):
                    self._request_times.append(time.time() + retry_after_sec)

                raise LLMRateLimitError(
                    message=f"Provider {self.config.name.value} rate limited (429)",
                    reset_time=retry_after_sec,
                    provider=self.config.name.value
                )

            if response.status_code != 200:
                self._consecutive_failures += 1
                self._last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(
                    f"Provider {self.config.name.value} error: {self._last_error}"
                )
                if self._consecutive_failures > 5:
                    self._available = False
                return None

            self._consecutive_failures = 0
            self._daily_count += 1

            if self.config.name == LLMProvider.GEMINI:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    return (
                        candidates[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                    )
                return None
            elif self.config.name == LLMProvider.ANTHROPIC:
                data = response.json()
                content = data.get("content", [])
                if content and content[0].get("type") == "text":
                    return content[0].get("text", "")
                return None

            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

        except httpx.TimeoutException:
            self._consecutive_failures += 1
            logger.warning(f"Provider {self.config.name.value} timeout")
            return None
        except LLMRateLimitError:
            raise
        except Exception as e:
            self._consecutive_failures += 1
            self._last_error = str(e)
            logger.warning(f"Provider {self.config.name.value} exception: {e}")
            return None

    async def close(self):
        await self._client.aclose()


class LLMProviderPool:
    """
    Rotates across multiple free LLM providers.
    Automatically falls back on rate limits, errors, or quota exhaustion.
    """

    def __init__(self):
        self._providers: dict[LLMProvider, ProviderInstance] = {}
        self._health: dict[LLMProvider, bool] = {}
        self._last_used: dict[LLMProvider, float] = {}
        self._lock = asyncio.Lock()

    def initialize(self) -> "LLMProviderPool":
        """Create provider instances for all configured providers."""
        for cfg in PROVIDER_CONFIGS:
            if cfg.is_configured or cfg.name == LLMProvider.DUMMY:
                self._providers[cfg.name] = ProviderInstance(cfg)
                self._health[cfg.name] = True
                self._last_used[cfg.name] = 0.0
                logger.info(f"LLM provider active: {cfg.name.value}")
            else:
                logger.info(f"LLM provider skipped (no API key): {cfg.name.value}")

        if not self._providers:
            logger.warning(
                "No LLM providers configured! Set GROQ_API_KEY, "
                "GEMINI_API_KEY, HUGGINGFACE_API_KEY, or OPENROUTER_API_KEY in .env"
            )

        return self

    async def get_provider(
        self, preferred: LLMProvider | None = None
    ) -> ProviderInstance | None:
        """
        Get the best available provider (by preference, weight, health).
        This is the main entry point for obtaining a provider instance.
        """

        if not self._providers:
            return None

        candidates = list(self._providers.keys())

        def sort_key(p: LLMProvider) -> tuple:
            w = _PROVIDER_WEIGHT.get(p, 0)
            is_preferred = 0 if preferred and p == preferred else 1
            return (is_preferred, -w, self._last_used.get(p, 0))

        candidates.sort(key=sort_key)

        for name in candidates:
            if self._health.get(name, False):
                return self._providers[name]

        # All unhealthy — try a health check to revive one
        await self._health_check()
        for name in candidates:
            if self._health.get(name, False):
                return self._providers[name]

        return None

    async def rotate_on_failure(
        self, failed_provider: LLMProvider
    ) -> ProviderInstance | None:
        """
        Called when a provider fails. Marks it unhealthy and returns
        the next best available provider.
        """
        async with self._lock:
            self._health[failed_provider] = False
            instance = self._providers.get(failed_provider)
            if instance:
                instance._consecutive_failures = max(instance._consecutive_failures, 4)
            logger.info(
                f"Provider {failed_provider.value} marked unhealthy, rotating..."
            )

        # Return the next best healthy provider
        return await self.get_provider()

    async def check_quota(self, provider_name: LLMProvider) -> dict[str, Any]:
        """
        Check remaining quota for a specific provider.
        Returns {available, remaining, daily_used, daily_limit, rate_limit_rpm}.
        """
        instance = self._providers.get(provider_name)
        if not instance:
            return {"available": False, "error": "Provider not found"}

        cfg = next((c for c in PROVIDER_CONFIGS if c.name == provider_name), None)
        healthy = self._health.get(provider_name, False)

        return {
            "available": healthy and instance._available,
            "healthy": healthy,
            "daily_used": instance._daily_count,
            "daily_limit": cfg.daily_limit if cfg else 0,
            "rate_limit_rpm": cfg.rate_limit_rpm if cfg else 0,
            "consecutive_failures": instance._consecutive_failures,
            "last_error": instance._last_error,
        }

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        preferred_provider: LLMProvider | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str | None:
        """
        Send a completion request, rotating across providers on failure.
        Returns None if all providers fail.
        """

        if not self._providers:
            return None

        # Check semantic cache first
        try:
            cached = await asyncio.to_thread(semantic_cache.get_cached_response, user_prompt)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {e}")


        # Build ordered list of providers to try
        candidates = list(self._providers.keys())

        # Sort by: preferred first, then by weight (higher first), then by last_used
        def sort_key(p: LLMProvider) -> tuple:
            w = _PROVIDER_WEIGHT.get(p, 0)
            is_preferred = 0 if p == preferred_provider else 1
            return (is_preferred, -w, self._last_used.get(p, 0))

        candidates.sort(key=sort_key)

        last_rate_limit_err = None
        for provider_name in candidates:
            provider = self._providers[provider_name]
            if not self._health.get(provider_name, True):
                continue

            try:
                result = await provider.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except LLMRateLimitError as rle:
                logger.warning(
                    f"Provider {provider_name.value} rate limited: {rle}. Attempting fallback..."
                )
                last_rate_limit_err = rle
                provider._consecutive_failures += 1
                if provider._consecutive_failures > 3:
                    async with self._lock:
                        self._health[provider_name] = False
                continue

            async with self._lock:
                self._last_used[provider_name] = time.time()

            if result is not None:
                try:
                    await asyncio.to_thread(semantic_cache.save_to_cache, user_prompt, result)
                except Exception as e:
                    logger.warning(f"Semantic cache save failed: {e}")
                return result

            # Mark as unhealthy if consecutive failures accumulated
            if provider._consecutive_failures > 3:
                async with self._lock:
                    self._health[provider_name] = False
                logger.warning(f"Provider {provider_name.value} marked unhealthy")

        # Periodic health check revive
        await self._health_check()

        # If all failed and the last error was rate limiting, propagate it to Celery
        if last_rate_limit_err:
            raise last_rate_limit_err

        return None

    async def _health_check(self):
        """Attempt to revive unhealthy providers."""
        for provider_name, instance in self._providers.items():
            if not self._health.get(provider_name, True):
                # Quick test: simple completion
                result = await instance.complete(
                    system_prompt="Reply with OK",
                    user_prompt="Say OK",
                    max_tokens=10,
                )
                if result is not None:
                    async with self._lock:
                        self._health[provider_name] = True
                    logger.info(f"Provider {provider_name.value} revived")

    async def get_health_status(self) -> dict[str, Any]:
        status = {}
        for name, instance in self._providers.items():
            cfg = next((c for c in PROVIDER_CONFIGS if c.name == name), None)
            status[name.value] = {
                "healthy": self._health.get(name, False),
                "model": cfg.models[0] if cfg else "unknown",
                "daily_used": instance._daily_count,
                "daily_limit": cfg.daily_limit if cfg else 0,
                "consecutive_failures": instance._consecutive_failures,
                "last_error": instance._last_error,
            }
        return status

    async def close_all(self):
        for instance in self._providers.values():
            await instance.close()

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 5: Unified response method with provider metadata
    # Priority chain: Groq (llama-3.3-70b) → Gemini 1.5 Pro → Claude 3.5 Sonnet
    # Falls back on LLMRateLimitError or httpx.TimeoutException.
    # ─────────────────────────────────────────────────────────────────────────
    async def complete_with_metadata(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict:
        """
        Send a completion request through the Phase-5 priority fallback chain.

        Chain order:
            1. Groq       — llama-3.3-70b-versatile   (fastest, free)
            2. Gemini     — gemini-1.5-pro             (high quality, free tier)
            3. Anthropic  — claude-3-5-sonnet-20241022 (premium fallback)

        Returns a unified dict:
            {
                "text":        str,   # the generated text
                "provider":    str,   # which provider was used
                "tokens_used": int,   # approximate token count (prompt + output)
            }

        Raises RuntimeError if all three priority providers fail.
        """
        PRIORITY_CHAIN: list[tuple[LLMProvider, str]] = [
            (LLMProvider.GROQ,      "llama-3.3-70b-versatile"),
            (LLMProvider.GEMINI,    "gemini-1.5-pro"),
            (LLMProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"),
        ]

        errors: list[str] = []

        for provider_enum, model_name in PRIORITY_CHAIN:
            instance = self._providers.get(provider_enum)
            if instance is None:
                logger.info(
                    f"[LLMPool] Skipping {provider_enum.value} (not configured)"
                )
                errors.append(f"{provider_enum.value}: not configured")
                continue

            if not self._health.get(provider_enum, True):
                logger.info(
                    f"[LLMPool] Skipping {provider_enum.value} (marked unhealthy)"
                )
                errors.append(f"{provider_enum.value}: unhealthy")
                continue

            logger.info(
                f"[LLMPool] Attempting provider={provider_enum.value} "
                f"model={model_name}"
            )
            try:
                text = await instance.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except LLMRateLimitError as exc:
                logger.warning(
                    f"[LLMPool] {provider_enum.value} rate-limited "
                    f"(reset={exc.reset_time:.1f}s) — falling back"
                )
                async with self._lock:
                    self._health[provider_enum] = False
                errors.append(f"{provider_enum.value}: rate-limited")
                continue
            except Exception as exc:
                logger.warning(
                    f"[LLMPool] {provider_enum.value} exception: {exc} — falling back"
                )
                errors.append(f"{provider_enum.value}: {exc}")
                continue

            if text is None:
                logger.warning(
                    f"[LLMPool] {provider_enum.value} returned None — falling back"
                )
                errors.append(f"{provider_enum.value}: returned None")
                continue

            # ── success ──────────────────────────────────────────────────────
            # Approximate token count: ~4 chars/token heuristic
            prompt_chars = len(system_prompt) + len(user_prompt)
            output_chars = len(text)
            tokens_used = max(1, (prompt_chars + output_chars) // 4)

            logger.info(
                f"[LLMPool] Success: provider={provider_enum.value} "
                f"model={model_name} tokens≈{tokens_used}"
            )
            async with self._lock:
                self._last_used[provider_enum] = time.time()

            return {
                "text": text,
                "provider": provider_enum.value,
                "tokens_used": tokens_used,
            }

        raise RuntimeError(
            f"All priority LLM providers failed. Errors: {'; '.join(errors)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton — initialised lazily on first access
# ─────────────────────────────────────────────────────────────────────────────
_llm_pool_instance: "LLMProviderPool | None" = None


def get_llm_pool() -> "LLMProviderPool":
    """Return the global LLMProviderPool singleton, initialising it on first call."""
    global _llm_pool_instance
    if _llm_pool_instance is None:
        _llm_pool_instance = LLMProviderPool().initialize()
    return _llm_pool_instance


# Convenience alias
llm_pool = None  # Set via get_llm_pool() at app startup to avoid import-time side-effects

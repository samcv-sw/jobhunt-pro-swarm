import asyncio
import hashlib
import json
import logging

from core.ai_tailor import AITailor
from core.edge_cache import cache_llm_result, edge_cache, get_cached_llm_result
from core.llm_provider_pool import LLMProvider, LLMProviderPool

logger = logging.getLogger(__name__)

# Initialize LLM Provider Pool
llm_pool = LLMProviderPool().initialize()

# Registry for dynamic tone guidelines
TONE_REGISTRY = {
    "professional": "polished, formal, professional, and well-structured, highlighting experience and qualifications objectively and elegantly.",
    "confident": "high energy, assertive, confident, bold, showing strong self-assurance, demonstrating direct capability and clear value proposition.",
    "creative": "engaging, storytelling, creative, unique, capturing attention with a compelling narrative and expressive language while showing personality.",
}


async def generate_smart_cover_letter(job_description: str, user_cv: str) -> dict:
    """
    Leverages LLMProviderPool to instantly generate
    a hyper-personalized cover letter. Enforces JSON mode for strict schema adherence.
    """
    logger.info("Initializing LLMProviderPool inference for Cover Letter generation...")

    # ── LLM-specific cache probe (truncated key, 1-hour TTL) ────────────────
    # Uses get_cached_llm_result which hashes only the first 500/200 chars so
    # cosmetically identical requests collapse to a single LLM call.
    try:
        llm_cached = await get_cached_llm_result(job_description, user_cv)
        if llm_cached is not None:
            logger.info('{"msg": "generate_smart_cover_letter LLM cache HIT"}')
            return llm_cached
    except Exception as _llm_cache_err:
        logger.warning('{"msg": "LLM cache probe failed", "error": "%s"}', _llm_cache_err)

    # ── Full-hash edge-cache probe (24-hour TTL, existing behaviour) ─────────
    # Build unique cache key using SHA-256 of user_cv + job_description
    raw_key = f"{user_cv}:{job_description}"
    cache_key = f"cover_letter:{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()}"

    # Try retrieving from edge cache
    try:
        if edge_cache.enabled:
            cached_val = await edge_cache.get(cache_key)
            if cached_val:
                logger.info("Cover letter cache hit! Returning in < 100ms.")
                if isinstance(cached_val, bytes):
                    cached_val = cached_val.decode("utf-8")
                return json.loads(cached_val)
    except Exception as cache_err:
        logger.warning(f"Failed to fetch cover letter from edge cache: {cache_err}")

    system_prompt = """
    You are an expert executive recruiter and copywriter.
    Your task is to write a highly persuasive, concise cover letter based on the provided CV and Job Description.
    You MUST output valid JSON ONLY, adhering exactly to the following schema:
    {
        "subject": "Compelling subject line for the email",
        "body": "The full text of the cover letter, using proper paragraph breaks (\\n\\n)"
    }
    """

    user_prompt = f"""
    Job Description:
    {job_description}

    User CV:
    {user_cv}
    """

    try:
        response_content = await llm_pool.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_provider=LLMProvider.GROQ,
            temperature=0.5,
            max_tokens=1024,
        )

        if not response_content:
            raise Exception("All LLM providers failed to complete request.")

        # Clean/Extract JSON and parse it
        json_str = AITailor._extract_json(response_content)
        parsed_response = json.loads(json_str)

        logger.info("LLMProviderPool inference completed successfully in JSON format.")

        # Save to edge cache (cache for 24 hours = 86400 seconds)
        try:
            if edge_cache.enabled:
                await edge_cache.set(cache_key, json.dumps(parsed_response), ex=86400)
        except Exception as cache_err:
            logger.warning(f"Failed to save generated cover letter to edge cache: {cache_err}")

        # Fire-and-forget: also populate the shorter LLM-specific cache key (1-hour TTL).
        # Never awaited directly so a cache failure cannot block the response.
        try:
            asyncio.ensure_future(
                cache_llm_result(job_description, user_cv, parsed_response, ttl=3600)
            )
        except Exception as _ef_err:
            logger.warning('{"msg": "LLM cache ensure_future failed", "error": "%s"}', _ef_err)

        return parsed_response

    except Exception as e:
        logger.error(f"Failed to generate cover letter: {e}")
        raise


async def generate_smart_cover_letter_stream(job_description: str, user_cv: str, tone: str):
    """
    Async generator yielding text chunks wrapped in SSE format (JSON-encoded delta).
    """
    logger.info(
        f"Initializing LLMProviderPool streaming inference for Cover letter with tone: {tone}..."
    )

    # Build unique cache key using SHA-256 of user_cv + job_description
    raw_key = f"{user_cv}:{job_description}"
    cache_key = f"cover_letter:{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()}"

    # Try retrieving from edge cache first
    try:
        if edge_cache.enabled:
            cached_val = await edge_cache.get(cache_key)
            if cached_val:
                logger.info("Cover letter stream cache hit! Streaming cached content.")
                if isinstance(cached_val, bytes):
                    cached_val = cached_val.decode("utf-8")
                parsed = json.loads(cached_val)
                body_text = parsed.get("body", "")
                # Yield in chunks
                chunk_size = 20
                for i in range(0, len(body_text), chunk_size):
                    chunk = body_text[i : i + chunk_size]
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    await asyncio.sleep(0.01)
                return
    except Exception as cache_err:
        logger.warning(f"Failed to stream from edge cache: {cache_err}")

    # Retrieve tone guidelines or default to professional
    tone_guidelines = TONE_REGISTRY.get(tone.lower(), TONE_REGISTRY["professional"])

    system_prompt = f"""
    You are an expert executive recruiter and copywriter.
    Your task is to write a highly persuasive, concise cover letter based on the provided CV and Job Description.
    You MUST write the cover letter using a tone that is {tone_guidelines}.
    Write the cover letter content directly. Do not output JSON. Do not include introductory/outro comments or conversational filler.
    """

    user_prompt = f"""
    Job Description:
    {job_description}

    User CV:
    {user_cv}
    """

    try:
        response_content = await llm_pool.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_provider=LLMProvider.GROQ,
            temperature=0.6,
            max_tokens=1024,
        )

        if not response_content:
            raise Exception("All LLM providers failed to complete request.")

        # Yield in chunks to simulate streaming
        chunk_size = 20
        for i in range(0, len(response_content), chunk_size):
            chunk = response_content[i : i + chunk_size]
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.01)

        # Cache the generated content (format as subject & body, using a generic subject)
        try:
            if edge_cache.enabled:
                cached_data = {"subject": "Cover Letter", "body": response_content}
                await edge_cache.set(cache_key, json.dumps(cached_data), ex=86400)
        except Exception as cache_err:
            logger.warning(f"Failed to cache generated stream: {cache_err}")

    except Exception as e:
        logger.error(f"Failed to stream cover letter: {e}")
        raise

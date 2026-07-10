# -*- coding: utf-8 -*-
# Fix test_process_single_job_llm_fallback: AsyncSession mock setup was broken
# The mock Session class (AsyncMock) returns a coroutine when called,
# but the code does `async with requests.AsyncSession() as session`
# so __aenter__ is awaited on the coroutine itself -> crash.
#
# Fix: make AsyncSession a regular MagicMock, set its .return_value as the
# session instance with proper __aenter__/__aexit__.

with open('tests/test_stealth_parser_and_fallbacks.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """    # HTML that has NO bot-detection keywords → curl_cffi path runs and keeps the HTML
    async def mock_session_get(url, timeout=None, **kwargs):
        m = MagicMock()
        # No CF/turnstile/challenge keywords — so bot detection is NOT triggered
        m.text = "<html><body>We are hiring: Python developer needed. Skills: Python, Django, AWS. Company: LLM Corp. Visit example.com/python-llm</body></html>"
        return m

    mock_session_instance = AsyncMock()
    mock_session_instance.get = mock_session_get
    mock_session_instance.headers = {}

    async def mock_session_enter():
        return mock_session_instance

    mock_session_cls = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(side_effect=mock_session_enter)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)

    # Patch the lazy-imported AITailor in core.ai_tailor so that when
    # _parse_html_with_llm does "from core.ai_tailor import AITailor", it gets
    # our patched version.
    import core.ai_tailor as ai_tailor_mod
    original_call_ai = ai_tailor_mod.AITailor._call_ai

    async def patched_call_ai(self, prompt, max_tokens=None, temperature=None):
        return await mock_llm_sideeffect(prompt, max_tokens, temperature)

    ai_tailor_mod.AITailor._call_ai = patched_call_ai

    try:
        with patch.object(si_module, "HAS_CFFI", True), \\
             patch.object(si_module.requests, "AsyncSession", return_value=mock_session_cls()):
            jobs = await process_single_job("https://example.com/job-raw")"""

new_block = """    # HTML with no bot-detection keywords → curl_cffi returns it, LLM fallback fires
    mock_response = MagicMock()
    mock_response.text = (
        "<html><body>We are hiring: Python developer needed. "
        "Skills: Python, Django, AWS. Company: LLM Corp. "
        "Visit example.com/python-llm</body></html>"
    )

    # Build the mock session instance that AsyncSession() returns
    mock_session_instance = MagicMock()
    mock_session_instance.headers = {}
    mock_session_instance.get = AsyncMock(return_value=mock_response)

    # AsyncSession is used as `async with AsyncSession() as session:`
    # -> __aenter__ is awaited on the instance, must return the session
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)

    # Make AsyncSession a regular MagicMock whose .return_value IS the session
    mock_async_session_cls = MagicMock(return_value=mock_session_instance)

    # Patch the lazy-imported AITailor in core.ai_tailor so that when
    # _parse_html_with_llm does "from core.ai_tailor import AITailor", it gets
    # our patched version.
    import core.ai_tailor as ai_tailor_mod
    original_call_ai = ai_tailor_mod.AITailor._call_ai

    async def patched_call_ai(self, prompt, max_tokens=None, temperature=None):
        return await mock_llm_sideeffect(prompt, max_tokens, temperature)

    ai_tailor_mod.AITailor._call_ai = patched_call_ai

    try:
        with patch.object(si_module, "HAS_CFFI", True), \\
             patch.object(si_module.requests, "AsyncSession", mock_async_session_cls):
            jobs = await process_single_job("https://example.com/job-raw")"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('tests/test_stealth_parser_and_fallbacks.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found!")
    # Show what we have around that area
    idx = content.find("mock_session_get")
    print(repr(content[max(0,idx-200):idx+200]))

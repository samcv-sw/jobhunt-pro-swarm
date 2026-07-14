import logging
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger("add_cache")

filepath = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\core\llm_provider_pool.py"

try:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "core.semantic_cache" not in content:
        # Add import
        content = content.replace("import os", "import os\nfrom core import semantic_cache")

        # Add cache read before LLM request
        cache_read = """
            if not self._providers:
                return None

            # Check semantic cache first
            try:
                cached = semantic_cache.get_cached_response(user_prompt)
                if cached:
                    return cached
            except Exception as e:
                logger.warning(f"Semantic cache lookup failed: {e}")
    """
        content = content.replace("        if not self._providers:\n            return None", cache_read)
        
        # Add cache write after LLM request success
        cache_write = """
                if result is not None:
                    try:
                        semantic_cache.save_to_cache(user_prompt, result)
                    except Exception as e:
                        logger.warning(f"Semantic cache save failed: {e}")
                    return result
    """
        content = content.replace("            if result is not None:\n                return result", cache_write)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Semantic caching integrated into llm_provider_pool.py")
    else:
        logger.info("Semantic caching already integrated.")
except Exception as e:
    logger.error(f"Failed to integrate caching: {e}")


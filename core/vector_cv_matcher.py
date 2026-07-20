import logging
import re
from core.semantic_cache import get_embedding

logger = logging.getLogger(__name__)

def select_relevant_cv_sections(cv_text: str, job_description: str, max_sections: int = 6) -> str:
    """Select the most semantically relevant sections of the CV matching the job description using vector embeddings.
    
    Filters out irrelevant parts of the CV to reduce prompt token size for LLM cover letter tailoring.
    """
    if not cv_text or not job_description:
        return cv_text

    # Normalize newlines and split CV into sections/paragraphs
    sections = [s.strip() for s in re.split(r'\n\s*\n+', cv_text.strip()) if s.strip()]
    if len(sections) <= max_sections:
        logger.debug("[CV-MATCHER] CV has %d sections, which is <= max_sections (%d). Using full CV.", len(sections), max_sections)
        return cv_text

    # Get job description embedding
    job_emb = get_embedding(job_description[:3000])  # limit job description to first 3000 chars for embedding
    if not job_emb:
        logger.warning("[CV-MATCHER] Failed to retrieve job description embedding. Falling back to full CV.")
        return cv_text

    # Helper for cosine similarity
    def _cosine_similarity(v1, v2):
        if not v1 or not v2:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    scored_sections = []
    # Always preserve the first section (usually contact details, summary) to ensure LLM has context
    contact_section = sections[0]
    
    for sec in sections[1:]:
        # Calculate embedding for this CV section
        sec_emb = get_embedding(sec[:2000])
        if sec_emb:
            sim = _cosine_similarity(sec_emb, job_emb)
            scored_sections.append((sim, sec))
        else:
            scored_sections.append((0.0, sec))

    # Sort sections by similarity score descending
    scored_sections.sort(key=lambda x: x[0], reverse=True)

    # Pick top N-1 sections (leaving 1 slot for contact section)
    top_sections = [contact_section] + [sec for _, sec in scored_sections[:max_sections - 1]]

    # Reassemble selected sections in their original order of appearance
    ordered_sections = []
    for original_sec in sections:
        if original_sec in top_sections:
            ordered_sections.append(original_sec)

    selected_cv = "\n\n".join(ordered_sections)
    reduction = 100 * (1 - len(selected_cv) / len(cv_text))
    logger.info("[CV-MATCHER] Selected %d/%d CV sections. Reduced CV string length by %.1f%%", len(ordered_sections), len(sections), reduction)
    return selected_cv

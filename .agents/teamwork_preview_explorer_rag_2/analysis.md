# Vector DB (RAG) Integration Analysis Report

## Summary
This report analyzes `backend/ai_engine.py` and details the implementation plan for local Vector DB (RAG) integration to retrieve past cover letters and writing styles for personalized generation. Due to CODE_ONLY network constraints, we propose a completely local, offline-capable architecture using Qdrant (or Chroma) in-memory/disk-based client combined with a deterministic offline pseudo-embedding function.

---

## 1. Examination of `backend/ai_engine.py`

The current implementation of `backend/ai_engine.py` is a simple wrapper around the `AsyncGroq` client. It contains:
- **`TONE_REGISTRY`**: A dictionary containing description strings for `professional`, `confident`, and `creative` tones.
- **`generate_smart_cover_letter(job_description: str, user_cv: str) -> dict`**:
  - Uses the `llama3-70b-8192` model with JSON mode to ensure the output conforms to a schema containing `subject` and `body`.
  - The prompt consists of a static system prompt setting the role, and a user prompt with the target `job_description` and `user_cv`.
- **`generate_smart_cover_letter_stream(job_description: str, user_cv: str, tone: str)`**:
  - An async generator that streams the cover letter chunks in SSE format (`data: {"chunk": "..."}\n\n`).
  - Uses a system prompt containing tone instructions and a user prompt with the target `job_description` and `user_cv`.

### Key Limitations & Gaps for RAG Integration:
1. **Missing `user_id` Context**: Neither function currently accepts a `user_id` parameter. Since cover letters and writing styles are user-specific, we must pass the `user_id` from the authentication layer (extracted from the JWT in `verify_jwt`) down to the generation functions.
2. **Static Prompts**: The prompts are static and do not adapt to historical user data.
3. **No Automatic Ingestion**: Newly generated cover letters are not saved back to any database. For RAG to work, successful generations must be automatically ingested into the Vector DB.

---

## 2. Vector DB Query Mechanics & Offline Strategy

### A. Local Vector DB Choice: Qdrant vs Chroma
We recommend using **Qdrant** via the `qdrant-client` package for the following reasons:
1. **Zero-Configuration Local Storage**: Qdrant can run fully in-process using an in-memory database (`QdrantClient(":memory:")`) or persistent local folder (`QdrantClient(path="./qdrant_db")`), meaning no Docker container is required.
2. **Robust Concurrency**: Unlike Chroma's SQLite-backed storage which can suffer from database locks during concurrent writes in Celery worker processes, Qdrant's local engine uses write-ahead logging (WAL) and manages multi-threaded access safely.
3. **Filtering Support**: Qdrant has native support for combining semantic search with payload metadata filters (e.g., filtering search results by `user_id` before computing similarity).

### B. Offline Embedding Strategy (CODE_ONLY Mode)
Normally, vector databases require a model (like HuggingFace `sentence-transformers`) to generate embeddings. However, in a restricted CODE_ONLY network environment, downloading model weights at runtime is impossible.
We propose a **Deterministic Offline Pseudo-Embedding Function** that:
- Uses a deterministic hash projection method.
- Normalizes vectors to unit length so that Cosine Similarity (dot product) remains valid.
- Has zero external dependencies and does not make HTTP requests.
- Yields high similarity for documents sharing overlapping tokens (good for keyword and context matching).

---

## 3. Prompt Injection Strategy

To inject retrieved cover letters as context for writing styles, we use a few-shot learning approach:
1. **Format Past Cover Letters**: If similar cover letters are found for the user, we format them into a reference section.
2. **Inject into System Prompt**:
   - For `generate_smart_cover_letter`: We append a `## Style Reference & Past Cover Letters` section to the system prompt containing the examples.
   - For `generate_smart_cover_letter_stream`: We append the same reference section to the system prompt.
3. **Fallback Mechanism**: If no past cover letters exist in the vector database for the user, the prompt falls back gracefully to the default prompt, ensuring new users have a seamless experience.

---

## 4. Proposed API Structure & Implementations

To ensure code stability and separation of concerns, we recommend creating a new module `backend/vector_store.py` to encapsulate all vector DB actions, and modifying `backend/ai_engine.py` to call it.

### Proposed `backend/vector_store.py` (Complete, Copy-Paste Ready)
```python
import os
import hashlib
import numpy as np
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

# Initialize Qdrant Client (Uses persistent local storage)
DB_PATH = os.environ.get("VECTOR_DB_PATH", "./qdrant_db")
collection_name = "cover_letters"

# In-memory option for tests
if os.environ.get("TESTING") == "1":
    qdrant_client = QdrantClient(":memory:")
else:
    qdrant_client = QdrantClient(path=DB_PATH)

def generate_offline_embedding(text: str, dimension: int = 384) -> list[float]:
    """
    Generates a deterministic pseudo-embedding vector for text without external dependencies.
    Hashes tokens and projects them to a normalized 384-dimensional vector.
    This ensures Cosine Distance calculation is fully functional offline.
    """
    if not text:
        return [0.0] * dimension
        
    words = text.lower().split()
    vector = np.zeros(dimension)
    for word in words:
        h = hashlib.sha256(word.encode('utf-8')).hexdigest()
        seed = int(h[:8], 16)
        rng = np.random.default_rng(seed)
        word_vector = rng.standard_normal(dimension)
        vector += word_vector
        
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
        
    return vector.tolist()

def initialize_vector_db():
    """
    Creates the collection if it does not exist.
    """
    try:
        if not qdrant_client.collection_exists(collection_name=collection_name):
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logger.info(f"Initialized Qdrant collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant DB: {e}")

async def upsert_cover_letter(user_id: str, job_description: str, cover_letter_subject: str, cover_letter_body: str, tone: str):
    """
    Inserts a newly generated cover letter into the vector database.
    """
    initialize_vector_db()
    # Generate ID based on payload hash to prevent duplicates
    payload_str = f"{user_id}:{job_description[:50]}"
    point_id = hashlib.md5(payload_str.encode('utf-8')).hexdigest()
    
    embedding = generate_offline_embedding(job_description)
    
    point = PointStruct(
        id=point_id,
        vector=embedding,
        payload={
            "user_id": user_id,
            "job_description": job_description,
            "subject": cover_letter_subject,
            "body": cover_letter_body,
            "tone": tone
        }
    )
    
    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        logger.info(f"Successfully upserted cover letter for user {user_id} into vector DB.")
    except Exception as e:
        logger.error(f"Failed to upsert cover letter: {e}")

async def search_similar_cover_letters(user_id: str, query_text: str, top_k: int = 2) -> list[dict]:
    """
    Queries Qdrant for past cover letters matching the query_text, filtered by user_id.
    """
    initialize_vector_db()
    query_vector = generate_offline_embedding(query_text)
    
    # Metadata filter to ensure users only retrieve their own cover letters
    user_filter = Filter(
        must=[
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id)
            )
        ]
    )
    
    try:
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=user_filter,
            limit=top_k
        )
        
        results = []
        for hit in search_results:
            results.append(hit.payload)
        return results
    except Exception as e:
        logger.error(f"Failed to query vector DB: {e}")
        return []
```

---

### Proposed Updated `backend/ai_engine.py` (Complete, Copy-Paste Ready)
```python
import os
import json
import logging
import asyncio
from groq import AsyncGroq
from .vector_store import search_similar_cover_letters, upsert_cover_letter

logger = logging.getLogger(__name__)

# Initialize the Groq client
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY", "fallback-key-for-testing"),
)

# Registry for dynamic tone guidelines
TONE_REGISTRY = {
    "professional": "polished, formal, professional, and well-structured, highlighting experience and qualifications objectively and elegantly.",
    "confident": "high energy, assertive, confident, bold, showing strong self-assurance, demonstrating direct capability and clear value proposition.",
    "creative": "engaging, storytelling, creative, unique, capturing attention with a compelling narrative and expressive language while showing personality."
}

def build_rag_context_prompt(past_letters: list[dict]) -> str:
    """
    Formats retrieved past cover letters into a few-shot instruction block.
    """
    if not past_letters:
        return ""
        
    context = "\n\n## Style Reference & Past Cover Letters (Few-Shot Examples)\n"
    context += "Analyze the formatting, writing style, paragraph structure, and wording of the examples below. "
    context += "Ensure your new output matches this user's personal writing signature and structure while incorporating the new Job Description and CV.\n"
    
    for i, letter in enumerate(past_letters, 1):
        context += f"\n--- Reference Example {i} ---\n"
        context += f"Job Description:\n{letter.get('job_description', '')}\n"
        context += f"Cover Letter Subject:\n{letter.get('subject', 'N/A')}\n"
        context += f"Cover Letter Body:\n{letter.get('body', '')}\n"
        context += "-------------------------\n"
        
    return context

async def generate_smart_cover_letter(job_description: str, user_cv: str, user_id: str = None, use_rag: bool = True) -> dict:
    """
    Leverages Groq's LPU architecture and Llama 3 70B to instantly generate 
    a hyper-personalized cover letter. Enforces JSON mode for strict schema adherence.
    Integrates Qdrant-based RAG if user_id is provided.
    """
    logger.info("Initializing Groq inference for Cover Letter generation...")
    
    rag_context = ""
    if use_rag and user_id:
        past_letters = await search_similar_cover_letters(user_id, job_description, top_k=2)
        rag_context = build_rag_context_prompt(past_letters)
    
    system_prompt = f"""
    You are an expert executive recruiter and copywriter. 
    Your task is to write a highly persuasive, concise cover letter based on the provided CV and Job Description.
    You MUST output valid JSON ONLY, adhering exactly to the following schema:
    {{
        "subject": "Compelling subject line for the email",
        "body": "The full text of the cover letter, using proper paragraph breaks (\\n\\n)"
    }}
    {rag_context}
    """
    
    user_prompt = f"""
    Job Description:
    {job_description}
    
    User CV:
    {user_cv}
    """
 
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        
        response_content = chat_completion.choices[0].message.content
        parsed_response = json.loads(response_content)
        
        logger.info("Groq inference completed successfully in JSON format.")
        
        # Ingest the generated cover letter into vector DB for future use
        if user_id:
            asyncio.create_task(upsert_cover_letter(
                user_id=user_id,
                job_description=job_description,
                cover_letter_subject=parsed_response.get("subject"),
                cover_letter_body=parsed_response.get("body"),
                tone="professional"
            ))
            
        return parsed_response
        
    except Exception as e:
        logger.error(f"Failed to generate cover letter via Groq: {e}")
        raise

async def generate_smart_cover_letter_stream(job_description: str, user_cv: str, tone: str, user_id: str = None, use_rag: bool = True):
    """
    Async generator yielding text chunks wrapped in SSE format (JSON-encoded delta).
    Integrates Qdrant-based RAG if user_id is provided.
    """
    logger.info(f"Initializing Groq streaming inference for Cover letter with tone: {tone}...")
    
    tone_guidelines = TONE_REGISTRY.get(tone.lower(), TONE_REGISTRY["professional"])
    
    rag_context = ""
    if use_rag and user_id:
        past_letters = await search_similar_cover_letters(user_id, job_description, top_k=2)
        rag_context = build_rag_context_prompt(past_letters)
        
    system_prompt = f"""
    You are an expert executive recruiter and copywriter.
    Your task is to write a highly persuasive, concise cover letter based on the provided CV and Job Description.
    You MUST write the cover letter using a tone that is {tone_guidelines}.
    Write the cover letter content directly. Do not output JSON. Do not include introductory/outro comments or conversational filler.
    {rag_context}
    """
    
    user_prompt = f"""
    Job Description:
    {job_description}
    
    User CV:
    {user_cv}
    """
    
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model="llama3-70b-8192",
            temperature=0.6,
            max_tokens=1024,
            stream=True
        )
        
        full_body = []
        async for chunk in chat_completion:
            if len(chunk.choices) > 0:
                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    full_body.append(delta_content)
                    yield f"data: {json.dumps({'chunk': delta_content})}\n\n"
                    
        # Ingest the generated cover letter into vector DB for future use
        if user_id and full_body:
            full_letter_body = "".join(full_body)
            asyncio.create_task(upsert_cover_letter(
                user_id=user_id,
                job_description=job_description,
                cover_letter_subject="Generated Cover Letter (Streamed)",
                cover_letter_body=full_letter_body,
                tone=tone
            ))
                    
    except Exception as e:
        logger.error(f"Failed to stream cover letter via Groq: {e}")
        raise
```

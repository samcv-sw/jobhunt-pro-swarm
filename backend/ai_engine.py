import os
import json
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# Initialize the Groq client
# The API key should be set in the environment variables as GROQ_API_KEY
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY", "fallback-key-for-testing"),
)

# Registry for dynamic tone guidelines
TONE_REGISTRY = {
    "professional": "polished, formal, professional, and well-structured, highlighting experience and qualifications objectively and elegantly.",
    "confident": "high energy, assertive, confident, bold, showing strong self-assurance, demonstrating direct capability and clear value proposition.",
    "creative": "engaging, storytelling, creative, unique, capturing attention with a compelling narrative and expressive language while showing personality."
}

async def generate_smart_cover_letter(job_description: str, user_cv: str) -> dict:
    """
    Leverages Groq's LPU architecture and Llama 3 70B to instantly generate 
    a hyper-personalized cover letter. Enforces JSON mode for strict schema adherence.
    """
    logger.info("Initializing Groq inference for Cover Letter generation...")

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
        # We use llama3-70b-8192 for high-quality generation
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
            model="llama-3.3-70b-versatile",
            temperature=0.5, # Balance between creativity and precision
            max_tokens=1024, # Limit output to reduce TTFT (Time-To-First-Token)
            response_format={"type": "json_object"}
        )
        
        response_content = chat_completion.choices[0].message.content
        parsed_response = json.loads(response_content)
        
        logger.info("Groq inference completed successfully in JSON format.")
        return parsed_response
        
    except Exception as e:
        logger.error(f"Failed to generate cover letter via Groq: {e}")
        raise

async def generate_smart_cover_letter_stream(job_description: str, user_cv: str, tone: str):
    """
    Async generator yielding text chunks wrapped in SSE format (JSON-encoded delta).
    """
    logger.info(f"Initializing Groq streaming inference for Cover letter with tone: {tone}...")
    
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
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            max_tokens=1024,
            stream=True
        )
        
        async for chunk in chat_completion:
            if len(chunk.choices) > 0:
                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    yield f"data: {json.dumps({'chunk': delta_content})}\n\n"
                    
    except Exception as e:
        logger.error(f"Failed to stream cover letter via Groq: {e}")
        raise

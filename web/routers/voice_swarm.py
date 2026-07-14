import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/voice-swarm")
async def voice_swarm_endpoint(websocket: WebSocket):
    """
    USA TECH: Real-Time Voice Swarm (WebRTC Simulation).
    This websocket receives binary audio chunks (simulated here as text),
    runs a background RAG agent to fetch the company's tech stack,
    and returns a synthesized AI voice response in <300ms latency.
    """
    await websocket.accept()
    logger.info("Voice Swarm WebSocket Connected. AI Voice Agent is live.")

    try:
        while True:
            # In production, this receives binary PCM audio data.
            # We mock it as text for the prototype.
            transcribed_text = await websocket.receive_text()

            logger.info(f"[HR Recruiter Audio]: {transcribed_text}")

            # --- THE DYNAMIC RAG INJECTION ---
            # While the Voice Agent listens, the RAG Agent fetches the exact answer.
            rag_prompt = f"RAG INJECTION: The interviewer just asked '{transcribed_text}'. Give a 1-sentence technical answer."

            # We use the semantic cache to return instantly
            ai_brain_response = await ai_tailor._call_ai(rag_prompt, max_tokens=50)

            # Simulated Voice Synthesizer (Text-to-Speech)
            synthetic_audio_packet = f"[[AUDIO_BLOB_SYNTHESIZED]]: {ai_brain_response}"

            await websocket.send_text(synthetic_audio_packet)

    except WebSocketDisconnect:
        logger.info("Voice Swarm Call Ended.")
    except Exception as e:
        logger.error(f"Voice Swarm Error: {e}")

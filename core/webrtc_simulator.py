"""
JobHunt Pro — WebRTC Voice Agent Simulation Orchestrator
Coordinates multi-agent panel sessions, processes audio packet latency metrics,
and records interactive conversations for user reviews.
"""

import time
import asyncio
from typing import Dict, Any, List
from core.voice_webrtc_agent import VoiceAgentSession

class WebRTCSimulator:
    def __init__(self):
        self.active_sessions: Dict[str, VoiceAgentSession] = {}
        self.recordings_log: List[Dict[str, Any]] = []

    def start_session(self, session_id: str, candidate_name: str, job_title: str) -> Dict[str, Any]:
        """
        Starts a WebRTC simulated audio session.
        """
        session = VoiceAgentSession(session_id=session_id, candidate_name=candidate_name, job_title=job_title)
        self.active_sessions[session_id] = session
        return {
            "session_id": session_id,
            "status": "started",
            "candidate": candidate_name,
            "job_title": job_title,
            "timestamp": time.time()
        }

    async def stream_audio_and_respond(self, session_id: str, client_audio_b64: str) -> Dict[str, Any]:
        """
        Streams audio packets and returns a synchronized AI speaker turn response.
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found.")

        session = self.active_sessions[session_id]
        response = await session.process_audio_chunk(client_audio_b64)
        
        # Log recording turn
        self.recordings_log.append({
            "session_id": session_id,
            "speaker": "user",
            "transcript": response["transcript_user"],
            "timestamp": time.time()
        })
        self.recordings_log.append({
            "session_id": session_id,
            "speaker": response["active_interviewer"],
            "transcript": response["ai_response"],
            "timestamp": time.time()
        })

        return response

    def get_recording(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Returns full dialogue recording history for a session.
        """
        return [log for log in self.recordings_log if log["session_id"] == session_id]

webrtc_simulator = WebRTCSimulator()

"""
Quantum Security Router
Exposes Post-Quantum Zero-Trust authentication and Self-Fuzzing Guard APIs.
"""

from fastapi import APIRouter, HTTPException, Request, Body
from typing import Dict, Any, Optional
from core.quantum_zero_trust_armor import quantum_armor

router = APIRouter(prefix="/api/v1/quantum-security", tags=["Quantum Security"])

@router.post("/generate-nonce")
def generate_pq_nonce(payload: Dict[str, Any] = Body(...)):
    """Generates a post-quantum lattice nonce for zero-trust API calls."""
    user_id = str(payload.get("user_id", "guest"))
    client_ip = str(payload.get("client_ip", "127.0.0.1"))
    nonce = quantum_armor.generate_lattice_nonce(user_id, client_ip)
    return {
        "status": "success",
        "post_quantum_nonce": nonce,
        "algorithm": "Dilithium-Kyber-Hybrid-Simulated",
        "ttl_seconds": 300
    }

@router.post("/verify-nonce")
def verify_pq_nonce(payload: Dict[str, Any] = Body(...)):
    """Validates a post-quantum lattice nonce."""
    nonce = str(payload.get("nonce", ""))
    is_valid = quantum_armor.verify_lattice_nonce(nonce)
    return {
        "status": "success" if is_valid else "invalid",
        "is_valid": is_valid
    }

@router.post("/fuzz-audit")
def self_fuzz_audit(payload: Dict[str, Any] = Body(...)):
    """Runs automated self-fuzzing inspection on target payload."""
    is_clean, threats = quantum_armor.self_fuzz_inspect_payload(payload)
    return {
        "status": "clean" if is_clean else "threat_detected",
        "is_clean": is_clean,
        "threats": threats,
        "zero_trust_score": 100 if is_clean else max(0, 100 - len(threats) * 25)
    }

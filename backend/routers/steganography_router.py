"""
FastAPI Router for Steganographic Quantum-Proof Storage Vault
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from core.steganography_vault import stego_vault

router = APIRouter(prefix="/api/v1/steganography-vault", tags=["Steganography Quantum Vault"])

class EncodeRequest(BaseModel):
    secret_data: Dict[str, Any]
    passkey: str

class DecodeRequest(BaseModel):
    payload_id: str
    passkey: str

@router.post("/encode")
def encode_stego(req: EncodeRequest):
    """Encode confidential resume/credentials into a steganographic PNG image pixel container."""
    record = stego_vault.encode_data_into_payload(secret_data=req.secret_data, passkey=req.passkey)
    return {"status": "success", "record": record}

@router.post("/decode")
def decode_stego(req: DecodeRequest):
    """Decode and decrypt confidential payload from a steganographic container."""
    res = stego_vault.decode_data_from_payload(payload_id=req.payload_id, passkey=req.passkey)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

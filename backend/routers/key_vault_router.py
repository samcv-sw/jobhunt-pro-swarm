"""
FastAPI Router for Zero-Trust Hardware-Encrypted Key Vault Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from core.zero_trust_key_vault import ZeroTrustKeyVault, get_key_vault_status

router = APIRouter(prefix="/api/v2/key-vault", tags=["Zero-Trust Key Vault"])

class StoreKeyRequest(BaseModel):
    user_id: str
    provider: str
    api_key: str

class DecryptKeyRequest(BaseModel):
    user_id: str
    cipher_b64: str

@router.get("/status")
def status_endpoint():
    return get_key_vault_status()

@router.post("/store")
def store_key_endpoint(req: StoreKeyRequest):
    vault = ZeroTrustKeyVault()
    return vault.encrypt_api_key(req.user_id, req.provider, req.api_key)

@router.post("/decrypt")
def decrypt_key_endpoint(req: DecryptKeyRequest):
    vault = ZeroTrustKeyVault()
    decrypted = vault.decrypt_api_key(req.user_id, req.cipher_b64)
    return {"user_id": req.user_id, "decrypted_key": decrypted}

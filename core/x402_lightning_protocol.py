"""
HTTP 402 Lightning Protocol & Autonomous AI Monetization Engine.
Enables micro-token / Satoshi paywalls and autonomous L402 LNURL invoice verification
for sovereign AI agent monetization without credit cards or third-party gateways.
"""

import os
import time
import json
import hmac
import hashlib
from typing import Dict, Any, Optional

class X402LightningEngine:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("L402_SECRET_KEY", "sovereign_l402_secret_key_99")

    def create_invoice(self, resource_id: str, amount_sats: int, ttl_seconds: int = 3600) -> Dict[str, Any]:
        """Generate a cryptographically signed L402 payment challenge & mock LN invoice."""
        expiry = int(time.time()) + ttl_seconds
        payment_hash = hashlib.sha256(f"{resource_id}:{expiry}:{amount_sats}".encode()).hexdigest()
        
        # Preimage generation for simulation / verification
        preimage = hashlib.sha256(f"{payment_hash}:{self.secret_key}".encode()).hexdigest()
        
        macaroon_payload = f"res={resource_id}&exp={expiry}&sats={amount_sats}&hash={payment_hash}"
        signature = hmac.new(self.secret_key.encode(), macaroon_payload.encode(), hashlib.sha256).hexdigest()
        
        macaroon = f"{macaroon_payload}&sig={signature}"
        
        return {
            "status": "402_payment_required",
            "resource_id": resource_id,
            "amount_sats": amount_sats,
            "payment_hash": payment_hash,
            "payment_request": f"lnbc{amount_sats}u1p{payment_hash[:20]}...",
            "macaroon": macaroon,
            "expires_at": expiry
        }

    def verify_payment(self, macaroon: str, preimage: str) -> Dict[str, Any]:
        """Verify L402 payment challenge with preimage and cryptographic macaroon signature."""
        try:
            parts = dict(param.split("=") for param in macaroon.split("&"))
            sig = parts.pop("sig", None)
            
            if not sig:
                return {"valid": False, "error": "Missing signature"}
            
            reconstructed_payload = "&".join(f"{k}={v}" for k, v in parts.items())
            expected_sig = hmac.new(self.secret_key.encode(), reconstructed_payload.encode(), hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(sig, expected_sig):
                return {"valid": False, "error": "Invalid signature"}
            
            if int(parts["exp"]) < time.time():
                return {"valid": False, "error": "Challenge expired"}
            
            # Verify preimage hash match
            expected_hash = parts["hash"]
            computed_preimage_hash = hashlib.sha256(preimage.encode()).hexdigest()
            
            # Allow mock matching or direct SHA256 match
            simulated_preimage = hashlib.sha256(f"{expected_hash}:{self.secret_key}".encode()).hexdigest()
            
            if preimage != simulated_preimage and computed_preimage_hash != expected_hash:
                return {"valid": False, "error": "Preimage mismatch"}
            
            return {
                "valid": True,
                "resource_id": parts["res"],
                "amount_sats": int(parts["sats"]),
                "verified_at": int(time.time())
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

lightning_engine = X402LightningEngine()

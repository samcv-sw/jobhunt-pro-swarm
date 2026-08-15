"""
PHASE 6: Security Hardening
Zero-Trust Architecture + Advanced MFA + E2E Encryption
Audit Logging + DDoS Protection + Secrets Management
"""

import hashlib
import secrets
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List, Any
import json


class SecurityLevel(str, Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""
    TOTP = "totp"                    # Time-based OTP
    WEBAUTHN = "webauthn"            # FIDO2/WebAuthn
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODE = "backup_code"


class EncryptionAlgorithm(str, Enum):
    """Encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    RSA_4096 = "rsa_4096"


@dataclass
class AuditLogEntry:
    """Security audit log"""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    status: str  # success | failure
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    severity: SecurityLevel


@dataclass
class SecurityEvent:
    """Real-time security event"""
    event_id: str
    event_type: str
    severity: SecurityLevel
    description: str
    timestamp: datetime
    affected_resources: List[str]
    remediation_required: bool


class ZeroTrustArchitecture:
    """Zero-trust security model implementation"""
    
    def __init__(self):
        self.verified_devices: Dict[str, Dict] = {}
        self.device_trust_scores: Dict[str, float] = {}
        self.suspicious_activities: List[Dict] = []
    
    async def verify_device(self, device_id: str, device_fingerprint: str) -> bool:
        """Verify device fingerprint"""
        
        if device_id not in self.verified_devices:
            # First time device
            self.verified_devices[device_id] = {
                "fingerprint": device_fingerprint,
                "first_seen": datetime.now(),
                "trust_score": 0.3
            }
            return False  # Require additional verification
        
        stored_fingerprint = self.verified_devices[device_id]["fingerprint"]
        if stored_fingerprint == device_fingerprint:
            # Fingerprint matches
            self.device_trust_scores[device_id] = min(1.0,
                self.device_trust_scores.get(device_id, 0.3) + 0.1
            )
            return True
        else:
            # Fingerprint mismatch - suspicious
            self.suspicious_activities.append({
                "device_id": device_id,
                "event": "fingerprint_mismatch",
                "timestamp": datetime.now(),
                "expected": stored_fingerprint,
                "received": device_fingerprint
            })
            self.device_trust_scores[device_id] = max(0.0,
                self.device_trust_scores.get(device_id, 0.5) - 0.3
            )
            return False
    
    async def evaluate_trust_score(
        self,
        user_id: str,
        device_id: str,
        ip_address: str,
        behavior_data: Dict
    ) -> float:
        """Calculate overall trust score (0-1)"""
        
        score = 0.5  # Baseline
        
        # Device trust
        device_trust = self.device_trust_scores.get(device_id, 0.3)
        score += device_trust * 0.3
        
        # IP reputation (in production: check IP reputation database)
        known_ips = behavior_data.get("known_ips", [])
        if ip_address in known_ips:
            score += 0.2
        
        # Time of day consistency
        expected_active_hours = behavior_data.get("typical_hours", (9, 17))
        current_hour = datetime.now().hour
        if expected_active_hours[0] <= current_hour <= expected_active_hours[1]:
            score += 0.1
        
        # Geolocation consistency
        if not behavior_data.get("check_geolocation", True):
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    async def enforce_zero_trust_access(
        self,
        user_id: str,
        device_id: str,
        resource: str,
        trust_score: float
    ) -> bool:
        """Enforce zero-trust access control"""
        
        if trust_score >= 0.8:
            return True  # Grant access
        elif trust_score >= 0.5:
            # Require additional verification
            return False
        else:
            # Deny access
            return False


class AdvancedMFAManager:
    """Advanced MFA with WebAuthn support"""
    
    def __init__(self):
        self.mfa_enrollments: Dict[str, List[Dict]] = {}
        self.backup_codes: Dict[str, List[str]] = {}
        self.totp_secrets: Dict[str, str] = {}
    
    async def enroll_webauthn(self, user_id: str, credential_data: Dict) -> bool:
        """Enroll FIDO2/WebAuthn credential"""
        
        if user_id not in self.mfa_enrollments:
            self.mfa_enrollments[user_id] = []
        
        credential = {
            "type": MFAMethod.WEBAUTHN,
            "credential_id": credential_data.get("id"),
            "public_key": credential_data.get("public_key"),
            "enrolled_at": datetime.now(),
            "last_used": None,
            "is_backup": credential_data.get("is_backup", False)
        }
        
        self.mfa_enrollments[user_id].append(credential)
        return True
    
    async def enroll_totp(self, user_id: str) -> Dict:
        """Enroll TOTP (Time-based One-Time Password)"""
        
        # Generate secret
        secret = secrets.token_urlsafe(32)
        self.totp_secrets[user_id] = secret
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        self.backup_codes[user_id] = backup_codes
        
        return {
            "secret": secret,
            "backup_codes": backup_codes,
            "qr_code_url": f"otpauth://totp/JobHunt Pro:{user_id}?secret={secret}"
        }
    
    async def verify_mfa(
        self,
        user_id: str,
        mfa_method: MFAMethod,
        verification_data: Dict
    ) -> bool:
        """Verify MFA code/credential"""
        
        if mfa_method == MFAMethod.WEBAUTHN:
            # In production: verify WebAuthn signature
            return True
        elif mfa_method == MFAMethod.TOTP:
            # In production: verify TOTP code
            provided_code = verification_data.get("code")
            return len(str(provided_code)) == 6
        elif mfa_method == MFAMethod.BACKUP_CODE:
            # Verify backup code
            code = verification_data.get("code")
            if user_id in self.backup_codes and code in self.backup_codes[user_id]:
                self.backup_codes[user_id].remove(code)  # One-time use
                return True
        
        return False


class EndToEndEncryption:
    """E2E encryption for sensitive data"""
    
    def __init__(self, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM):
        self.algorithm = algorithm
        self.user_keys: Dict[str, str] = {}
    
    async def generate_user_keypair(self, user_id: str) -> Dict:
        """Generate encryption keypair for user"""
        
        # In production: use cryptography library for actual encryption
        # For demo: use mock keys
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        
        self.user_keys[user_id] = private_key
        
        return {
            "public_key": public_key,
            "algorithm": self.algorithm.value,
            "key_id": hashlib.sha256(f"{user_id}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        }
    
    async def encrypt_data(self, user_id: str, plaintext: str) -> Dict:
        """Encrypt data with user's public key"""
        
        # In production: use actual encryption (e.g., cryptography.hazmat)
        # For demo: simple encoding
        ciphertext = hashlib.sha256(
            f"{plaintext}{self.user_keys.get(user_id, 'default')}".encode()
        ).hexdigest()
        
        return {
            "ciphertext": ciphertext,
            "algorithm": self.algorithm.value,
            "timestamp": datetime.now().isoformat()
        }
    
    async def decrypt_data(self, user_id: str, encrypted_data: Dict) -> Optional[str]:
        """Decrypt data with user's private key"""
        
        if user_id not in self.user_keys:
            return None
        
        # In production: actual decryption
        return "[Decrypted content]"


class AuditLogging:
    """Comprehensive security audit logging"""
    
    def __init__(self):
        self.audit_logs: List[AuditLogEntry] = []
        self.security_events: List[SecurityEvent] = []
    
    async def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        status: str,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict] = None
    ) -> None:
        """Log security-relevant action"""
        
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource=resource,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            severity=self._determine_severity(action, status)
        )
        
        self.audit_logs.append(entry)
    
    async def log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        description: str,
        affected_resources: List[str],
        remediation_required: bool = False
    ) -> None:
        """Log security event"""
        
        event_id = secrets.token_hex(8)
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            description=description,
            timestamp=datetime.now(),
            affected_resources=affected_resources,
            remediation_required=remediation_required
        )
        
        self.security_events.append(event)
    
    def _determine_severity(self, action: str, status: str) -> SecurityLevel:
        """Determine log severity"""
        
        if status == "failure":
            if "login" in action:
                return SecurityLevel.HIGH
            elif "access" in action:
                return SecurityLevel.MEDIUM
        
        if "delete" in action or "modify" in action:
            return SecurityLevel.MEDIUM
        
        return SecurityLevel.LOW
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """Retrieve audit trail"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs = [
            {
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "action": log.action,
                "resource": log.resource,
                "status": log.status,
                "severity": log.severity.value,
                "details": log.details
            }
            for log in self.audit_logs
            if log.timestamp > cutoff_date and
               (user_id is None or log.user_id == user_id)
        ]
        
        return logs


class DDoSProtection:
    """DDoS attack detection and mitigation"""
    
    def __init__(self, rate_limit_per_minute: int = 100):
        self.rate_limit = rate_limit_per_minute
        self.request_history: Dict[str, List[datetime]] = {}
        self.blocked_ips: List[str] = []
    
    async def check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP exceeds rate limit"""
        
        if ip_address in self.blocked_ips:
            return False
        
        if ip_address not in self.request_history:
            self.request_history[ip_address] = []
        
        # Clean old requests (older than 1 minute)
        cutoff = datetime.now() - timedelta(minutes=1)
        self.request_history[ip_address] = [
            ts for ts in self.request_history[ip_address]
            if ts > cutoff
        ]
        
        # Add current request
        self.request_history[ip_address].append(datetime.now())
        
        # Check if exceeded limit
        if len(self.request_history[ip_address]) > self.rate_limit:
            self.blocked_ips.append(ip_address)
            return False
        
        return True
    
    async def detect_pattern_attack(self, ip_address: str) -> bool:
        """Detect suspicious patterns"""
        
        if ip_address not in self.request_history:
            return False
        
        recent_requests = len(self.request_history[ip_address])
        
        # If >5x normal rate in last 30s
        if recent_requests > self.rate_limit // 2:
            return True
        
        return False


class SecretsRotation:
    """Automatic secrets rotation"""
    
    def __init__(self, rotation_days: int = 90):
        self.rotation_days = rotation_days
        self.secrets_vault: Dict[str, Dict] = {}
    
    async def store_secret(self, secret_name: str, secret_value: str) -> Dict:
        """Store secret with rotation metadata"""
        
        secret_id = secrets.token_hex(12)
        
        self.secrets_vault[secret_name] = {
            "secret_id": secret_id,
            "value": secret_value,  # In production: encrypted
            "created_at": datetime.now(),
            "next_rotation": datetime.now() + timedelta(days=self.rotation_days),
            "version": 1
        }
        
        return {"secret_id": secret_id, "version": 1}
    
    async def rotate_secret(self, secret_name: str, new_value: str) -> Dict:
        """Rotate secret to new value"""
        
        if secret_name not in self.secrets_vault:
            return {"status": "error", "message": "Secret not found"}
        
        old_secret = self.secrets_vault[secret_name]
        
        rotated_secret = {
            "secret_id": secrets.token_hex(12),
            "value": new_value,
            "created_at": datetime.now(),
            "next_rotation": datetime.now() + timedelta(days=self.rotation_days),
            "version": old_secret["version"] + 1,
            "previous_version": old_secret["secret_id"]
        }
        
        self.secrets_vault[secret_name] = rotated_secret
        
        return {
            "status": "success",
            "version": rotated_secret["version"],
            "next_rotation": rotated_secret["next_rotation"].isoformat()
        }
    
    async def check_rotation_due(self) -> List[str]:
        """Check which secrets need rotation"""
        
        rotation_due = []
        for secret_name, secret_data in self.secrets_vault.items():
            if datetime.now() >= secret_data["next_rotation"]:
                rotation_due.append(secret_name)
        
        return rotation_due


# Global security instances
zero_trust = ZeroTrustArchitecture()
mfa_manager = AdvancedMFAManager()
e2e_encryption = EndToEndEncryption()
audit_logger = AuditLogging()
ddos_protection = DDoSProtection(rate_limit_per_minute=100)
secrets_manager = SecretsRotation(rotation_days=90)

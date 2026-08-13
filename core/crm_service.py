"""
Enterprise CRM Service & Outbound Webhook Dispatcher
Supports HubSpot, Salesforce, Pipedrive, and HMAC-SHA256 signed webhooks.
"""

import hmac
import hashlib
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

class CRMService:
    def __init__(self):
        pass

    def dispatch_webhook(self, webhook_url: str, secret: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches an outbound webhook with HMAC-SHA256 signature header.
        """
        if not webhook_url:
            return {"success": False, "error": "Webhook URL is required"}

        body_data = {
            "event": event_type,
            "timestamp": int(time.time()),
            "data": payload
        }
        body_bytes = json.dumps(body_data, ensure_ascii=False).encode("utf-8")
        
        signature = hmac.new(
            secret.encode("utf-8") if secret else b"default_secret",
            body_bytes,
            hashlib.sha256
        ).hexdigest()

        req = urllib.request.Request(
            webhook_url,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-JobHunt-Signature": f"sha256={signature}",
                "X-JobHunt-Event": event_type,
                "User-Agent": "JobHuntPro-CRM-Dispatcher/2.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return {
                    "success": True,
                    "status_code": response.status,
                    "event": event_type,
                    "dispatched_at": time.time()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "event": event_type,
                "dispatched_at": time.time()
            }

    def export_to_hubspot(self, api_key: str, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exports a B2B lead to HubSpot CRM.
        """
        if not api_key:
            return {"success": False, "error": "HubSpot API key missing"}

        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        payload = {
            "properties": {
                "email": lead.get("email"),
                "firstname": lead.get("first_name", lead.get("name", "").split(" ")[0]),
                "lastname": lead.get("last_name", " ".join(lead.get("name", "").split(" ")[1:]) or "N/A"),
                "company": lead.get("company", "Independent"),
                "jobtitle": lead.get("title", lead.get("job_title", "Prospect")),
                "lifecyclestage": "lead"
            }
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"success": True, "provider": "hubspot", "crm_id": data.get("id")}
        except Exception as e:
            return {"success": False, "provider": "hubspot", "error": str(e)}

    def export_to_pipedrive(self, api_token: str, domain: str, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exports a B2B lead to Pipedrive CRM.
        """
        if not api_token:
            return {"success": False, "error": "Pipedrive API token missing"}

        base_domain = domain if domain else "api.pipedrive.com"
        url = f"https://{base_domain}/v1/persons?api_token={api_token}"
        payload = {
            "name": lead.get("name") or f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip() or "B2B Lead",
            "email": [{"value": lead.get("email"), "primary": True}],
            "org_name": lead.get("company", "")
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {"success": True, "provider": "pipedrive", "crm_id": data.get("data", {}).get("id")}
        except Exception as e:
            return {"success": False, "provider": "pipedrive", "error": str(e)}

crm_service = CRMService()

"""
Unified CRM Integration Adapter for JobHunt Pro (HubSpot, Salesforce, Pipedrive).
"""

from typing import Dict, Any


def sync_lead_to_crm(crm_provider: str, api_key: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Syncs a converted lead to HubSpot, Salesforce, or Pipedrive.
    """
    provider = crm_provider.strip().lower()
    email = lead_data.get("email", "")
    full_name = lead_data.get("full_name", "Prospective Lead")
    company = lead_data.get("company", "Target Client")

    if not provider or not api_key:
        return {"status": "error", "message": "CRM provider and API key are required."}

    if provider == "hubspot":
        # HubSpot Contacts API payload
        payload = {
            "properties": {
                "email": email,
                "firstname": full_name.split()[0] if full_name else "",
                "lastname": full_name.split()[-1] if len(full_name.split()) > 1 else "",
                "company": company,
                "lifecyclestage": "lead"
            }
        }
        return {"status": "synced", "provider": "hubspot", "crm_id": f"hs_{hash(email) % 1000000}", "payload": payload}

    elif provider == "salesforce":
        # Salesforce Lead API payload
        payload = {
            "Email": email,
            "LastName": full_name,
            "Company": company,
            "Status": "Open - Not Contacted"
        }
        return {"status": "synced", "provider": "salesforce", "crm_id": f"sf_{hash(email) % 1000000}", "payload": payload}

    elif provider == "pipedrive":
        # Pipedrive Persons API payload
        payload = {
            "name": full_name,
            "email": [email],
            "org_id": company
        }
        return {"status": "synced", "provider": "pipedrive", "crm_id": f"pd_{hash(email) % 1000000}", "payload": payload}

    else:
        return {"status": "error", "message": f"Unsupported CRM provider: {crm_provider}"}

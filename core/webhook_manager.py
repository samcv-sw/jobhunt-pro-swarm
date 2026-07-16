# ──────────────────────────────────────────────────────────────────────────────
# webhook_manager.py - Secure Webhook Handling & Verification
# Manages webhook subscriptions, signature verification, and retries
# ──────────────────────────────────────────────────────────────────────────────

import hashlib
import hmac
import json
import logging
import asyncio
from typing import Callable, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook event types."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    JOB_APPLIED = "job.applied"
    JOB_POSTED = "job.posted"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"


@dataclass
class Webhook:
    """Webhook subscription."""
    id: str
    url: str
    events: List[WebhookEventType]
    secret: str
    active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 5


@dataclass
class WebhookEvent:
    """Webhook event."""
    id: str
    event_type: WebhookEventType
    data: Dict
    timestamp: datetime
    delivery_status: str = "pending"  # pending, delivered, failed
    attempts: int = 0
    next_retry_at: Optional[datetime] = None


class WebhookManager:
    """Manages webhook subscriptions and deliveries."""
    
    def __init__(self):
        self._webhooks: Dict[str, Webhook] = {}
        self._events: Dict[str, WebhookEvent] = {}
        self._retry_config = {
            "max_retries": 5,
            "initial_delay": 60,  # seconds
            "max_delay": 3600,  # seconds
            "backoff_multiplier": 2,
        }
    
    def register_webhook(
        self,
        webhook_id: str,
        url: str,
        events: List[WebhookEventType],
        secret: str,
    ) -> Webhook:
        """Register a new webhook."""
        webhook = Webhook(
            id=webhook_id,
            url=url,
            events=events,
            secret=secret,
            active=True,
            created_at=datetime.utcnow(),
        )
        self._webhooks[webhook_id] = webhook
        logger.info(f"Webhook registered: {webhook_id} -> {url}")
        return webhook
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info(f"Webhook unregistered: {webhook_id}")
            return True
        return False
    
    def disable_webhook(self, webhook_id: str) -> bool:
        """Disable a webhook temporarily."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].active = False
            logger.info(f"Webhook disabled: {webhook_id}")
            return True
        return False
    
    def enable_webhook(self, webhook_id: str) -> bool:
        """Enable a webhook."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].active = True
            logger.info(f"Webhook enabled: {webhook_id}")
            return True
        return False
    
    def get_webhooks_for_event(self, event_type: WebhookEventType) -> List[Webhook]:
        """Get all active webhooks subscribed to an event."""
        return [
            w for w in self._webhooks.values()
            if w.active and event_type in w.events and w.failure_count < w.max_failures
        ]
    
    async def trigger_event(
        self,
        event_id: str,
        event_type: WebhookEventType,
        data: Dict,
    ) -> None:
        """Trigger a webhook event."""
        logger.info(f"Triggering webhook event: {event_type}")
        
        event = WebhookEvent(
            id=event_id,
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
        )
        self._events[event_id] = event
        
        # Get webhooks for this event
        webhooks = self.get_webhooks_for_event(event_type)
        
        # Deliver to all webhooks asynchronously
        tasks = [self._deliver_webhook(webhook, event) for webhook in webhooks]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _deliver_webhook(self, webhook: Webhook, event: WebhookEvent) -> None:
        """Deliver webhook to endpoint."""
        try:
            import httpx
            
            # Generate signature
            signature = self._generate_signature(webhook.secret, event)
            
            # Prepare payload
            payload = {
                "id": event.id,
                "type": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
            }
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-ID": webhook.id,
                "X-Webhook-Attempt": str(event.attempts + 1),
            }
            
            # Send webhook
            logger.info(f"Delivering webhook {webhook.id} for event {event.event_type}")
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                )
            
            if response.status_code in [200, 201, 202]:
                event.delivery_status = "delivered"
                webhook.last_triggered_at = datetime.utcnow()
                webhook.failure_count = 0
                logger.info(f"Webhook {webhook.id} delivered successfully")
            else:
                await self._retry_webhook(webhook, event)
        
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            await self._retry_webhook(webhook, event)
    
    async def _retry_webhook(self, webhook: Webhook, event: WebhookEvent) -> None:
        """Schedule webhook retry."""
        event.attempts += 1
        max_retries = self._retry_config["max_retries"]
        
        if event.attempts >= max_retries:
            event.delivery_status = "failed"
            webhook.failure_count += 1
            
            if webhook.failure_count >= webhook.max_failures:
                webhook.active = False
                logger.warning(f"Webhook {webhook.id} disabled due to repeated failures")
            return
        
        # Calculate next retry time
        delay = min(
            self._retry_config["initial_delay"] *
            (self._retry_config["backoff_multiplier"] ** (event.attempts - 1)),
            self._retry_config["max_delay"],
        )
        
        event.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        logger.info(f"Webhook {webhook.id} scheduled for retry in {delay}s")
    
    @staticmethod
    def _generate_signature(secret: str, event: WebhookEvent) -> str:
        """Generate webhook signature for verification."""
        payload = json.dumps({
            "id": event.id,
            "type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
        }, sort_keys=True)
        
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    @staticmethod
    def verify_signature(
        secret: str,
        event: WebhookEvent,
        provided_signature: str,
    ) -> bool:
        """Verify webhook signature."""
        expected_signature = WebhookManager._generate_signature(secret, event)
        return hmac.compare_digest(expected_signature, provided_signature)
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        return self._webhooks.get(webhook_id)
    
    def get_all_webhooks(self) -> List[Webhook]:
        """Get all webhooks."""
        return list(self._webhooks.values())
    
    def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Get event by ID."""
        return self._events.get(event_id)
    
    def get_event_history(
        self,
        event_type: Optional[WebhookEventType] = None,
        limit: int = 100,
    ) -> List[WebhookEvent]:
        """Get event history."""
        events = list(self._events.values())
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_stats(self) -> dict:
        """Get webhook statistics."""
        webhooks = list(self._webhooks.values())
        events = list(self._events.values())
        
        return {
            "total_webhooks": len(webhooks),
            "active_webhooks": sum(1 for w in webhooks if w.active),
            "total_events": len(events),
            "delivered": sum(1 for e in events if e.delivery_status == "delivered"),
            "failed": sum(1 for e in events if e.delivery_status == "failed"),
            "pending": sum(1 for e in events if e.delivery_status == "pending"),
        }


# Global webhook manager instance
webhook_manager = WebhookManager()


# Usage in FastAPI:
#
# @app.post("/api/webhooks")
# async def register_webhook(webhook_req: WebhookRequest):
#     webhook = webhook_manager.register_webhook(
#         webhook_id=str(uuid.uuid4()),
#         url=webhook_req.url,
#         events=webhook_req.events,
#         secret=webhook_req.secret,
#     )
#     return success_response(data=webhook.to_dict())
#
# @app.post("/api/events/trigger")
# async def trigger_event(event_req: EventRequest):
#     await webhook_manager.trigger_event(
#         event_id=str(uuid.uuid4()),
#         event_type=WebhookEventType[event_req.type],
#         data=event_req.data,
#     )
#     return success_response(message="Event triggered")
#
# @app.get("/api/webhooks/{webhook_id}/events")
# async def get_webhook_events(webhook_id: str):
#     webhook = webhook_manager.get_webhook(webhook_id)
#     events = webhook_manager.get_event_history()
#     return success_response(data=[e.to_dict() for e in events])

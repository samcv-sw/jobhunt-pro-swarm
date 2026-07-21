"""
Decentralized P2P Mesh Relay Engine
Enables zero-cost proxy distribution and peer-to-peer web crawling via WebRTC / WebSocket signaling.
"""

import time
import uuid
import hashlib
from typing import Dict, List, Optional, Any

class P2PMeshRelay:
    def __init__(self):
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.active_channels: Dict[str, Dict[str, Any]] = {}
        self.total_relayed_requests: int = 0

    def register_peer(self, peer_id: Optional[str] = None, ip_region: str = "global", capacity: int = 10) -> Dict[str, Any]:
        """Registers a new peer node into the P2P mesh network."""
        pid = peer_id or f"node_{uuid.uuid4().hex[:8]}"
        peer_info = {
            "peer_id": pid,
            "ip_region": ip_region,
            "capacity": capacity,
            "active_tasks": 0,
            "last_heartbeat": time.time(),
            "status": "online"
        }
        self.peers[pid] = peer_info
        return peer_info

    def heartbeat(self, peer_id: str) -> Any:
        """Updates node heartbeat timestamp."""
        if peer_id in self.peers:
            self.peers[peer_id]["last_heartbeat"] = time.time()
            self.peers[peer_id]["status"] = "online"
            has_task = self.peers[peer_id].get("assigned_task") is not None
            return {"status": "ok", "has_task": has_task}
        return {"status": "error", "has_task": False}

    def register_node(self, node_id: str, client_hash: str = "", user_agent: str = "") -> Dict[str, Any]:
        """Registers a node into the mesh."""
        info = self.register_peer(peer_id=node_id)
        info["status"] = "node_registered"
        info["client_hash"] = client_hash
        info["user_agent"] = user_agent
        info["assigned_task"] = None
        return info

    def dispatch_mesh_task(self, target_url: str, selector: str = "") -> str:
        """Dispatches a task to the mesh."""
        task_id = f"mesh_task_{uuid.uuid4().hex[:8]}"
        for pid in self.peers:
            if not self.peers[pid].get("assigned_task"):
                self.peers[pid]["assigned_task"] = task_id
                break
        return task_id

    def submit_task_result(self, node_id: str, task_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Submits task result."""
        if node_id in self.peers:
            self.peers[node_id]["assigned_task"] = None
            self.total_relayed_requests += 1
        return {"status": "result_accepted", "task_id": task_id}

    def select_optimal_peer(self, target_region: str = "global") -> Optional[str]:
        """Selects the optimal online peer node matching the target region, or falls back to any online peer."""
        regional_peers = [
            pid for pid, info in self.peers.items()
            if info["status"] == "online" and info.get("ip_region") == target_region
        ]
        if regional_peers:
            return regional_peers[0]
        
        # Fallback to any online peer
        online_peers = [pid for pid, info in self.peers.items() if info["status"] == "online"]
        return online_peers[0] if online_peers else None

    def create_signal_channel(self, source_peer: str, target_peer: str) -> Dict[str, Any]:
        """Initiates a WebRTC signaling channel between source and target peers."""
        channel_id = f"chan_{uuid.uuid4().hex[:8]}"
        channel_info = {
            "channel_id": channel_id,
            "source_peer": source_peer,
            "target_peer": target_peer,
            "status": "signaling",
            "created_at": time.time()
        }
        self.active_channels[channel_id] = channel_info
        return channel_info

    def complete_signal(self, channel_id: str, sdp_answer: str = "") -> bool:
        """Completes a WebRTC signaling handshake."""
        if channel_id in self.active_channels:
            self.active_channels[channel_id]["status"] = "established"
            self.active_channels[channel_id]["sdp_answer"] = sdp_answer
            self.total_relayed_requests += 1
            return True
        return False

    def get_mesh_stats(self) -> Dict[str, Any]:
        """Returns overall P2P mesh network telemetry."""
        online_count = sum(1 for p in self.peers.values() if p["status"] == "online")
        return {
            "total_peers": len(self.peers),
            "total_registered_nodes": len(self.peers),
            "online_peers": online_count,
            "active_channels": len(self.active_channels),
            "total_relayed_requests": self.total_relayed_requests,
            "status": "healthy"
        }

    def get_mesh_status(self) -> Dict[str, Any]:
        """Returns mesh status."""
        stats = self.get_mesh_stats()
        stats["completed_tasks"] = self.total_relayed_requests
        return stats

p2p_mesh = P2PMeshRelay()
p2p_mesh_relay = p2p_mesh


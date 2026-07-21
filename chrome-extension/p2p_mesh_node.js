/**
 * Decentralized P2P Scraping Mesh Extension Node - JobHunt Pro v4.0
 * Connects browser extension to zero-cost P2P mesh relay for distributed job fetching.
 */

const P2P_MESH_CONFIG = {
  relayEndpoint: "https://jobhunt-pro-api.local/api/v4/mesh",
  heartbeatIntervalMs: 30000,
  nodeId: "ext_node_" + Math.random().toString(36).substring(2, 11)
};

async function initP2PMeshNode() {
  console.log(`[P2P Mesh Node] Initializing node ID: ${P2P_MESH_CONFIG.nodeId}`);
  
  // Register node
  try {
    const res = await fetch(`${P2P_MESH_CONFIG.relayEndpoint}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        node_id: P2P_MESH_CONFIG.nodeId,
        user_agent: navigator.userAgent
      })
    });
    const data = await res.json();
    console.log("[P2P Mesh Node] Registration response:", data);
  } catch (err) {
    console.warn("[P2P Mesh Node] Mesh relay offline or unreachable, operating standalone.", err);
  }

  // Start periodic heartbeat
  setInterval(runMeshHeartbeat, P2P_MESH_CONFIG.heartbeatIntervalMs);
}

async function runMeshHeartbeat() {
  try {
    const res = await fetch(`${P2P_MESH_CONFIG.relayEndpoint}/heartbeat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ node_id: P2P_MESH_CONFIG.nodeId })
    });
    const data = await res.json();
    
    if (data.has_task && data.task) {
      executeMeshTask(data.task);
    }
  } catch (err) {
    // Silent fail for background worker
  }
}

async function executeMeshTask(task) {
  console.log("[P2P Mesh Node] Executing micro-task:", task);
  try {
    // Perform fetch via extension background context
    const response = await fetch(task.url);
    const htmlText = await response.text();
    
    // Submit result to mesh relay
    await fetch(`${P2P_MESH_CONFIG.relayEndpoint}/result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        node_id: P2P_MESH_CONFIG.nodeId,
        task_id: task.task_id,
        payload: { length: htmlText.length, status: response.status }
      })
    });
  } catch (err) {
    console.error("[P2P Mesh Node] Task execution failed:", err);
  }
}

// Auto-boot node on extension load
if (typeof window !== "undefined") {
  initP2PMeshNode();
}

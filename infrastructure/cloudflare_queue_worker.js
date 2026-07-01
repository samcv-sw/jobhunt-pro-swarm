/**
 * Cloudflare Worker with Queues for The Hydra 2026.
 * This worker acts as a massive shock-absorber (buffer) for millions of concurrent users.
 * Incoming requests are immediately acknowledged (202 Accepted) and placed in a Queue.
 * A separate queue consumer then drip-feeds the tasks to the Oracle Cloud / HF backend,
 * ensuring 100% server utilization without crashing the backend.
 */

export default {
  // 1. HTTP INTAKE (Producer)
  // This function receives the user's web request and pushes it to the Queue.
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    try {
      const payload = await request.json();
      
      // Send the payload to the Cloudflare Queue named "HYDRA_TASK_QUEUE"
      await env.HYDRA_TASK_QUEUE.send(payload);

      // Return immediately to free up the Edge worker and provide a fast UX
      return new Response(JSON.stringify({ 
        status: "accepted", 
        message: "Task queued successfully. The swarm will process it shortly.",
        task_id: crypto.randomUUID()
      }), { 
        status: 202,
        headers: { "Content-Type": "application/json" }
      });

    } catch (err) {
      return new Response("Invalid Payload", { status: 400 });
    }
  },

  // 2. QUEUE CONSUMER (Drip-feeder)
  // This function automatically pulls messages from the Queue at a controlled rate
  // and forwards them to the actual backend (Oracle Cloud / HF Spaces).
  async queue(batch, env, ctx) {
    const BACKEND_URL = env.BACKEND_API_URL || "https://your-oracle-server.com/api/v1/swarm/task";

    // We process the batch of messages
    for (const msg of batch.messages) {
      try {
        const response = await fetch(BACKEND_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${env.BACKEND_SECRET}`
          },
          body: JSON.stringify(msg.body)
        });

        if (response.ok) {
          // If the backend accepts it, acknowledge the message so it's removed from the queue
          msg.ack();
        } else {
          // If the backend is overwhelmed (e.g. 429 or 503), retry later
          msg.retry();
        }
      } catch (error) {
        console.error("Failed to reach backend:", error);
        // Retry later using Exponential Backoff automatically handled by Cloudflare Queues
        msg.retry();
      }
    }
  }
};

/**
 * Cloudflare Worker: Payment Webhook Queue (Profit Shield)
 * 
 * Purpose: Receives payment notifications from Stripe/NowPayments, stores them securely 
 * in a queue, and attempts to deliver them to the PythonAnywhere server. If the PA server 
 * is down or busy, this Worker will retry later, ensuring no payments are ever lost.
 */

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    try {
      const body = await request.text();
      const signature = request.headers.get("x-signature") || "unknown";
      
      // 1. Store the webhook payload securely
      await env.PAYMENT_QUEUE.send({
        payload: body,
        signature: signature,
        timestamp: Date.now()
      });

      // 2. Return 200 OK immediately to the Payment Gateway (so they don't retry and block)
      return new Response(JSON.stringify({ status: "queued" }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
      
    } catch (err) {
      return new Response("Internal Error", { status: 500 });
    }
  },
  
  // This function processes the queue in the background
  async queue(batch, env) {
    for (let msg of batch.messages) {
      try {
        const response = await fetch("https://jhfguf.pythonanywhere.com/api/v1/webhooks/payment", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CF-Signature": msg.body.signature
          },
          body: msg.body.payload
        });

        if (response.ok) {
          msg.ack(); // Payment successfully delivered to PA
        } else {
          msg.retry(); // PA Server is busy, retry later
        }
      } catch (err) {
        msg.retry(); // Network error, retry later
      }
    }
  }
};

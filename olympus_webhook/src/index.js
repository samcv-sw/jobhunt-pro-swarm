// Olympus Webhook — NOWPayments IPN + checkout handler
// Deployed: olympus-webhook.accidental-princess.workers.dev

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, x-nowpayments-sig, x-b2b-key",
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });
}

async function readBody(request) {
  try {
    return await request.json();
  } catch(e) {
    return {};
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

    try {
      // ── CHECKOUT ──
      if (url.pathname === "/api/v1/checkout" && request.method === "POST") {
        const body = await readBody(request);
        const userId = body.userId || "anon";
        const amount = body.amount || 29;

        const npPayload = {
          price_amount: amount,
          price_currency: "usd",
          order_id: userId + "_" + Date.now(),
          order_description: "JobHunt Pro AI - Lifetime Access",
          ipn_callback_url: url.origin + "/api/v1/webhook/nowpayments",
          success_url: "https://jhfguf.pythonanywhere.com/payment/success",
          cancel_url: "https://jhfguf.pythonanywhere.com/payment/cancel",
          is_fixed_rate: true,
          is_fee_paid_by_user: true,
        };

        const npRes = await fetch("https://api.nowpayments.io/v1/invoice", {
          method: "POST",
          headers: { "x-api-key": env.NOWPAYMENTS_API_KEY, "Content-Type": "application/json" },
          body: JSON.stringify(npPayload),
        });
        const npData = await npRes.json();

        if (npData.invoice_url) {
          return json({ invoice_url: npData.invoice_url, payment_id: npData.payment_id || "" });
        }

        // Fallback: direct crypto addresses
        return json({
          method: "direct_crypto",
          wallets: { btc: "bc1q0e68d76d8dc303249a1992405ac2879f97fa8f", eth: "0x0e68d76d8dc303249a1992405ac2879f97fa8fec", usdt: "0xc303249a1992405ac2879f97fa8fec34c72be2f8", ltc: "ltc1q0e68d76d8dc303249a1992405ac2879f97fa8f" },
        });
      }

      // ── NOWPAYMENTS IPN ──
      if (url.pathname === "/api/v1/webhook/nowpayments") {
        const signature = request.headers.get("x-nowpayments-sig");
        if (!signature) return json({ error: "Missing Signature" }, 400);

        const bodyText = await request.text();
        const bodyDict = JSON.parse(bodyText);

        // HMAC-SHA512 verify
        const sortedKeys = Object.keys(bodyDict).sort();
        const sortedObj = {};
        for (const k of sortedKeys) sortedObj[k] = bodyDict[k];
        const message = JSON.stringify(sortedObj);

        const encoder = new TextEncoder();
        const cryptoKey = await crypto.subtle.importKey("raw", encoder.encode(env.IPN_SECRET), { name: "HMAC", hash: "SHA-512" }, false, ["verify"]);
        const sigBytes = await crypto.subtle.sign("HMAC", cryptoKey, encoder.encode(message));
        const hashHex = Array.from(new Uint8Array(sigBytes)).map(b => b.toString(16).padStart(2, "0")).join("");

        if (hashHex !== signature) return json({ error: "Invalid Signature" }, 403);

        console.log("IPN received:", bodyDict.payment_status, bodyDict.order_id);

        if (bodyDict.payment_status === "finished") {
          // Notify PA
          ctx.waitUntil(fetch("https://jhfguf.pythonanywhere.com/api/v2/payment_ipn", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyDict),
          }).catch(e => console.error("PA notify failed:", e.message)));
        }

        return json({ status: "ok" });
      }

      // ── HEALTH ──
      if (url.pathname === "/health") {
        return json({ status: "ok", worker: "olympus-webhook", version: "1.0" });
      }

      // ── PROXY TO PA (fallback) ──
      const targetUrl = "https://jhfguf.pythonanywhere.com" + url.pathname + url.search;
      const headers = new Headers(request.headers);
      headers.set("User-Agent", "OlympusWebhook/1.0");

      const paResp = await fetch(targetUrl, {
        method: request.method,
        headers,
        body: request.method !== "GET" && request.method !== "HEAD" ? await request.text() : undefined,
      });
      const paBody = await paResp.text();
      return new Response(paBody, { status: paResp.status, headers: { ...corsHeaders, ...Object.fromEntries(paResp.headers) } });

    } catch (e) {
      return json({ error: e.message }, 500);
    }
  },
};

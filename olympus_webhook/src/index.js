// Built-in Web Crypto API is used for HMAC verification

export default {
  async fetch(request, env, ctx) {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }
    
    try {
      const signature = request.headers.get('x-nowpayments-sig');
      if (!signature) {
        return new Response('Missing Signature', { status: 400 });
      }

      const bodyText = await request.text();
      const bodyDict = JSON.parse(bodyText);
      
      // Verification logic: Sort keys, stringify, generate HMAC-SHA512
      const sortedKeys = Object.keys(bodyDict).sort();
      const sortedObj = {};
      for (const key of sortedKeys) {
        sortedObj[key] = bodyDict[key];
      }
      const message = JSON.stringify(sortedObj);
      
      const encoder = new TextEncoder();
      const keyData = encoder.encode(env.IPN_SECRET);
      
      const cryptoKey = await crypto.subtle.importKey(
        'raw', keyData, { name: 'HMAC', hash: 'SHA-512' }, false, ['sign', 'verify']
      );
      
      const signatureBytes = await crypto.subtle.sign(
        'HMAC', cryptoKey, encoder.encode(message)
      );
      
      const hashArray = Array.from(new Uint8Array(signatureBytes));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      
      if (hashHex !== signature) {
        console.error("Invalid Signature!");
        return new Response('Invalid Signature', { status: 403 });
      }

      const paymentStatus = bodyDict.payment_status;
      const orderId = bodyDict.order_id;
      
      console.log(`Valid IPN received! Order: ${orderId} | Status: ${paymentStatus}`);
      
      if (paymentStatus === 'finished') {
        console.log(`Payment FINISHED for ${orderId}. Triggering automated delivery...`);
        // Here we could trigger another webhook to GitHub Actions or a database update
      }
      
      return new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: {'Content-Type': 'application/json'} });
    } catch (e) {
      return new Response('Error Processing Webhook: ' + e.message, { status: 500 });
    }
  }
};

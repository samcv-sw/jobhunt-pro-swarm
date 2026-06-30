/**
 * PROJECT OMNI - The AI Parasite Router
 * 
 * Instead of paying for Groq/OpenAI, this edge router distributes AI tasks
 * (like CV parsing and cover letter generation) across 50 identical free 
 * Hugging Face spaces running LLaMA-3.
 * 
 * Deploy this on Cloudflare Workers (100,000 free requests/day).
 */

const HF_SPACES = [
    "https://user-jobhunt-ai-1.hf.space",
    "https://user-jobhunt-ai-2.hf.space",
    "https://user-jobhunt-ai-3.hf.space",
    // ... scales up to 50
    "https://user-jobhunt-ai-50.hf.space"
];

export default {
    async fetch(request, env, ctx) {
        // Only accept POST requests
        if (request.method !== "POST") {
            return new Response("Method not allowed", { status: 405 });
        }

        try {
            // Get the user's AI prompt
            const payload = await request.json();
            
            // Randomly select a free Hugging Face GPU space
            const randomSpace = HF_SPACES[Math.floor(Math.random() * HF_SPACES.length)];
            
            console.log(`Routing AI request to: ${randomSpace}`);
            
            // Proxy the request to the selected free GPU
            const aiResponse = await fetch(`${randomSpace}/api/generate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!aiResponse.ok) {
                // If one space fails (e.g., sleeping), we could implement a retry to another space here
                throw new Error(`HF Space returned ${aiResponse.status}`);
            }

            const data = await aiResponse.json();
            
            // Return the generated cover letter to the P2P network
            return new Response(JSON.stringify(data), {
                headers: { 
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*" 
                }
            });
            
        } catch (error) {
            return new Response(JSON.stringify({ error: error.message }), { 
                status: 500,
                headers: { "Content-Type": "application/json" }
            });
        }
    }
};

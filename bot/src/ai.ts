import Groq from 'groq-sdk';

export async function callGroqWithFallback(prompt: string): Promise<string> {
    const keysJson = process.env.GROQ_KEYS_JSON;
    if (!keysJson) {
        console.error("ERROR: GROQ_KEYS_JSON not set.");
        return "No API Key";
    }

    let keys: string[] = [];
    try {
        keys = JSON.parse(keysJson);
        // Shuffle keys to prevent hitting the same key first every time
        keys = keys.sort(() => Math.random() - 0.5);
    } catch (e) {
        console.error("Error parsing GROQ_KEYS_JSON:", e);
        return "Key Parse Error";
    }

    while (keys.length > 0) {
        const apiKey = keys.shift()!;
        console.log(`Attempting Groq Request with Key: ${apiKey.substring(0, 8)}... (${keys.length} keys remaining)`);
        
        try {
            const groq = new Groq({ apiKey });
            const response = await groq.chat.completions.create({
                messages: [{ role: 'user', content: prompt }],
                model: 'llama-3.3-70b-versatile',
            });
            console.log("Groq Request Successful!");
            return response.choices[0]?.message?.content || "";
        } catch (error: any) {
            console.warn(`Groq API Error on this key: ${error.message}. Switching to next key...`);
            // Add a small delay before trying the next key
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    console.error("FATAL: All Groq keys failed (Rate Limit or Banned).");
    return "Error";
}

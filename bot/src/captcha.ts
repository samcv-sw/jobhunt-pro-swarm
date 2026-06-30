import { GoogleGenAI } from '@google/genai';
import fs from 'fs';

export async function solveCaptcha(screenshotPath: string): Promise<{ x: number, y: number } | null> {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
        console.warn("WARNING: GEMINI_API_KEY not set. CAPTCHA solver disabled.");
        return null;
    }

    try {
        const ai = new GoogleGenAI({ apiKey });
        const imagePart = {
            inlineData: {
                data: Buffer.from(fs.readFileSync(screenshotPath)).toString("base64"),
                mimeType: "image/png"
            }
        };

        console.log("Sending CAPTCHA screenshot to Gemini 2.0 Flash for solving...");
        const response = await ai.models.generateContent({
            model: "gemini-2.0-flash",
            contents: [
                {
                    role: 'user',
                    parts: [
                        { text: "Analyze this CAPTCHA image. If there is a puzzle (like finding traffic lights or a specific object), determine the center coordinate of the target object. Reply ONLY with a JSON object containing 'x' and 'y' integer coordinates. Example: {\"x\": 150, \"y\": 200}" },
                        imagePart
                    ]
                }
            ]
        });

        const textResponse = response.text || "";
        console.log("Gemini CAPTCHA Solver Response:", textResponse);
        
        // Extract JSON from response
        const jsonMatch = textResponse.match(/\{[\s\S]*?\}/);
        if (jsonMatch) {
            const coords = JSON.parse(jsonMatch[0]);
            return coords;
        }

    } catch (e: any) {
        console.error("Gemini CAPTCHA Solver Error:", e.message);
    }
    return null;
}

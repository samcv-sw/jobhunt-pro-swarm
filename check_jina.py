"""Check if JinaAI Indeed response actually contains job data or just Cloudflare challenge."""
import requests, json

r = requests.get(
    "https://r.jina.ai/www.indeed.com/rss?q=network+engineer&sort=date",
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
)
text = r.text
print(f"Status: {r.status_code}")
print(f"Length: {len(text)} chars")
print(f"Contains 'job': {'job' in text.lower()}")
print(f"Contains 'position': {'position' in text.lower()}")
print(f"Contains 'engineer': {'engineer' in text.lower()}")
print(f"Contains '<rss': {'<rss' in text}")
print(f"Contains '<item': {'<item' in text}")
print(f"Contains '<entry': {'<entry' in text}")
print(f"Contains 'Just a moment': {'just a moment' in text.lower()}")
print(f"Contains 'Cloudflare': {'cloudflare' in text.lower()}")
print()
print("First 600 chars:")
print(text[:600])
print()
print("Last 500 chars:")
print(text[-500:])

# Save full response
with open("proxy_test_results/jina_full_response.txt", "w", encoding="utf-8") as f:
    f.write(text)
print("\nFull response saved to: proxy_test_results/jina_full_response.txt")

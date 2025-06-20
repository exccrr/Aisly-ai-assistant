import httpx
GROQ_API_KEY = "your-api-key"
GROQ_MODEL = "llama3-70b-8192"

def ask_groq(messages):
    try:
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.7},
            timeout=30
        )
        if resp.status_code != 200:
            return f"❌ HTTP {resp.status_code}: {resp.text}"
        data = resp.json()
        if "error" in data:
            return f"❌ API error: {data['error'].get('message')}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Исключение: {e}"

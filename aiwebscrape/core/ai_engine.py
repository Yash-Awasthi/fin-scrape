import os
from dotenv import load_dotenv
import requests
import re

# Load .env from the root of the project
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in environment variables.")




#"anthropic/claude-3-haiku",  #qwen #metallama
def call_ai(prompt, system_prompt):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 400,
                "response_format": {"type": "json_object"}
            },
            timeout=45
        )

        if response.status_code != 200:
            print("AI HTTP ERROR:", response.text)
            return ""

        try:
            data = response.json()

            if "choices" not in data:
                return ""

            content = data["choices"][0]["message"]["content"]
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                return match.group(0)
            return content

        except Exception as e:
                print("AI PARSE ERROR:", e)
                return ""

    except requests.exceptions.RequestException:
        return ""

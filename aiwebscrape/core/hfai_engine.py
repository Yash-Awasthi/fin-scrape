import os
import requests

# Use environment variable for security (don't hardcode token)
HF_TOKEN = ""# ignore this , i am running locally fo now

def call_ai(prompt, system_prompt):
    if not HF_TOKEN:
        print("[ERROR] HF_TOKEN not found in environment variables")
        return ""

    try:
        response = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/Llama-3.3-70B-Instruct:fastest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0,
                "max_tokens": 400,
                "response_format": {"type": "json_object"}
            },
            timeout=45 
        )

        if response.status_code != 200:
            print(f"[ERROR] Hugging Face API error {response.status_code}: {response.text}")
            return ""

        data = response.json()

        if "choices" not in data or not data["choices"]:
            print("[ERROR] No choices in response:", data)
            return ""

        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return ""
    except Exception as e:
        print(f"[ERROR] Unexpected error in call_ai: {e}")
        return ""
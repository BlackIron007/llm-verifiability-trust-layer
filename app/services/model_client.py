import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL


class ModelClient:

    @staticmethod
    def generate(prompt: str) -> str:
        """
        Sends prompt to OpenRouter model and returns raw text response.
        """

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }

        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Model API error: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]
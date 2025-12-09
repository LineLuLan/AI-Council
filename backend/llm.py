from re import S
import requests
from config import Settings

# Default to localhost:11434, but allow env config if needed later
OLLAMA_URL = Settings().OLLAMA_URL

def chat_with_local_model(prompt: str, model: str = "llama3"):
    """
    Sends a prompt to the local Ollama instance and returns the response.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False  # Return the whole response at once
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        
        if response.status_code == 200:
            # Parse the specific JSON structure from Ollama
            data = response.json()
            return data.get("message", {}).get("content", "")
        else:
            return f"Error: Ollama returned status {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Is it running on port 11434?"
from re import S
import requests
from config import Settings

# Default to localhost:11434, but allow env config if needed later
OLLAMA_URL = Settings().OLLAMA_URL
def chat_with_local_model(prompt: str, system_instruction: str | None, model: str = "llama3"):
    """
    Sends a chat request to Ollama with a System Prompt.
    """
    
    # 1. Build the System Prompt
    # Start with the global default
    final_system_prompt = Settings().DEFAULT_SYSTEM_PROMPT
    
    # If the user has custom instructions, append them
    if system_instruction:
        final_system_prompt += f"\n\nUser Custom Instructions:\n{system_instruction}"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False  # Return the whole response at once
    }

    # 2. Construct the Message History
    payload = {
        "model": model,
        "messages": [
            # The System Message comes FIRST
            {"role": "system", "content": final_system_prompt},
            # The User Message comes SECOND
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "")
        else:
            return f"Error: Ollama status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama."
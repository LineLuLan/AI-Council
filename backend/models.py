


from pydantic import BaseModel


class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

class ChatRequest(BaseModel):
    prompt: str
    model: str = "gemma3:270m" # Default model
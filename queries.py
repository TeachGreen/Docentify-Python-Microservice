from pydantic import BaseModel


class ChatbotQuery(BaseModel):
    user_message: str
    context: dict | None = {"tentativas": 0}

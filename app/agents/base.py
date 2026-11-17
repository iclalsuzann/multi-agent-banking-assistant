"""Base agent configuration, LLM initialization, and runner abstractions."""
import os
from typing import List, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from app.core.config import settings


def get_llm(model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
    """
    Returns configured ChatModel (ChatOpenAI if OPENAI_API_KEY is available,
    otherwise a robust DeterministicMockChatModel for offline/test environments).
    """
    api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")

    if api_key and not api_key.startswith("your_openai"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=temperature,
            api_key=api_key,
        )

    # Offline / Test fallback
    return FallbackDeterministicChatModel()


class FallbackDeterministicChatModel(BaseChatModel):
    """
    Deterministic Chat Model fallback for tests and offline execution when
    OPENAI_API_KEY is not configured.
    """

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any):
        from langchain_core.outputs import ChatGeneration, ChatResult

        last_message = messages[-1] if messages else HumanMessage(content="")
        content_text = str(last_message.content)

        response_text = (
            f"Talebiniz başarıyla incelendi. İlgili bankacılık ve finans verileri doğrultusunda "
            f"işlemleriniz gerçekleştirilmiş olup güncel durum kayıt altına alınmıştır."
        )

        generation = ChatGeneration(message=AIMessage(content=response_text))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "fallback-deterministic-chat"

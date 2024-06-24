from openai import AsyncOpenAI
from src.services.context_manager import ContextManager
from typing import Any


class LLMInteractionManager:
    def __init__(self, llm_client: AsyncOpenAI, context_manager: ContextManager):
        self.llm_client = llm_client
        self.context_manager = context_manager

    async def process_with_llm(
        self, thread_id: str, user_input: str, response_model: Any
    ) -> Any:
        self.context_manager.add_message(thread_id, "user", user_input)
        messages = self.context_manager.get_messages(thread_id)
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o",
            response_model=response_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        self.context_manager.add_message(thread_id, "assistant", str(response))
        return response

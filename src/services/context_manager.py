from typing import Dict, List
from src.models.context import Message, Thread
import logfire


class ContextManager:
    def __init__(self):
        self.threads: Dict[str, Thread] = {}

    def create_thread(self, thread_id: str) -> Thread:
        if thread_id in self.threads:
            raise ValueError(f"Thread with id {thread_id} already exists")
        thread = Thread(id=thread_id)
        self.threads[thread_id] = thread
        logfire.info(f"Created new thread: {thread_id}")
        return thread

    def get_thread(self, thread_id: str) -> Thread:
        if thread_id not in self.threads:
            raise ValueError(f"Thread with id {thread_id} does not exist")
        return self.threads[thread_id]

    def add_message(self, thread_id: str, role: str, content: str):
        thread = self.get_thread(thread_id)
        message = Message(role=role, content=content)
        thread.messages.append(message)
        logfire.info(
            f"Added message to thread: {thread_id}",
        )

    def get_messages(self, thread_id: str) -> List[Message]:
        return self.get_thread(thread_id).messages

    def clear_thread(self, thread_id: str):
        if thread_id in self.threads:
            del self.threads[thread_id]
            logfire.info(f"Cleared thread: {thread_id}")

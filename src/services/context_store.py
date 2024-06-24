import chromadb
from chromadb.config import Settings
from typing import List, Dict
import logfire


class ChromaContextStore:
    def __init__(self, name: str):
        self.name = name
        self.client = chromadb.Client(Settings(is_persistent=False))
        self.collection = self.client.create_collection(name)

    async def add(self, content: str, embedding: List[float], metadata: Dict = None):
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata] if metadata else None,
            ids=[str(self.collection.count() + 1)],
        )
        logfire.info(
            f"Added content to context store {self.name}",
        )

    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[str]:
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k
        )
        logfire.info(
            f"Searched context store {self.name} with {top_k} results",
        )
        return results["documents"][0]

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction, SentenceTransformerEmbeddingFunction
from config import settings
import os


class VectorStore:
    """
    Initializes a persistent ChromaDB client and collection.
    The underlying data persists to disk (defined in CHROMA_DB_PATH).
    """

    def __init__(self):
        self.db_path = settings.db_path
        self.collection_name = settings.collection_name

        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Create or retrieve the collection, prioritizing OpenAI embedders if a key exists."""
        embedding_function = None
        if os.environ.get("OPENAI_API_KEY"):
            embedding_function = OpenAIEmbeddingFunction(
                api_key=os.environ.get("OPENAI_API_KEY"), model_name="text-embedding-3-small"
            )
        # If no key, ChromaDB uses its default (SentenceTransformer locally)

        return self.client.get_or_create_collection(
            name=self.collection_name, embedding_function=embedding_function, metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: list[dict]) -> int:
        """
        Upserts a list of documents into the vector store.
        documents: List of dicts with keys 'id', 'text', and optional 'metadata'.
        """
        if self.collection.count() == 0:
            # Ensure the collection is properly built if it wasn't populated previously
            self.collection = self._get_or_create_collection()

        self.collection.add(
            ids=[doc["id"] for doc in documents],
            documents=[doc["text"] for doc in documents],
            metadatas=[doc.get("metadata", {}) for doc in documents],
        )
        return len(documents)

    def get_collection_size(self) -> int:
        return self.collection.count()

    def query(self, query_text: str, n_results: int = 3) -> list[dict]:
        """
        Performs a semantic search.
        Returns a list of dicts: { 'id', 'text', 'metadata', 'distance' }
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(query_texts=[query_text], n_results=n_results)

        output = []
        for i in range(len(results["ids"][0])):
            output.append(
                {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return output

    def delete_collection(self) -> None:
        self.client.delete_collection(self.collection_name)

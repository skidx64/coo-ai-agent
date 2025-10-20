"""RAG (Retrieval-Augmented Generation) service using ChromaDB or Bedrock Knowledge Base."""
from typing import List, Dict, Optional
import os

# Lazy import chromadb only when needed
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None


class RAGService:
    """Service for semantic search using ChromaDB or Bedrock Knowledge Base."""

    def __init__(self, persist_directory: str = "./vector_db"):
        """
        Initialize RAG service with ChromaDB or Bedrock KB.

        Args:
            persist_directory: Path to ChromaDB persistence directory
        """
        from ..config import settings

        self.persist_directory = persist_directory
        self.provider = settings.rag_provider
        self.client = None
        self.collection = None
        self.bedrock_agent = None
        self.kb_id = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB or Bedrock Knowledge Base client."""
        from ..config import settings

        if self.provider == "chromadb":
            if not CHROMADB_AVAILABLE:
                print("[RAG] ChromaDB not available - RAG features disabled")
                self.client = None
                self.collection = None
                return

            try:
                # Initialize ChromaDB client with persistence
                self.client = chromadb.PersistentClient(path=self.persist_directory)

                # Get or create collection
                collections = self.client.list_collections()

                if collections:
                    # Use existing collection
                    self.collection = collections[0]
                    print(f"[RAG] Loaded existing ChromaDB collection: {self.collection.name}")
                else:
                    print("[RAG] Warning: No collections found in vector database")
                    self.collection = None

            except Exception as e:
                print(f"[RAG] Error initializing ChromaDB: {e}")
                self.client = None
                self.collection = None

        elif self.provider == "bedrock_kb":
            try:
                import boto3
                self.bedrock_agent = boto3.client(
                    'bedrock-agent-runtime',
                    region_name=settings.aws_region
                )
                self.kb_id = settings.bedrock_kb_id
                print(f"[RAG] Initialized Bedrock Knowledge Base: {self.kb_id}")
            except Exception as e:
                print(f"[RAG] Error initializing Bedrock KB: {e}")
                self.bedrock_agent = None

    def search(self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for relevant documents using semantic similarity.

        Args:
            query: Search query text
            n_results: Number of results to return (default 5)
            filter_metadata: Optional metadata filter (e.g., {"category": "vaccines"})

        Returns:
            List of relevant documents with metadata and distances
        """
        if self.provider == "chromadb":
            if not self.collection:
                return []

            try:
                # Query ChromaDB collection
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=filter_metadata if filter_metadata else None
                )

                # Format ChromaDB results
                documents = []
                if results and results['documents'] and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        doc = {
                            "content": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                            "distance": results['distances'][0][i] if results['distances'] else 0,
                            "id": results['ids'][0][i] if results['ids'] else None
                        }
                        documents.append(doc)

                return documents

            except Exception as e:
                print(f"[RAG] Error searching ChromaDB: {e}")
                return []

        elif self.provider == "bedrock_kb":
            if not self.bedrock_agent or not self.kb_id:
                print("[RAG] Bedrock KB not configured")
                return []

            try:
                # Query Bedrock Knowledge Base
                response = self.bedrock_agent.retrieve(
                    knowledgeBaseId=self.kb_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': n_results
                        }
                    }
                )

                # Format Bedrock KB results
                documents = []
                for result in response.get('retrievalResults', []):
                    doc = {
                        "content": result['content']['text'],
                        "metadata": result.get('metadata', {}),
                        "distance": result.get('score', 0),
                        "id": result.get('location', {}).get('s3Location', {}).get('uri', None)
                    }
                    documents.append(doc)

                return documents

            except Exception as e:
                print(f"[RAG] Error searching Bedrock KB: {e}")
                return []

        return []

    def search_by_category(self, query: str, category: str, n_results: int = 3) -> List[Dict]:
        """
        Search for documents in a specific category.

        Args:
            query: Search query text
            category: Category to search in (pregnancy, vaccines, development, etc.)
            n_results: Number of results to return

        Returns:
            List of relevant documents from the specified category
        """
        filter_metadata = {"category": category}
        return self.search(query, n_results=n_results, filter_metadata=filter_metadata)

    def get_context_for_question(self, question: str, n_results: int = 5) -> str:
        """
        Get relevant context for answering a question.

        Args:
            question: User's question
            n_results: Number of documents to retrieve

        Returns:
            Combined context string from relevant documents
        """
        results = self.search(question, n_results=n_results)

        if not results:
            return ""

        # Combine document contents
        context_parts = []
        for i, doc in enumerate(results, 1):
            category = doc['metadata'].get('category', 'general')
            content = doc['content']
            context_parts.append(f"[Source {i} - {category}]\n{content}\n")

        return "\n".join(context_parts)

    def get_collection_info(self) -> Dict:
        """
        Get information about the vector database collection.

        Returns:
            Dictionary with collection metadata
        """
        if not self.collection:
            return {
                "status": "not_initialized",
                "count": 0,
                "name": None
            }

        try:
            count = self.collection.count()
            return {
                "status": "ready",
                "count": count,
                "name": self.collection.name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "count": 0
            }

    def get_available_categories(self) -> List[str]:
        """
        Get list of available categories in the knowledge base.

        Returns:
            List of category names
        """
        categories = [
            "pregnancy",
            "vaccines",
            "development",
            "symptoms",
            "activities",
            "education",
            "medical"
        ]
        return categories


# Global RAG service instance
rag_service = RAGService()

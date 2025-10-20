"""
Create Vector Embeddings for RAG
Windows-compatible (no emoji characters)
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import time

class EmbeddingCreator:
    """Creates vector embeddings for knowledge base"""
    
    def __init__(self):
        print("[INIT] Initializing embedding system...")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./vector_db")
        
        # Delete existing collection if exists
        try:
            self.client.delete_collection("coo_knowledge")
            print("  [OK] Cleared existing embeddings")
        except:
            pass
        
        # Create new collection
        self.collection = self.client.create_collection(
            name="coo_knowledge",
            metadata={"description": "Coo medical knowledge base - Pregnancy through Age 5"}
        )
        
        # Load embedding model
        print("  [LOADING] Downloading embedding model (first time only, ~100MB)...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        print("  [OK] Model loaded")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50):
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk) > 100:  # Skip tiny chunks
                chunks.append(chunk)
        
        return chunks
    
    def index_knowledge_base(self):
        """Index all markdown files"""
        print("\n[INDEXING] Processing knowledge base...")
        
        kb_dir = Path("knowledge-base")
        
        documents = []
        metadatas = []
        ids = []
        doc_id = 0
        
        # Process all markdown files
        for md_file in kb_dir.rglob("*.md"):
            print(f"  [FILE] {md_file.relative_to(kb_dir)}")
            
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into chunks
            chunks = self.chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": str(md_file.relative_to(kb_dir)),
                    "category": md_file.parent.name,
                    "filename": md_file.name,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                })
                ids.append(f"doc_{doc_id}")
                doc_id += 1
        
        print(f"\n  [STATS] Total chunks: {len(documents)}")
        print("  [EMBEDDING] Creating embeddings (this will take 2-3 minutes)...")
        
        # Create embeddings
        embeddings = self.embedder.encode(
            documents,
            show_progress_bar=True,
            batch_size=32
        )
        
        print("  [STORING] Saving to vector database...")
        
        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            
            self.collection.add(
                documents=documents[i:end],
                embeddings=embeddings[i:end].tolist(),
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
        
        print("  [OK] Vector database created!")
    
    def test_retrieval(self):
        """Test the RAG system"""
        print("\n[TESTING] Testing retrieval system...\n")
        
        test_queries = [
            "My baby has a fever after vaccines",
            "What can I buy during second trimester?",
            "When should my toddler start swimming classes?",
            "How do I choose a preschool?",
            "2 month developmental milestones"
        ]
        
        for query in test_queries:
            print(f"Query: '{query}'")
            
            # Create query embedding
            query_embedding = self.embedder.encode([query])[0]
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=3
            )
            
            print("  Top results:")
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"    {i+1}. {metadata['category']}/{metadata['filename']}")
                print(f"       {doc[:80]}...")
            print()
    
    def run_all(self):
        """Run complete embedding creation"""
        print("=" * 60)
        print("CREATING VECTOR EMBEDDINGS FOR RAG")
        print("=" * 60)
        
        start_time = time.time()
        
        self.index_knowledge_base()
        self.test_retrieval()
        
        elapsed = time.time() - start_time
        
        # Get stats
        count = self.collection.count()
        
        print("=" * 60)
        print(f"COMPLETE ({elapsed/60:.1f} minutes)")
        print("=" * 60)
        print(f"\nVector Database Stats:")
        print(f"  - Total embeddings: {count}")
        print(f"  - Storage location: ./vector_db")
        print(f"  - Embedding model: all-MiniLM-L6-v2")
        print(f"  - Dimensions: 384")
        
        print("\n[SUCCESS] Day 1 Complete! Your data is ready!")
        print("\nNext steps:")
        print("  - Day 2: Set up Twilio for SMS")
        print("  - Day 3: Build backend API")
        print("  - Day 4: Create agentic AI workflows")


def main():
    creator = EmbeddingCreator()
    creator.run_all()


if __name__ == "__main__":
    main()
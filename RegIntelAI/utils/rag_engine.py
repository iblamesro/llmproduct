"""
RAG (Retrieval-Augmented Generation) engine for RegIntel AI
"""
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from config import (
    OPENAI_API_KEY,
    MODEL_NAME,
    EMBEDDING_MODEL,
    CHROMA_DB_DIR,
    COLLECTION_NAME,
    TOP_K_RESULTS
)


class RAGEngine:
    """RAG Engine using ChromaDB and OpenAI"""
    
    def __init__(self):
        """Initialize RAG engine with vector store and LLM"""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        except:
            self.collection = self.chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Regulatory documents for compliance analysis"}
            )
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    
    def add_documents(self, chunks: List[Dict[str, any]]):
        """
        Add document chunks to vector store
        
        Args:
            chunks: List of document chunks with metadata
        """
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for chunk in chunks:
            text = chunk["text"]
            metadata = chunk["metadata"]
            
            # Generate unique ID
            doc_id = f"{metadata['source']}_chunk_{metadata['chunk_id']}"
            
            # Get embedding
            embedding = self.get_embedding(text)
            
            documents.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
            embeddings.append(embedding)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
    
    def retrieve(self, query: str, n_results: int = TOP_K_RESULTS) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: Search query
            n_results: Number of results to retrieve
            
        Returns:
            List of retrieved chunks with metadata
        """
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Query vector store
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        retrieved_chunks = []
        if results["documents"] and len(results["documents"]) > 0:
            for idx in range(len(results["documents"][0])):
                retrieved_chunks.append({
                    "text": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "distance": results["distances"][0][idx] if "distances" in results else None
                })
        
        return retrieved_chunks
    
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate answer using LLM with retrieved context
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            
        Returns:
            Generated answer
        """
        # Build context from retrieved chunks
        context = "\n\n---\n\n".join([
            f"Source: {chunk['metadata']['source']} (Chunk {chunk['metadata']['chunk_id'] + 1})\n{chunk['text']}"
            for chunk in context_chunks
        ])
        
        # System prompt for compliance analysis
        system_prompt = """You are RegIntel AI, an expert regulatory compliance assistant for HexaBank.

Your role is to:
- Analyze regulatory documents (EU AI Act, EBA guidelines, ECB regulations, GDPR, etc.)
- Perform gap analyses between regulations and internal policies
- Extract key compliance requirements
- Provide traceable, evidence-based answers with citations

Always:
- Ground your answers in the provided context
- Reference specific sources and sections
- Be precise and actionable
- Highlight compliance gaps or risks
- Use a professional, clear tone
- Respond in the same language as the query (French or English)"""

        user_prompt = f"""Based on the following regulatory documents:

{context}

---

Question: {query}

Provide a detailed, evidence-based answer. Include specific references to the source documents."""

        # Generate response
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower temperature for factual responses
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    def query(self, question: str) -> Dict[str, any]:
        """
        Complete RAG query: retrieve + generate
        
        Args:
            question: User question
            
        Returns:
            Dictionary with answer and retrieved chunks
        """
        # Retrieve relevant chunks
        chunks = self.retrieve(question)
        
        # Generate answer
        answer = self.generate_answer(question, chunks)
        
        return {
            "answer": answer,
            "sources": chunks
        }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.chroma_client.delete_collection(name=COLLECTION_NAME)
            self.collection = self.chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Regulatory documents for compliance analysis"}
            )
        except Exception as e:
            print(f"Error clearing collection: {e}")
    
    def get_document_count(self) -> int:
        """Get number of documents in collection"""
        try:
            return self.collection.count()
        except:
            return 0

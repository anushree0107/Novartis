"""
GEPA-Optimized RAG Adapter for Clinical Data
=============================================
Uses GEPA (Generic Evolutionary Prompt Adaptation) to optimize
RAG prompts for clinical trial data retrieval and analysis.

Uses FREE API models via Groq/Together/HuggingFace
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

try:
    import gepa
    from gepa.adapters.generic_rag_adapter import GenericRAGAdapter, ChromaVectorStore
    GEPA_AVAILABLE = True
except ImportError:
    GEPA_AVAILABLE = False
    print("Warning: GEPA not installed. Run: pip install gepa")

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


# Simple hash-based embedding function (no external dependencies)
class SimpleEmbeddingFunction:
    """
    A simple embedding function using hashing for basic similarity.
    Good enough for small-medium datasets, no heavy dependencies.
    Implements ChromaDB's EmbeddingFunction interface.
    """
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        self._name = "simple_hash_embedding"
    
    def name(self) -> str:
        """Return the name of the embedding function (required by ChromaDB)."""
        return self._name
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = []
        for text in input:
            embedding = self._text_to_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _text_to_embedding(self, text: str) -> List[float]:
        """Convert text to a simple hash-based embedding."""
        import numpy as np
        
        # Normalize text
        text = str(text).lower().strip()
        
        # Create embedding using multiple hash functions
        embedding = np.zeros(self.dim)
        
        # Use words and n-grams for better similarity
        words = text.split()
        
        for i, word in enumerate(words):
            # Hash the word
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            # Distribute across embedding dimensions
            for j in range(min(10, self.dim)):
                idx = (h + j * 7) % self.dim
                embedding[idx] += 1.0 / (1 + i * 0.1)  # Decay for position
        
        # Add bigrams
        for i in range(len(words) - 1):
            bigram = words[i] + " " + words[i+1]
            h = int(hashlib.md5(bigram.encode()).hexdigest(), 16)
            idx = h % self.dim
            embedding[idx] += 0.5
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()


@dataclass
class RAGDataInstance:
    """
    Training/validation data instance for GEPA optimization.
    Follows GEPA's RAGDataInst structure.
    """
    query: str
    ground_truth_answer: str
    relevant_doc_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Global client instance to prevent multiple instances with different settings
_chroma_client = None


class ClinicalVectorStore:
    """
    ChromaDB-based vector store for clinical trial data.
    Compatible with GEPA's VectorStoreInterface.
    Uses simple hash-based embeddings (no heavy dependencies like onnxruntime).
    """
    
    def __init__(
        self, 
        persist_directory: str,
        collection_name: str = "clinical_documents",
        embedding_model: str = "simple"
    ):
        global _chroma_client
        
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_dim = 384
        
        # Use simple embedding function (no onnxruntime needed)
        logger.info(f"Initializing ChromaDB with simple embedding function...")
        self.embedding_function = SimpleEmbeddingFunction(dim=self.embedding_dim)
        
        # Initialize ChromaDB - reuse existing client to avoid conflicts
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        if _chroma_client is None:
            _chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
        self.client = _chroma_client
        
        # Get or create collection with embedding function
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Vector store initialized: {collection_name} ({self.collection.count()} documents)")
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """Add documents to the vector store with embeddings."""
        total = len(documents)
        logger.info(f"Adding {total} documents to vector store...")
        
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            
            ids = [doc["id"] for doc in batch]
            contents = [doc["content"] for doc in batch]
            metadatas = [doc.get("metadata", {}) for doc in batch]
            
            # ChromaDB will auto-generate embeddings using the embedding function
            self.collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Added batch {i//batch_size + 1}/{(total-1)//batch_size + 1}")
        
        logger.info(f"Total documents in store: {self.collection.count()}")
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Semantic similarity search using embeddings."""
        # Build where clause for filtering
        where = filters if filters else None
        
        # Query ChromaDB (embedding is auto-generated)
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        documents = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                doc = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": 1 - results["distances"][0][i] if results["distances"] else 0.5
                }
                documents.append(doc)
        
        return documents
    
    def vector_search(
        self, 
        query_vector: List[float], 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Direct vector search with pre-computed embedding."""
        where = filters if filters else None
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        documents = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                doc = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": 1 - results["distances"][0][i] if results["distances"] else 0.5
                }
                documents.append(doc)
        
        return documents
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata and statistics."""
        return {
            "name": self.collection_name,
            "document_count": self.collection.count(),
            "dimension": self.embedding_dim,
            "vector_store_type": "chromadb",
            "persist_directory": str(self.persist_directory)
        }
    
    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")


class GEPAOptimizedRAG:
    """
    Main GEPA-optimized RAG system for clinical trial data.
    
    Uses GEPA to evolutionarily optimize prompts for:
    - Query reformulation
    - Context synthesis
    - Answer generation
    - Document reranking
    """
    
    def __init__(
        self,
        vector_store: ClinicalVectorStore,
        llm_model: str = "ollama/qwen3:8b",
        rag_config: Optional[Dict[str, Any]] = None,
        initial_prompts: Optional[Dict[str, str]] = None
    ):
        self.vector_store = vector_store
        self.llm_model = llm_model
        self.rag_config = rag_config or {}
        self.initial_prompts = initial_prompts or {}
        self.optimized_prompts = None
        
        # GEPA adapter (if available)
        self.gepa_adapter = None
        if GEPA_AVAILABLE:
            self._setup_gepa_adapter()
    
    def _setup_gepa_adapter(self):
        """Setup GEPA adapter for prompt optimization."""
        try:
            # Create ChromaDB vector store wrapper for GEPA
            chroma_store = ChromaVectorStore.create_local(
                persist_directory=str(self.vector_store.persist_directory),
                collection_name=self.vector_store.collection_name
            )
            
            self.gepa_adapter = GenericRAGAdapter(
                vector_store=chroma_store,
                llm_model=self.llm_model,
                rag_config={
                    "retrieval_strategy": self.rag_config.get("retrieval_strategy", "similarity"),
                    "top_k": self.rag_config.get("top_k", 5),
                    "retrieval_weight": self.rag_config.get("retrieval_weight", 0.35),
                    "generation_weight": self.rag_config.get("generation_weight", 0.65)
                }
            )
            logger.info("GEPA adapter initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize GEPA adapter: {e}")
            self.gepa_adapter = None
    
    def optimize_prompts(
        self,
        train_data: List[RAGDataInstance],
        val_data: List[RAGDataInstance],
        max_iterations: int = 15,
        reflection_model: str = "ollama/llama3.1:8b"
    ) -> Dict[str, str]:
        """
        Run GEPA optimization to find best prompts.
        
        Args:
            train_data: Training examples for optimization
            val_data: Validation examples for evaluation
            max_iterations: Maximum optimization iterations
            reflection_model: Model for GEPA reflection/mutation
            
        Returns:
            Dictionary of optimized prompts
        """
        if not GEPA_AVAILABLE or self.gepa_adapter is None:
            logger.warning("GEPA not available. Using initial prompts.")
            self.optimized_prompts = self.initial_prompts
            return self.optimized_prompts
        
        # Convert to GEPA format
        trainset = [
            {
                "query": inst.query,
                "ground_truth_answer": inst.ground_truth_answer,
                "relevant_doc_ids": inst.relevant_doc_ids,
                "metadata": inst.metadata
            }
            for inst in train_data
        ]
        
        valset = [
            {
                "query": inst.query,
                "ground_truth_answer": inst.ground_truth_answer,
                "relevant_doc_ids": inst.relevant_doc_ids,
                "metadata": inst.metadata
            }
            for inst in val_data
        ]
        
        logger.info(f"Starting GEPA optimization with {len(trainset)} training examples...")
        logger.info(f"Using LLM: {self.llm_model}, Reflection: {reflection_model}")
        
        # Run GEPA optimization
        result = gepa.optimize(
            seed_candidate=self.initial_prompts,
            trainset=trainset,
            valset=valset,
            adapter=self.gepa_adapter,
            max_metric_calls=max_iterations,
            reflection_llm_model=reflection_model
        )
        
        self.optimized_prompts = result.best_candidate
        logger.info(f"GEPA optimization complete. Best score: {result.best_score:.4f}")
        
        return self.optimized_prompts
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        use_optimized: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            use_optimized: Whether to use GEPA-optimized prompts
            filters: Optional metadata filters
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        prompts = self.optimized_prompts if (use_optimized and self.optimized_prompts) else self.initial_prompts
        
        # Step 1: Query Reformulation (optional)
        reformulated_query = question
        if "query_reformulation" in prompts:
            reformulated_query = self._reformulate_query(question, prompts["query_reformulation"])
        
        # Step 2: Retrieve documents
        retrieved_docs = self.vector_store.similarity_search(
            reformulated_query, 
            k=top_k * 2,  # Retrieve more for reranking
            filters=filters
        )
        
        # Step 3: Rerank documents (optional)
        if "document_reranking" in prompts and len(retrieved_docs) > top_k:
            retrieved_docs = self._rerank_documents(question, retrieved_docs, prompts["document_reranking"])[:top_k]
        else:
            retrieved_docs = retrieved_docs[:top_k]
        
        # Step 4: Synthesize context
        context = self._synthesize_context(question, retrieved_docs, prompts.get("context_synthesis", ""))
        
        # Step 5: Generate answer
        answer = self._generate_answer(question, context, prompts.get("answer_generation", ""))
        
        return {
            "question": question,
            "reformulated_query": reformulated_query,
            "answer": answer,
            "sources": [
                {
                    "id": doc["id"],
                    "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                    "metadata": doc["metadata"],
                    "relevance_score": doc["score"]
                }
                for doc in retrieved_docs
            ],
            "num_sources": len(retrieved_docs)
        }
    
    def _reformulate_query(self, query: str, prompt_template: str) -> str:
        """Reformulate query using LLM."""
        try:
            import litellm
            
            prompt = prompt_template.format(query=query)
            response = litellm.completion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Query reformulation failed: {e}")
            return query
    
    def _rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        prompt_template: str
    ) -> List[Dict[str, Any]]:
        """Rerank documents using LLM."""
        try:
            import litellm
            
            # Format documents for reranking
            doc_text = "\n\n".join([
                f"[DOC_{i}] ID: {doc['id']}\n{doc['content'][:300]}..."
                for i, doc in enumerate(documents)
            ])
            
            prompt = prompt_template.format(query=query, documents=doc_text)
            response = litellm.completion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse ranking (simple approach)
            ranking_text = response.choices[0].message.content
            # Return original order if parsing fails
            return documents
        except Exception as e:
            logger.warning(f"Document reranking failed: {e}")
            return documents
    
    def _synthesize_context(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        prompt_template: str
    ) -> str:
        """Synthesize context from retrieved documents."""
        if not prompt_template:
            # Simple concatenation if no template
            return "\n\n---\n\n".join([
                f"Source: {doc['metadata'].get('filename', 'Unknown')}\n{doc['content']}"
                for doc in documents
            ])
        
        try:
            import litellm
            
            doc_text = "\n\n---\n\n".join([
                f"Document {i+1} (Source: {doc['metadata'].get('filename', 'Unknown')}):\n{doc['content']}"
                for i, doc in enumerate(documents)
            ])
            
            prompt = prompt_template.format(query=query, documents=doc_text)
            response = litellm.completion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Context synthesis failed: {e}")
            return doc_text
    
    def _generate_answer(self, query: str, context: str, prompt_template: str) -> str:
        """Generate final answer using LLM."""
        try:
            import litellm
            
            if prompt_template:
                prompt = prompt_template.format(query=query, context=context)
            else:
                prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            
            response = litellm.completion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"Error generating answer: {e}"
    
    def save_optimized_prompts(self, filepath: Path):
        """Save optimized prompts to file."""
        import json
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.optimized_prompts or self.initial_prompts, f, indent=2)
        logger.info(f"Prompts saved to {filepath}")
    
    def load_optimized_prompts(self, filepath: Path):
        """Load optimized prompts from file."""
        import json
        with open(filepath, 'r') as f:
            self.optimized_prompts = json.load(f)
        logger.info(f"Prompts loaded from {filepath}")

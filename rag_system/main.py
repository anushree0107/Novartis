"""
GEPA-Optimized RAG System - Main Application
=============================================
Complete RAG system for clinical trial data using GEPA prompt optimization.

Uses FREE local models via Ollama:
- qwen3:8b or llama3.1:8b for generation
- nomic-embed-text or sentence-transformers for embeddings

Setup Instructions:
1. Install Ollama: https://ollama.ai
2. Pull models: ollama pull qwen3:8b && ollama pull llama3.1:8b
3. Install dependencies: pip install -r requirements.txt
4. Run: python main.py
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.gepa_settings import (
    DATA_DIR, 
    VECTOR_DB_DIR,
    OLLAMA_CONFIG,
    GEPA_CONFIG,
    RAG_CONFIG,
    INITIAL_PROMPTS,
    CLINICAL_DATA_SCHEMA,
    LOGGING_CONFIG
)
from src.data_loader import ClinicalDataLoader, DocumentChunker, Document
from src.gepa_rag_adapter import ClinicalVectorStore, GEPAOptimizedRAG, RAGDataInstance

# Setup logging
import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class ClinicalRAGSystem:
    """
    Complete GEPA-optimized RAG system for NEST 2.0 clinical data.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        vector_db_dir: Optional[Path] = None,
        llm_model: Optional[str] = None
    ):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.vector_db_dir = Path(vector_db_dir) if vector_db_dir else VECTOR_DB_DIR
        self.llm_model = llm_model or OLLAMA_CONFIG["llm_model"]
        
        # Components
        self.data_loader = None
        self.vector_store = None
        self.rag_system = None
        
        logger.info(f"Initializing Clinical RAG System")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Vector DB directory: {self.vector_db_dir}")
        logger.info(f"LLM Model: {self.llm_model}")
    
    def load_and_index_data(self, force_reload: bool = False, limit: Optional[int] = None) -> int:
        """
        Load clinical data and index into vector store.
        
        Args:
            force_reload: If True, reload data even if index exists
            limit: Max number of files to process (for testing)
            
        Returns:
            Number of documents indexed
        """
        if limit:
            logger.info(f"Loading clinical data (limited to {limit} files)...")
        else:
            logger.info("Loading clinical data from NEST 2.0 files...")
        
        # Initialize data loader
        self.data_loader = ClinicalDataLoader(self.data_dir)
        documents = self.data_loader.load_all_data(limit=limit)
        
        if len(documents) == 0:
            logger.warning("No documents found. Check data directory path.")
            return 0
        
        # Chunk documents for better retrieval
        logger.info("Chunking documents...")
        chunker = DocumentChunker(
            chunk_size=RAG_CONFIG["chunk_size"],
            chunk_overlap=RAG_CONFIG["chunk_overlap"]
        )
        chunked_docs = chunker.chunk_all_documents(documents)
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        self.vector_store = ClinicalVectorStore(
            persist_directory=str(self.vector_db_dir),
            collection_name="clinical_documents",
            embedding_model=OLLAMA_CONFIG["local_embedding_model"]
        )
        
        # Check if we need to reload
        current_count = self.vector_store.collection.count()
        if current_count > 0 and not force_reload:
            logger.info(f"Vector store already contains {current_count} documents. Use force_reload=True to reload.")
            return current_count
        
        # Clear existing if reloading
        if force_reload and current_count > 0:
            logger.info("Force reload: clearing existing documents...")
            self.vector_store.delete_collection()
            self.vector_store = ClinicalVectorStore(
                persist_directory=str(self.vector_db_dir),
                collection_name="clinical_documents",
                embedding_model=OLLAMA_CONFIG["local_embedding_model"]
            )
        
        # Prepare documents for indexing
        docs_for_indexing = [
            {
                "id": doc.doc_id,
                "content": doc.content,
                "metadata": {
                    k: str(v) if isinstance(v, list) else v 
                    for k, v in doc.metadata.items()
                }
            }
            for doc in chunked_docs
        ]
        
        # Index documents
        logger.info(f"Indexing {len(docs_for_indexing)} document chunks...")
        self.vector_store.add_documents(docs_for_indexing)
        
        # Print summary
        summary = self.data_loader.get_study_summary()
        logger.info(f"Data loading complete:")
        logger.info(f"  - Total documents: {summary['total_documents']}")
        logger.info(f"  - Unique studies: {summary['unique_studies']}")
        logger.info(f"  - Report types: {summary['report_type_counts']}")
        
        return len(docs_for_indexing)
    
    def initialize_rag(self) -> GEPAOptimizedRAG:
        """Initialize the GEPA-optimized RAG system."""
        if self.vector_store is None:
            # Try to load existing vector store
            self.vector_store = ClinicalVectorStore(
                persist_directory=str(self.vector_db_dir),
                collection_name="clinical_documents",
                embedding_model=OLLAMA_CONFIG["local_embedding_model"]
            )
            
            if self.vector_store.collection.count() == 0:
                logger.warning("Vector store is empty. Indexing data now...")
                print("\n⚠️  Vector store is empty. Let me index the clinical data first...")
                print("This may take a few minutes...\n")
                self.load_and_index_data()
                
                if self.vector_store.collection.count() == 0:
                    raise ValueError("No data found to index. Check that data directory exists and contains Excel files.")
        
        # Initialize RAG system
        self.rag_system = GEPAOptimizedRAG(
            vector_store=self.vector_store,
            llm_model=self.llm_model,
            rag_config=RAG_CONFIG,
            initial_prompts=INITIAL_PROMPTS
        )
        
        logger.info("RAG system initialized successfully")
        return self.rag_system
    
    def create_training_data(self) -> List[RAGDataInstance]:
        """
        Create training data for GEPA optimization.
        These are example Q&A pairs for the clinical data domain.
        """
        # Example training data for clinical study queries
        training_data = [
            RAGDataInstance(
                query="What is the total number of EDC metrics records across all studies?",
                ground_truth_answer="The EDC metrics reports contain subject counts, visit completion rates, and form status information for each study.",
                relevant_doc_ids=[],  # Will be populated during retrieval
                metadata={"category": "EDC_Metrics", "complexity": "simple"}
            ),
            RAGDataInstance(
                query="Show me the safety adverse event data from the eSAE dashboards",
                ground_truth_answer="The eSAE Dashboard reports contain safety reporting data including SAE counts, severity levels, relatedness assessments, and outcomes.",
                relevant_doc_ids=[],
                metadata={"category": "eSAE", "complexity": "medium"}
            ),
            RAGDataInstance(
                query="What MedDRA coding information is available?",
                ground_truth_answer="The MedDRA Global Coding Reports contain medical terminology coding including preferred terms, system organ class (SOC), high level group terms (HLGT), and high level terms (HLT).",
                relevant_doc_ids=[],
                metadata={"category": "MedDRA_Coding", "complexity": "medium"}
            ),
            RAGDataInstance(
                query="Are there any missing pages or incomplete forms in the studies?",
                ground_truth_answer="The Missing Pages Reports track incomplete data forms across study sites and subjects, showing form names and missing counts.",
                relevant_doc_ids=[],
                metadata={"category": "Missing_Pages", "complexity": "simple"}
            ),
            RAGDataInstance(
                query="What WHODD drug coding data is available?",
                ground_truth_answer="The WHODD Global Coding Reports contain WHO Drug Dictionary coding including drug names, ATC codes, routes of administration, and formulations.",
                relevant_doc_ids=[],
                metadata={"category": "WHODD_Coding", "complexity": "medium"}
            ),
            RAGDataInstance(
                query="Compare the data quality across Study 1 and Study 10",
                ground_truth_answer="Comparison requires examining the EDRR compiled reports for both studies, looking at query counts, response rates, and data completeness metrics.",
                relevant_doc_ids=[],
                metadata={"category": "EDRR", "complexity": "complex"}
            ),
            RAGDataInstance(
                query="What laboratory test data is missing ranges or names?",
                ground_truth_answer="The Missing Lab Name and Missing Ranges reports identify laboratory tests with missing reference ranges, test names, units, and affected sites.",
                relevant_doc_ids=[],
                metadata={"category": "Lab_Ranges", "complexity": "medium"}
            ),
            RAGDataInstance(
                query="Show visit tracking and projection data",
                ground_truth_answer="The Visit Projection Tracker reports contain scheduled visit information including visit names, expected dates, actual dates, and completion status.",
                relevant_doc_ids=[],
                metadata={"category": "Visit_Tracker", "complexity": "simple"}
            )
        ]
        
        return training_data
    
    def optimize_with_gepa(
        self,
        train_data: Optional[List[RAGDataInstance]] = None,
        max_iterations: int = None
    ) -> Dict[str, str]:
        """
        Run GEPA optimization on RAG prompts.
        
        Args:
            train_data: Training examples (uses default if None)
            max_iterations: Number of optimization iterations
            
        Returns:
            Optimized prompts dictionary
        """
        if self.rag_system is None:
            self.initialize_rag()
        
        # Use provided or create default training data
        training_data = train_data or self.create_training_data()
        
        # Split into train and validation
        split_idx = int(len(training_data) * 0.7)
        train_set = training_data[:split_idx]
        val_set = training_data[split_idx:]
        
        logger.info(f"Running GEPA optimization with {len(train_set)} train, {len(val_set)} val examples")
        
        # Run optimization
        optimized = self.rag_system.optimize_prompts(
            train_data=train_set,
            val_data=val_set,
            max_iterations=max_iterations or GEPA_CONFIG["max_metric_calls"],
            reflection_model=OLLAMA_CONFIG["reflection_model"]
        )
        
        # Save optimized prompts
        prompts_path = self.vector_db_dir / "optimized_prompts.json"
        self.rag_system.save_optimized_prompts(prompts_path)
        
        return optimized
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User's question about clinical data
            top_k: Number of documents to retrieve
            filters: Optional metadata filters (e.g., {"study_id": "Study_1"})
            
        Returns:
            Response with answer and sources
        """
        if self.rag_system is None:
            self.initialize_rag()
            
            # Try to load optimized prompts if they exist
            prompts_path = self.vector_db_dir / "optimized_prompts.json"
            if prompts_path.exists():
                self.rag_system.load_optimized_prompts(prompts_path)
        
        return self.rag_system.query(
            question=question,
            top_k=top_k,
            filters=filters
        )
    
    def interactive_mode(self):
        """Run interactive query mode."""
        print("\n" + "="*60)
        print("GEPA-Optimized Clinical RAG System")
        print("="*60)
        print(f"Model: {self.llm_model}")
        print(f"Documents indexed: {self.vector_store.collection.count() if self.vector_store else 'N/A'}")
        print("\nType 'quit' to exit, 'help' for commands")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("\n📋 Your question: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'quit':
                    print("Goodbye!")
                    break
                    
                if user_input.lower() == 'help':
                    print("\nCommands:")
                    print("  quit     - Exit the system")
                    print("  help     - Show this help")
                    print("  stats    - Show system statistics")
                    print("  optimize - Run GEPA optimization")
                    print("\nOr just type your question about the clinical data!")
                    continue
                    
                if user_input.lower() == 'stats':
                    if self.vector_store:
                        info = self.vector_store.get_collection_info()
                        print(f"\nVector Store Stats:")
                        print(f"  Documents: {info['document_count']}")
                        print(f"  Embedding dim: {info['dimension']}")
                    if self.data_loader:
                        summary = self.data_loader.get_study_summary()
                        print(f"\nData Summary:")
                        print(f"  Studies: {summary['unique_studies']}")
                        print(f"  Report types: {list(summary['report_type_counts'].keys())}")
                    continue
                    
                if user_input.lower() == 'optimize':
                    print("\nRunning GEPA optimization...")
                    self.optimize_with_gepa()
                    print("Optimization complete!")
                    continue
                
                # Query the system
                print("\n🔍 Searching...")
                result = self.query(user_input)
                
                print("\n" + "-"*50)
                print("📝 ANSWER:")
                print("-"*50)
                print(result["answer"])
                
                print("\n" + "-"*50)
                print(f"📚 SOURCES ({result['num_sources']} documents):")
                print("-"*50)
                for i, source in enumerate(result["sources"][:3], 1):
                    print(f"\n{i}. {source['metadata'].get('filename', 'Unknown')}")
                    print(f"   Study: {source['metadata'].get('study_id', 'N/A')}")
                    print(f"   Type: {source['metadata'].get('report_type', 'N/A')}")
                    print(f"   Relevance: {source['relevance_score']:.3f}")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GEPA-Optimized Clinical RAG System")
    parser.add_argument("--index", action="store_true", help="Load and index data")
    parser.add_argument("--force-reload", action="store_true", help="Force reload data")
    parser.add_argument("--optimize", action="store_true", help="Run GEPA optimization")
    parser.add_argument("--query", type=str, help="Query the system")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--model", type=str, default=None, help="LLM model to use")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process (for testing)")
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        rag = ClinicalRAGSystem(llm_model=args.model)
        
        if args.index or args.force_reload:
            rag.load_and_index_data(force_reload=args.force_reload, limit=args.limit)
        
        if args.optimize:
            rag.initialize_rag()
            rag.optimize_with_gepa()
        
        if args.query:
            result = rag.query(args.query)
            print("\nAnswer:", result["answer"])
            print("\nSources:")
            for s in result["sources"]:
                print(f"  - {s['metadata'].get('filename')}")
        
        if args.interactive or (not args.index and not args.optimize and not args.query):
            rag.initialize_rag()
            rag.interactive_mode()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure your API key is set in .env file")
        print("  2. Check that clinical data exists in the data directory")
        print("  3. Try running: python main.py --index")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

"""
GEPA-Optimized Clinical RAG - Streamlit Web Interface
======================================================
A user-friendly web interface for the GEPA-optimized RAG system.

Run with: streamlit run app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from config.gepa_settings import (
    DATA_DIR,
    VECTOR_DB_DIR,
    OLLAMA_CONFIG,
    CLINICAL_DATA_SCHEMA
)
from src.data_loader import ClinicalDataLoader, DocumentChunker
from src.gepa_rag_adapter import ClinicalVectorStore, GEPAOptimizedRAG
from config.gepa_settings import RAG_CONFIG, INITIAL_PROMPTS

# Page configuration
st.set_page_config(
    page_title="Clinical Data RAG - GEPA Optimized",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .source-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #e8f4ea;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def get_system_key():
    """Generate a unique key for the system configuration."""
    return f"{VECTOR_DB_DIR}_{OLLAMA_CONFIG['llm_model']}"


@st.cache_resource
def initialize_system(_key=None):
    """Initialize the RAG system (cached)."""
    try:
        vector_store = ClinicalVectorStore(
            persist_directory=str(VECTOR_DB_DIR),
            collection_name="clinical_documents",
            embedding_model=OLLAMA_CONFIG["local_embedding_model"]
        )
        
        rag_system = GEPAOptimizedRAG(
            vector_store=vector_store,
            llm_model=OLLAMA_CONFIG["llm_model"],
            rag_config=RAG_CONFIG,
            initial_prompts=INITIAL_PROMPTS
        )
        
        # Try to load optimized prompts
        prompts_path = VECTOR_DB_DIR / "optimized_prompts.json"
        if prompts_path.exists():
            rag_system.load_optimized_prompts(prompts_path)
        
        return vector_store, rag_system
    except Exception as e:
        # Clear any stale ChromaDB client references
        from src import gepa_rag_adapter
        gepa_rag_adapter._chroma_client = None
        raise e


def main():
    # Header
    st.title("🏥 Clinical Data RAG System")
    st.markdown("**GEPA-Optimized** | Powered by Local LLMs (Ollama)")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_options = [
            "ollama/qwen3:8b",
            "ollama/llama3.1:8b", 
            "ollama/llama3.2:1b",
            "ollama/mistral:7b"
        ]
        selected_model = st.selectbox(
            "LLM Model",
            model_options,
            index=0
        )
        
        # Retrieval settings
        st.subheader("Retrieval Settings")
        top_k = st.slider("Documents to retrieve", 3, 10, 5)
        
        # Filters
        st.subheader("Filters")
        
        # Study filter
        study_options = ["All Studies"] + [f"Study_{i}" for i in [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]]
        selected_study = st.selectbox("Study", study_options)
        
        # Report type filter
        report_options = ["All Types"] + list(CLINICAL_DATA_SCHEMA["report_types"].keys())
        selected_report = st.selectbox("Report Type", report_options)
        
        # System info
        st.subheader("📊 System Info")
        
        # Add reset button
        if st.button("🔄 Reset Cache"):
            st.cache_resource.clear()
            from src import gepa_rag_adapter
            gepa_rag_adapter._chroma_client = None
            st.rerun()
        
        try:
            vector_store, rag_system = initialize_system(_key=get_system_key())
            info = vector_store.get_collection_info()
            st.metric("Documents Indexed", info["document_count"])
            st.metric("Embedding Dim", info["dimension"])
            st.success("✅ System Ready")
        except Exception as e:
            st.error(f"System not initialized: {e}")
            st.info("Run: python main.py --index")
            if st.button("🔄 Retry"):
                st.cache_resource.clear()
                st.rerun()
            return
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 Ask Questions")
        
        # Example queries
        example_queries = [
            "What is the EDC metrics data for Study 1?",
            "Show safety adverse events from eSAE dashboards",
            "What MedDRA coding information is available?",
            "Compare data quality across different studies",
            "What laboratory tests have missing reference ranges?",
            "Show visit tracking and completion status"
        ]
        
        # Quick select
        selected_example = st.selectbox(
            "📝 Quick Examples",
            ["Type your own question..."] + example_queries
        )
        
        # Query input
        if selected_example == "Type your own question...":
            query = st.text_area(
                "Your Question",
                placeholder="Ask anything about the clinical trial data...",
                height=100
            )
        else:
            query = st.text_area(
                "Your Question",
                value=selected_example,
                height=100
            )
        
        # Build filters
        filters = {}
        if selected_study != "All Studies":
            filters["study_id"] = selected_study
        if selected_report != "All Types":
            filters["report_type"] = selected_report
        
        # Search button
        if st.button("🔎 Search", type="primary", use_container_width=True):
            if query:
                with st.spinner("Searching and generating answer..."):
                    try:
                        result = rag_system.query(
                            question=query,
                            top_k=top_k,
                            filters=filters if filters else None
                        )
                        
                        # Store result in session state
                        st.session_state["last_result"] = result
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter a question")
    
    with col2:
        st.header("📚 Report Types")
        for rt, info in list(CLINICAL_DATA_SCHEMA["report_types"].items())[:5]:
            with st.expander(f"📄 {rt}"):
                st.write(info["description"])
                st.caption(f"Key fields: {', '.join(info['key_fields'])}")
    
    # Results section
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        
        st.markdown("---")
        st.header("📝 Answer")
        
        # Answer box
        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #4CAF50; padding: 20px; border-radius: 5px;">
        {result["answer"]}
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sources Used", result["num_sources"])
        with col2:
            if result["sources"]:
                avg_score = sum(s["relevance_score"] for s in result["sources"]) / len(result["sources"])
                st.metric("Avg Relevance", f"{avg_score:.3f}")
        with col3:
            st.metric("Query Reformulated", "Yes" if result.get("reformulated_query") != result["question"] else "No")
        
        # Sources
        st.subheader("📚 Sources")
        
        for i, source in enumerate(result["sources"], 1):
            with st.expander(f"Source {i}: {source['metadata'].get('filename', 'Unknown')} (Score: {source['relevance_score']:.3f})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Study:** {source['metadata'].get('study_id', 'N/A')}")
                    st.write(f"**Report Type:** {source['metadata'].get('report_type', 'N/A')}")
                with col2:
                    st.write(f"**Sheet:** {source['metadata'].get('sheet_name', 'N/A')}")
                    st.write(f"**Relevance:** {source['relevance_score']:.4f}")
                
                st.text_area(
                    "Content Preview",
                    source["content"],
                    height=150,
                    key=f"source_{i}"
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888;">
        <small>
        GEPA-Optimized RAG System | Using Free Local Models via Ollama<br>
        Built for NEST 2.0 Clinical Trial Data Analysis
        </small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

"""
GEPA RAG System - Clinical Data Loaders
=======================================
Handles loading and parsing of Excel files containing clinical study data.
Optimized for NEST 2.0 anonymized clinical trial data.
"""

import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from tqdm import tqdm
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document chunk with content and metadata."""
    content: str
    metadata: Dict[str, Any]
    doc_id: str


class ClinicalDataLoader:
    """
    Loads clinical study data from Excel files.
    Optimized for NEST 2.0 data structure.
    """
    
    REPORT_TYPE_PATTERNS = {
        "EDRR": ["Compiled_EDRR", "EDRR"],
        "EDC_Metrics": ["EDC_Metrics", "EDC Metrics"],
        "eSAE": ["eSAE", "Safety_Report", "Safety Report"],
        "MedDRA_Coding": ["MedDRA", "GlobalCodingReport_MedDRA"],
        "WHODD_Coding": ["WHODD", "GlobalCodingReport_WHODD"],
        "Missing_Pages": ["Missing_Pages", "Missing Pages"],
        "Lab_Ranges": ["Missing_Lab_Name", "Lab_Name", "Missing_Ranges"],
        "Inactivated_Forms": ["Inactivated", "Inactivated Forms"],
        "Visit_Tracker": ["Visit_Projection", "Visit Projection", "Tracker"]
    }
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.documents: List[Document] = []
        
    def identify_report_type(self, filename: str) -> str:
        """Identify the report type from filename."""
        for report_type, patterns in self.REPORT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in filename.lower():
                    return report_type
        return "Unknown"
    
    def extract_study_id(self, filepath: Path) -> str:
        """Extract study ID from folder or file name."""
        # Try to get from parent folder
        parent_name = filepath.parent.name
        if "Study" in parent_name or "STUDY" in parent_name:
            # Extract study number
            parts = parent_name.split("_")
            for part in parts:
                if "Study" in part or "STUDY" in part:
                    return part.replace("Study", "Study_").replace("STUDY", "Study_").strip()
        
        # Try to get from filename
        filename = filepath.stem
        parts = filename.split("_")
        for i, part in enumerate(parts):
            if "Study" in part or "STUDY" in part:
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    return f"Study_{parts[i+1]}"
                return part
        
        return "Unknown_Study"
    
    def load_excel_file(self, filepath: Path, max_rows: int = 10000) -> List[Document]:
        """Load a single Excel file and convert to documents.
        
        Args:
            filepath: Path to Excel file
            max_rows: Maximum rows to read per sheet (prevents memory issues)
        """
        documents = []
        
        try:
            # Read all sheets with row limit
            excel_file = pd.ExcelFile(filepath)
            sheet_names = excel_file.sheet_names
            
            study_id = self.extract_study_id(filepath)
            report_type = self.identify_report_type(filepath.name)
            
            for sheet_name in sheet_names:
                try:
                    # Read with row limit to prevent memory issues
                    df = pd.read_excel(filepath, sheet_name=sheet_name, nrows=max_rows)
                    
                    if df.empty:
                        continue
                    
                    # Clean column names
                    df.columns = [str(col).strip() for col in df.columns]
                    
                    # Create document content
                    content = self._dataframe_to_text(df, filepath.name, sheet_name)
                    
                    # Create metadata
                    metadata = {
                        "source": str(filepath),
                        "filename": filepath.name,
                        "study_id": study_id,
                        "report_type": report_type,
                        "sheet_name": sheet_name,
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "columns": list(df.columns)
                    }
                    
                    doc_id = f"{study_id}_{report_type}_{sheet_name}".replace(" ", "_")
                    
                    doc = Document(
                        content=content,
                        metadata=metadata,
                        doc_id=doc_id
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    logger.warning(f"Error reading sheet {sheet_name} from {filepath}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading Excel file {filepath}: {e}")
            
        return documents
    
    def _dataframe_to_text(self, df: pd.DataFrame, filename: str, sheet_name: str) -> str:
        """Convert DataFrame to structured text for embedding."""
        lines = []
        
        # Header information
        lines.append(f"Report: {filename}")
        lines.append(f"Sheet: {sheet_name}")
        lines.append(f"Total Records: {len(df)}")
        lines.append(f"Columns: {', '.join(df.columns)}")
        lines.append("")
        
        # Summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            lines.append("=== Numeric Summary ===")
            for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
                try:
                    lines.append(f"{col}: Min={df[col].min():.2f}, Max={df[col].max():.2f}, Mean={df[col].mean():.2f}")
                except:
                    pass
            lines.append("")
        
        # Sample data rows
        lines.append("=== Sample Data ===")
        sample_df = df.head(20)  # First 20 rows as sample
        for idx, row in sample_df.iterrows():
            row_text = " | ".join([f"{col}: {str(val)[:50]}" for col, val in row.items() if pd.notna(val)])
            lines.append(row_text)
        
        # Unique value counts for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            lines.append("")
            lines.append("=== Categorical Value Counts ===")
            for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
                try:
                    value_counts = df[col].value_counts().head(10)
                    lines.append(f"{col}: {dict(value_counts)}")
                except:
                    pass
        
        return "\n".join(lines)
    
    def load_all_data(self, limit: Optional[int] = None) -> List[Document]:
        """Load all Excel files from the data directory.
        
        Args:
            limit: Max number of files to process (for testing)
        """
        self.documents = []
        
        # Find all Excel files
        excel_files = list(self.data_dir.rglob("*.xlsx"))
        
        if limit:
            excel_files = excel_files[:limit]
            logger.info(f"Processing {len(excel_files)} Excel files (limited from total)")
        else:
            logger.info(f"Found {len(excel_files)} Excel files to process")
        
        for filepath in tqdm(excel_files, desc="Loading clinical data"):
            docs = self.load_excel_file(filepath)
            self.documents.extend(docs)
            
        logger.info(f"Loaded {len(self.documents)} document chunks")
        return self.documents
    
    def get_documents_by_study(self, study_id: str) -> List[Document]:
        """Get all documents for a specific study."""
        return [doc for doc in self.documents if doc.metadata.get("study_id") == study_id]
    
    def get_documents_by_report_type(self, report_type: str) -> List[Document]:
        """Get all documents of a specific report type."""
        return [doc for doc in self.documents if doc.metadata.get("report_type") == report_type]
    
    def get_study_summary(self) -> Dict[str, Any]:
        """Get summary statistics of loaded data."""
        studies = set()
        report_types = {}
        
        for doc in self.documents:
            studies.add(doc.metadata.get("study_id", "Unknown"))
            rt = doc.metadata.get("report_type", "Unknown")
            report_types[rt] = report_types.get(rt, 0) + 1
            
        return {
            "total_documents": len(self.documents),
            "unique_studies": len(studies),
            "studies": sorted(list(studies)),
            "report_type_counts": report_types
        }


class DocumentChunker:
    """
    Chunks documents for optimal embedding and retrieval.
    Part of GEPA's Embedding optimization (E).
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def chunk_document(self, doc: Document) -> List[Document]:
        """Split a document into smaller chunks while preserving context."""
        content = doc.content
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split("\n\n")
        
        current_chunk = ""
        chunk_idx = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunk_doc = Document(
                        content=current_chunk.strip(),
                        metadata={**doc.metadata, "chunk_index": chunk_idx},
                        doc_id=f"{doc.doc_id}_chunk_{chunk_idx}"
                    )
                    chunks.append(chunk_doc)
                    chunk_idx += 1
                    
                    # Include overlap
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_doc = Document(
                content=current_chunk.strip(),
                metadata={**doc.metadata, "chunk_index": chunk_idx},
                doc_id=f"{doc.doc_id}_chunk_{chunk_idx}"
            )
            chunks.append(chunk_doc)
            
        return chunks
    
    def chunk_all_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk all documents."""
        all_chunks = []
        for doc in tqdm(documents, desc="Chunking documents"):
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks

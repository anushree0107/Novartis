"""
Preprocessing Module for NEXUS Text-to-SQL System

This module handles:
1. LSH (Locality Sensitive Hashing) indexing for database values - for entity retrieval
2. Vector database for schema descriptions - for context retrieval
"""
import os
import json
import pickle
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
import re

from config.settings import DATABASE_CONFIG


@dataclass
class ValueIndex:
    """Indexed database value with metadata"""
    value: str
    table_name: str
    column_name: str
    data_type: str
    

class MinHashLSH:
    """
    Locality Sensitive Hashing using MinHash for approximate string matching.
    Used for fast entity retrieval from database values.
    """
    
    def __init__(self, num_perm: int = 128, threshold: float = 0.5):
        """
        Args:
            num_perm: Number of permutations for MinHash
            threshold: Similarity threshold for LSH
        """
        self.num_perm = num_perm
        self.threshold = threshold
        self.hash_tables: Dict[int, Dict[int, Set[int]]] = {}
        self.values: List[ValueIndex] = []
        
        # Calculate number of bands and rows for LSH
        # b * r = num_perm, threshold ≈ (1/b)^(1/r)
        self.num_bands = 32
        self.rows_per_band = num_perm // self.num_bands
        
        # Generate random hash coefficients
        import random
        random.seed(42)
        self.a_coeffs = [random.randint(1, 2**31 - 1) for _ in range(num_perm)]
        self.b_coeffs = [random.randint(0, 2**31 - 1) for _ in range(num_perm)]
        self.prime = 2**31 - 1
    
    def _get_shingles(self, text: str, k: int = 3) -> Set[str]:
        """Get k-shingles (character n-grams) from text"""
        text = text.lower().strip()
        if len(text) < k:
            return {text}
        return {text[i:i+k] for i in range(len(text) - k + 1)}
    
    def _minhash(self, shingles: Set[str]) -> List[int]:
        """Compute MinHash signature for a set of shingles"""
        signature = [float('inf')] * self.num_perm
        
        for shingle in shingles:
            # Hash the shingle
            h = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
            
            # Update signature with min hash for each permutation
            for i in range(self.num_perm):
                hash_val = (self.a_coeffs[i] * h + self.b_coeffs[i]) % self.prime
                signature[i] = min(signature[i], hash_val)
        
        return [int(x) if x != float('inf') else 0 for x in signature]
    
    def _get_band_hashes(self, signature: List[int]) -> List[int]:
        """Get hash for each band of the signature"""
        band_hashes = []
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            end = start + self.rows_per_band
            band = tuple(signature[start:end])
            band_hashes.append(hash(band))
        return band_hashes
    
    def add(self, value_index: ValueIndex):
        """Add a value to the LSH index"""
        idx = len(self.values)
        self.values.append(value_index)
        
        # Compute MinHash signature
        shingles = self._get_shingles(value_index.value)
        signature = self._minhash(shingles)
        band_hashes = self._get_band_hashes(signature)
        
        # Add to hash tables
        for band_idx, band_hash in enumerate(band_hashes):
            if band_idx not in self.hash_tables:
                self.hash_tables[band_idx] = {}
            if band_hash not in self.hash_tables[band_idx]:
                self.hash_tables[band_idx][band_hash] = set()
            self.hash_tables[band_idx][band_hash].add(idx)
    
    def query(self, text: str, top_k: int = 10) -> List[Tuple[ValueIndex, float]]:
        """
        Query for similar values using LSH
        
        Args:
            text: Query text
            top_k: Number of results to return
            
        Returns:
            List of (ValueIndex, similarity_score) tuples
        """
        # Compute query signature
        shingles = self._get_shingles(text)
        signature = self._minhash(shingles)
        band_hashes = self._get_band_hashes(signature)
        
        # Find candidate matches from hash tables
        candidates = set()
        for band_idx, band_hash in enumerate(band_hashes):
            candidates.update(self.hash_tables[band_idx].get(band_hash, set()))
        
        # Compute actual similarity for candidates
        results = []
        for idx in candidates:
            value_idx = self.values[idx]
            similarity = self._compute_similarity(text, value_idx.value)
            if similarity >= self.threshold * 0.5:  # Lower threshold for candidates
                results.append((value_idx, similarity))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts"""
        shingles1 = self._get_shingles(text1)
        shingles2 = self._get_shingles(text2)
        
        if not shingles1 or not shingles2:
            return 0.0
        
        intersection = len(shingles1 & shingles2)
        union = len(shingles1 | shingles2)
        
        return intersection / union if union > 0 else 0.0


def edit_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings"""
    s1, s2 = s1.lower(), s2.lower()
    
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    
    if len(s2) == 0:
        return len(s1)
    
    prev_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    
    return prev_row[-1]


def edit_distance_similarity(s1: str, s2: str) -> float:
    """Compute edit distance similarity (0-1 scale)"""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    return 1 - (edit_distance(s1, s2) / max_len)


class VectorStore:
    """
    Simple vector store for semantic similarity search.
    Uses sentence embeddings for schema descriptions.
    """
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self._embedder = None
    
    def _get_embedder(self):
        """Lazy load embedder"""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                # Fallback to simple TF-IDF based approach
                self._embedder = 'tfidf'
        return self._embedder
    
    def _compute_embedding(self, text: str) -> List[float]:
        """Compute embedding for text"""
        embedder = self._get_embedder()
        
        if embedder == 'tfidf':
            # Simple bag of words fallback
            return self._simple_embedding(text)
        else:
            return embedder.encode(text).tolist()
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple embedding using character and word features"""
        text = text.lower()
        words = set(re.findall(r'\w+', text))
        
        # Create a simple feature vector
        features = []
        
        # Word length distribution
        lengths = [len(w) for w in words]
        features.extend([
            sum(lengths) / len(lengths) if lengths else 0,  # avg length
            max(lengths) if lengths else 0,  # max length
            len(words),  # word count
        ])
        
        # Character frequency features (26 letters)
        char_counts = [text.count(chr(i)) for i in range(ord('a'), ord('z') + 1)]
        total = sum(char_counts) or 1
        features.extend([c / total for c in char_counts])
        
        # Common clinical terms presence
        clinical_terms = ['patient', 'subject', 'site', 'visit', 'query', 'status', 
                         'date', 'count', 'id', 'name', 'type', 'code', 'value']
        features.extend([1.0 if term in text else 0.0 for term in clinical_terms])
        
        return features
    
    def add(self, document: Dict[str, Any], text: str):
        """Add a document with its text to the store"""
        self.documents.append(document)
        self.embeddings.append(self._compute_embedding(text))
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar documents"""
        if not self.documents:
            return []
        
        query_embedding = self._compute_embedding(query)
        
        # Compute similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((self.documents[i], sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if len(v1) != len(v2):
            # Pad shorter vector
            max_len = max(len(v1), len(v2))
            v1 = v1 + [0] * (max_len - len(v1))
            v2 = v2 + [0] * (max_len - len(v2))
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class DatabasePreprocessor:
    """
    Main preprocessing class that builds:
    1. LSH index for database values
    2. Vector store for schema descriptions
    """
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or "cache/preprocessing")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.lsh_index = MinHashLSH(num_perm=128, threshold=0.3)
        self.vector_store = VectorStore()
        self.schema_descriptions: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            'total_values_indexed': 0,
            'total_descriptions': 0,
            'tables_processed': 0
        }
    
    def build_value_index(self, db_manager, sample_limit: int = 1000):
        """
        Build LSH index from database values
        
        Args:
            db_manager: DatabaseManager instance
            sample_limit: Max unique values to index per column
        """
        from rich.progress import Progress
        from rich.console import Console
        
        console = Console()
        tables = db_manager.get_all_tables()
        
        console.print(f"\n[bold blue]Building LSH index for {len(tables)} tables...[/bold blue]")
        
        with Progress() as progress:
            task = progress.add_task("Indexing values...", total=len(tables))
            
            for table_name in tables:
                if table_name.startswith('_'):
                    progress.advance(task)
                    continue
                
                columns = db_manager.get_table_columns(table_name)
                
                for col_info in columns:
                    col_name = col_info['column_name']
                    data_type = col_info['data_type']
                    
                    # Skip non-text columns and metadata columns
                    if data_type not in ('text', 'character varying', 'varchar', 'char'):
                        continue
                    if col_name.startswith('_'):
                        continue
                    
                    # Get unique values
                    try:
                        query = f"""
                            SELECT DISTINCT {col_name} 
                            FROM {table_name} 
                            WHERE {col_name} IS NOT NULL 
                            AND {col_name} != ''
                            LIMIT {sample_limit}
                        """
                        result = db_manager.execute_query(query)
                        
                        for row in result:
                            value = str(row[col_name])
                            if value and len(value) > 1 and len(value) < 200:
                                value_index = ValueIndex(
                                    value=value,
                                    table_name=table_name,
                                    column_name=col_name,
                                    data_type=data_type
                                )
                                self.lsh_index.add(value_index)
                                self.stats['total_values_indexed'] += 1
                    except Exception as e:
                        pass  # Skip problematic columns
                
                self.stats['tables_processed'] += 1
                progress.advance(task)
        
        console.print(f"[green]Indexed {self.stats['total_values_indexed']} unique values[/green]")
    
    def build_description_index(self, db_manager, schema_manager=None):
        """
        Build vector store from schema descriptions
        
        Args:
            db_manager: DatabaseManager instance
            schema_manager: Optional SchemaManager for additional metadata
        """
        from rich.console import Console
        console = Console()
        
        console.print("\n[bold blue]Building vector store for schema descriptions...[/bold blue]")
        
        tables = db_manager.get_all_tables()
        
        for table_name in tables:
            if table_name.startswith('_'):
                continue
            
            columns = db_manager.get_table_columns(table_name)
            
            # Build table description
            col_descriptions = []
            for col in columns:
                col_name = col['column_name']
                data_type = col['data_type']
                
                # Create description from column name
                readable_name = col_name.replace('_', ' ').title()
                description = f"{readable_name} ({data_type})"
                col_descriptions.append(description)
                
                # Add individual column to vector store
                doc = {
                    'type': 'column',
                    'table': table_name,
                    'column': col_name,
                    'data_type': data_type
                }
                text = f"{table_name} {col_name} {readable_name}"
                self.vector_store.add(doc, text)
            
            # Add table description
            table_description = f"Table {table_name} contains: {', '.join(col_descriptions[:10])}"
            if len(col_descriptions) > 10:
                table_description += f" and {len(col_descriptions) - 10} more columns"
            
            self.schema_descriptions[table_name] = table_description
            
            doc = {
                'type': 'table',
                'table': table_name,
                'column_count': len(columns)
            }
            self.vector_store.add(doc, table_description)
            self.stats['total_descriptions'] += 1
        
        console.print(f"[green]Indexed {self.stats['total_descriptions']} schema descriptions[/green]")
    
    def preprocess(self, db_manager, schema_manager=None):
        """Run full preprocessing pipeline"""
        self.build_value_index(db_manager)
        self.build_description_index(db_manager, schema_manager)
        self.save_cache()
        return self.stats
    
    def save_cache(self):
        """Save preprocessed data to cache"""
        cache_file = self.cache_dir / "preprocess_cache.pkl"
        
        data = {
            'lsh_index': self.lsh_index,
            'vector_store': self.vector_store,
            'schema_descriptions': self.schema_descriptions,
            'stats': self.stats
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Cache saved to {cache_file}")
    
    def load_cache(self) -> bool:
        """Load preprocessed data from cache"""
        cache_file = self.cache_dir / "preprocess_cache.pkl"
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            self.lsh_index = data['lsh_index']
            self.vector_store = data['vector_store']
            self.schema_descriptions = data['schema_descriptions']
            self.stats = data['stats']
            
            print(f"Cache loaded: {self.stats['total_values_indexed']} values, "
                  f"{self.stats['total_descriptions']} descriptions")
            return True
        except Exception as e:
            print(f"Failed to load cache: {e}")
            return False
    
    def retrieve_entities(self, keyword: str, top_k: int = 10) -> List[Dict]:
        """
        Retrieve entities matching a keyword using LSH + edit distance
        
        Args:
            keyword: Keyword to search for
            top_k: Number of results
            
        Returns:
            List of matching entities with metadata
        """
        # Get LSH candidates
        lsh_results = self.lsh_index.query(keyword, top_k=top_k * 2)
        
        # Re-rank by edit distance similarity
        results = []
        for value_idx, lsh_sim in lsh_results:
            edit_sim = edit_distance_similarity(keyword, value_idx.value)
            combined_score = (lsh_sim + edit_sim) / 2
            
            results.append({
                'value': value_idx.value,
                'table': value_idx.table_name,
                'column': value_idx.column_name,
                'similarity': combined_score
            })
        
        # Sort by combined score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant schema context using vector similarity
        
        Args:
            query: Natural language query
            top_k: Number of results
            
        Returns:
            List of relevant schema descriptions
        """
        results = self.vector_store.search(query, top_k=top_k)
        
        return [
            {
                'type': doc['type'],
                'table': doc['table'],
                'column': doc.get('column'),
                'similarity': sim,
                'description': self.schema_descriptions.get(doc['table'], '')
            }
            for doc, sim in results
        ]


# Singleton instance
preprocessor = DatabasePreprocessor()

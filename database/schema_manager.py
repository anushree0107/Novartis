"""
Schema Manager - Extracts and manages database schema information
with token optimization for efficient context building
"""
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import tiktoken

from database.connection import DatabaseManager, db_manager
from config.settings import TOKEN_LIMITS, SCHEMA_CACHE_PATH


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    data_type: str
    is_nullable: bool
    sample_values: List[Any] = None
    description: str = ""
    
    def to_compact_str(self) -> str:
        """Compact string representation for token optimization"""
        nullable = "NULL" if self.is_nullable else "NOT NULL"
        return f"{self.name} ({self.data_type}, {nullable})"
    
    def to_detailed_str(self) -> str:
        """Detailed string with sample values"""
        base = self.to_compact_str()
        if self.sample_values:
            samples = [str(v)[:30] for v in self.sample_values[:3]]
            base += f" -- e.g., {', '.join(samples)}"
        return base


@dataclass  
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[ColumnInfo]
    row_count: int = 0
    primary_keys: List[str] = None
    foreign_keys: List[Dict] = None
    category: str = ""
    study_number: str = ""
    description: str = ""
    
    def get_column_names(self) -> List[str]:
        return [col.name for col in self.columns]
    
    def to_ddl(self, include_samples: bool = False) -> str:
        """Generate DDL-like representation"""
        lines = [f"CREATE TABLE {self.name} ("]
        
        for col in self.columns:
            if include_samples:
                lines.append(f"    {col.to_detailed_str()},")
            else:
                lines.append(f"    {col.to_compact_str()},")
        
        # Add primary key if exists
        if self.primary_keys:
            lines.append(f"    PRIMARY KEY ({', '.join(self.primary_keys)})")
        
        lines[-1] = lines[-1].rstrip(',')
        lines.append(");")
        
        if self.row_count:
            lines.append(f"-- {self.row_count} rows")
            
        return "\n".join(lines)
    
    def to_compact(self) -> str:
        """Very compact representation for token optimization"""
        cols = ", ".join([f"{c.name}:{c.data_type[:10]}" for c in self.columns])
        return f"{self.name}[{cols}]"


class SchemaManager:
    """Manages database schema extraction and caching with token optimization"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or db_manager
        self.tables: Dict[str, TableInfo] = {}
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self._load_cache()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def _load_cache(self):
        """Load schema from cache if available"""
        cache_path = Path(SCHEMA_CACHE_PATH)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    for table_name, table_data in data.items():
                        columns = [ColumnInfo(**col) for col in table_data['columns']]
                        self.tables[table_name] = TableInfo(
                            name=table_data['name'],
                            columns=columns,
                            row_count=table_data.get('row_count', 0),
                            primary_keys=table_data.get('primary_keys'),
                            foreign_keys=table_data.get('foreign_keys'),
                            category=table_data.get('category', ''),
                            study_number=table_data.get('study_number', ''),
                            description=table_data.get('description', '')
                        )
            except Exception as e:
                print(f"Warning: Could not load schema cache: {e}")
    
    def _save_cache(self):
        """Save schema to cache"""
        cache_path = Path(SCHEMA_CACHE_PATH)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for table_name, table_info in self.tables.items():
            data[table_name] = {
                'name': table_info.name,
                'columns': [asdict(col) for col in table_info.columns],
                'row_count': table_info.row_count,
                'primary_keys': table_info.primary_keys,
                'foreign_keys': table_info.foreign_keys,
                'category': table_info.category,
                'study_number': table_info.study_number,
                'description': table_info.description
            }
        
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def refresh_schema(self, include_samples: bool = True):
        """Refresh schema information from database"""
        self.tables = {}
        
        table_names = self.db.get_all_tables()
        
        for table_name in table_names:
            # Handle metadata tables specially
            if table_name.startswith('_'):
                self._add_metadata_table(table_name)
                continue
                
            columns_data = self.db.get_table_columns(table_name)
            
            # Get sample values if requested
            samples = {}
            if include_samples:
                try:
                    sample_rows = self.db.get_table_sample(table_name, limit=5)
                    for col in columns_data:
                        col_name = col['column_name']
                        samples[col_name] = list(set(
                            row.get(col_name) for row in sample_rows 
                            if row.get(col_name) is not None
                        ))[:3]
                except:
                    pass
            
            columns = [
                ColumnInfo(
                    name=col['column_name'],
                    data_type=col['data_type'],
                    is_nullable=col['is_nullable'] == 'YES',
                    sample_values=samples.get(col['column_name'], [])
                )
                for col in columns_data
            ]
            
            # Extract metadata from column values if present
            category = ""
            study_number = ""
            try:
                meta_sample = self.db.get_table_sample(table_name, limit=1)
                if meta_sample:
                    category = meta_sample[0].get('_category', '')
                    study_number = meta_sample[0].get('_study_number', '')
            except:
                pass
            
            self.tables[table_name] = TableInfo(
                name=table_name,
                columns=columns,
                row_count=self.db.get_table_row_count(table_name),
                primary_keys=self.db.get_primary_keys(table_name),
                foreign_keys=self.db.get_foreign_keys(table_name),
                category=category,
                study_number=study_number
            )
        
        self._save_cache()
        return len(self.tables)
    
    def _add_metadata_table(self, table_name: str):
        """Add metadata/system tables with proper descriptions"""
        # Define descriptions for known metadata tables
        metadata_descriptions = {
            '_table_metadata': 'System table containing metadata about all loaded tables including study number, category, row count, and column list. Use this to query information ABOUT the database structure.',
            '_studies': 'Summary table of all clinical studies in the database. Contains study_number, table_count, and total_rows for each study. USE THIS TABLE to answer questions about how many studies exist or study-level statistics.'
        }
        
        columns_data = self.db.get_table_columns(table_name)
        columns = [
            ColumnInfo(
                name=col['column_name'],
                data_type=col['data_type'],
                is_nullable=col['is_nullable'] == 'YES',
                sample_values=[]
            )
            for col in columns_data
        ]
        
        self.tables[table_name] = TableInfo(
            name=table_name,
            columns=columns,
            row_count=self.db.get_table_row_count(table_name),
            category='metadata',
            description=metadata_descriptions.get(table_name, 'System metadata table')
        )
    
    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """Get information for a specific table"""
        return self.tables.get(table_name)
    
    def get_all_tables(self) -> List[str]:
        """Get all table names"""
        return list(self.tables.keys())
    
    def get_tables_by_category(self, category: str) -> List[TableInfo]:
        """Get tables filtered by category"""
        return [t for t in self.tables.values() if t.category == category]
    
    def get_tables_by_study(self, study_number: str) -> List[TableInfo]:
        """Get tables for a specific study"""
        return [t for t in self.tables.values() if t.study_number == study_number]
    
    def search_columns(self, search_term: str) -> List[Dict]:
        """Search for columns by name across all tables"""
        results = []
        search_lower = search_term.lower()
        
        for table_name, table_info in self.tables.items():
            for col in table_info.columns:
                if search_lower in col.name.lower():
                    results.append({
                        'table': table_name,
                        'column': col.name,
                        'data_type': col.data_type,
                        'category': table_info.category
                    })
        
        return results
    
    def get_schema_summary(self) -> str:
        """Get a compact summary of all tables"""
        lines = ["DATABASE SCHEMA SUMMARY:", "=" * 50]
        
        # Group by category
        categories = {}
        for table_info in self.tables.values():
            cat = table_info.category or 'other'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(table_info)
        
        for category, tables in sorted(categories.items()):
            lines.append(f"\n[{category.upper()}] - {len(tables)} tables")
            for table in tables[:5]:  # Limit per category
                cols_preview = ", ".join([c.name for c in table.columns[:5]])
                if len(table.columns) > 5:
                    cols_preview += f" ... (+{len(table.columns) - 5} more)"
                lines.append(f"  • {table.name}: {cols_preview}")
            if len(tables) > 5:
                lines.append(f"  ... and {len(tables) - 5} more tables")
        
        return "\n".join(lines)
    
    def get_optimized_schema_context(
        self, 
        relevant_tables: List[str] = None,
        max_tokens: int = None,
        detail_level: str = "medium"  # "compact", "medium", "detailed"
    ) -> str:
        """
        Get schema context optimized for token budget
        
        Token Optimization Strategy (CHESS-inspired):
        1. Prioritize relevant tables
        2. Use compact representations for less relevant tables
        3. Include sample values only for key columns
        4. Truncate when approaching token limit
        """
        max_tokens = max_tokens or TOKEN_LIMITS['max_schema_tokens']
        
        if relevant_tables is None:
            relevant_tables = list(self.tables.keys())
        
        context_parts = []
        current_tokens = 0
        
        # Header
        header = "-- DATABASE SCHEMA --\n"
        context_parts.append(header)
        current_tokens += self.count_tokens(header)
        
        # Add relevant tables with appropriate detail level
        for table_name in relevant_tables:
            table_info = self.tables.get(table_name)
            if not table_info:
                continue
            
            # Choose representation based on detail level
            if detail_level == "detailed":
                table_str = table_info.to_ddl(include_samples=True)
            elif detail_level == "medium":
                table_str = table_info.to_ddl(include_samples=False)
            else:  # compact
                table_str = table_info.to_compact()
            
            table_tokens = self.count_tokens(table_str)
            
            # Check if we can fit this table
            if current_tokens + table_tokens > max_tokens:
                # Try compact version
                compact_str = table_info.to_compact()
                compact_tokens = self.count_tokens(compact_str)
                
                if current_tokens + compact_tokens <= max_tokens:
                    context_parts.append(compact_str)
                    current_tokens += compact_tokens
                else:
                    # Add truncation notice and stop
                    context_parts.append(f"\n-- Schema truncated. {len(relevant_tables) - len(context_parts) + 1} tables omitted --")
                    break
            else:
                context_parts.append(table_str)
                current_tokens += table_tokens
        
        return "\n\n".join(context_parts)
    
    def get_table_relationships(self) -> List[Dict]:
        """Infer relationships between tables based on column names"""
        relationships = []
        
        # Common linking columns in clinical data
        link_columns = ['subject_id', 'site_id', 'study_number', 'patient_id', 'visit_id']
        
        for table_name, table_info in self.tables.items():
            table_cols = set(c.name.lower() for c in table_info.columns)
            
            for other_table, other_info in self.tables.items():
                if table_name == other_table:
                    continue
                    
                other_cols = set(c.name.lower() for c in other_info.columns)
                
                # Find common columns
                common = table_cols.intersection(other_cols)
                link_cols = common.intersection(set(link_columns))
                
                if link_cols:
                    relationships.append({
                        'table1': table_name,
                        'table2': other_table,
                        'link_columns': list(link_cols)
                    })
        
        return relationships


# Singleton instance
schema_manager = SchemaManager()

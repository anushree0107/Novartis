"""
Schema Context Builder for CHASE-SQL.

Parses database schema and builds rich context for LLM understanding.
Extracts table definitions, column information, foreign keys, and sample data.
"""
import re
import sqlparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import logging

from .config import default_config
from .database import DatabaseConnection, get_database

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    fk_reference: Optional[str] = None  # e.g., "studies(study_id)"
    is_nullable: bool = True
    default_value: Optional[str] = None
    description: Optional[str] = None
    enum_values: Optional[List[str]] = None


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_key: Optional[str] = None
    description: Optional[str] = None
    sample_data: Optional[List[Dict[str, Any]]] = None
    
    def get_column(self, name: str) -> Optional[ColumnInfo]:
        """Get column by name"""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None
    
    def to_ddl(self, include_sample: bool = True) -> str:
        """Generate DDL-style representation for the LLM"""
        lines = [f"-- Table: {self.name}"]
        if self.description:
            lines.append(f"-- Description: {self.description}")
        
        lines.append(f"CREATE TABLE {self.name} (")
        col_lines = []
        for col in self.columns:
            col_def = f"    {col.name} {col.data_type}"
            annotations = []
            if col.is_primary_key:
                annotations.append("PK")
            if col.is_foreign_key and col.fk_reference:
                annotations.append(f"FK→{col.fk_reference}")
            if col.enum_values:
                annotations.append(f"ENUM: {', '.join(col.enum_values[:5])}")
            if annotations:
                col_def += f"  -- {', '.join(annotations)}"
            col_lines.append(col_def)
        lines.append(",\n".join(col_lines))
        lines.append(");")
        
        if include_sample and self.sample_data:
            lines.append(f"\n-- Sample data (first {len(self.sample_data)} rows):")
            for row in self.sample_data[:3]:
                row_str = ", ".join(f"{k}={repr(v)}" for k, v in list(row.items())[:5])
                lines.append(f"--   {row_str}")
        
        return "\n".join(lines)


@dataclass
class SchemaContext:
    """Complete schema context for LLM"""
    tables: Dict[str, TableInfo] = field(default_factory=dict)
    enum_types: Dict[str, List[str]] = field(default_factory=dict)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    views: Dict[str, str] = field(default_factory=dict)
    
    def get_table(self, name: str) -> Optional[TableInfo]:
        """Get table by name (case-insensitive)"""
        return self.tables.get(name.lower())
    
    def get_related_tables(self, table_name: str) -> Set[str]:
        """Get tables related via foreign keys"""
        related = set()
        for fk in self.foreign_keys:
            if fk['source_table'].lower() == table_name.lower():
                related.add(fk['target_table'])
            if fk['target_table'].lower() == table_name.lower():
                related.add(fk['source_table'])
        return related
    
    def to_prompt_context(
        self, 
        tables: Optional[List[str]] = None,
        include_samples: bool = True,
        max_tables: int = 15
    ) -> str:
        """
        Generate schema context string for LLM prompt.
        
        Args:
            tables: Specific tables to include (None = all)
            include_samples: Whether to include sample data
            max_tables: Maximum number of tables to include
        """
        if tables:
            selected = [self.tables[t.lower()] for t in tables if t.lower() in self.tables]
        else:
            # Prioritize core tables
            core_tables = ['studies', 'sites', 'subjects', 'visits', 'data_queries']
            selected = [self.tables[t] for t in core_tables if t in self.tables]
            # Add remaining tables up to limit
            for t in self.tables.values():
                if t.name not in core_tables and len(selected) < max_tables:
                    selected.append(t)
        
        lines = ["## Clinical Trials Database Schema\n"]
        
        # Add enum types
        if self.enum_types:
            lines.append("### Status/Type Enumerations:")
            for enum_name, values in list(self.enum_types.items())[:10]:
                lines.append(f"- {enum_name}: {', '.join(values)}")
            lines.append("")
        
        # Add table definitions
        lines.append("### Tables:\n")
        for table in selected[:max_tables]:
            lines.append(table.to_ddl(include_sample=include_samples))
            lines.append("")
        
        # Add key relationships
        lines.append("\n### Key Relationships:")
        for fk in self.foreign_keys[:20]:
            lines.append(f"- {fk['source_table']}.{fk['source_column']} → {fk['target_table']}.{fk['target_column']}")
        
        return "\n".join(lines)


class SchemaContextBuilder:
    """
    Builds rich schema context from SQL files or live database.
    
    Implements the schema understanding component of CHASE-SQL.
    """
    
    def __init__(self, schema_path: Optional[str] = None, db: Optional[DatabaseConnection] = None):
        self.schema_path = Path(schema_path) if schema_path else Path(default_config.schema_path)
        self.db = db
        self._context: Optional[SchemaContext] = None
    
    def build_from_file(self) -> SchemaContext:
        """Parse schema from SQL file"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        sql_content = self.schema_path.read_text()
        return self._parse_schema_sql(sql_content)
    
    def build_from_database(self) -> SchemaContext:
        """Build schema context from live database connection"""
        if self.db is None:
            self.db = get_database()
        
        context = SchemaContext()
        
        # Get all tables
        table_names = self.db.get_table_names()
        
        for table_name in table_names:
            columns = self.db.get_table_schema(table_name)
            sample_data = self.db.get_sample_data(table_name, limit=3)
            
            table_info = TableInfo(
                name=table_name,
                sample_data=sample_data
            )
            
            for col in columns:
                table_info.columns.append(ColumnInfo(
                    name=col['column_name'],
                    data_type=col['data_type'],
                    is_nullable=col['is_nullable'] == 'YES',
                    default_value=col['column_default']
                ))
            
            context.tables[table_name.lower()] = table_info
        
        # Get foreign keys
        fks = self.db.get_foreign_keys()
        context.foreign_keys = fks
        
        # Update column FK references
        for fk in fks:
            table = context.get_table(fk['source_table'])
            if table:
                col = table.get_column(fk['source_column'])
                if col:
                    col.is_foreign_key = True
                    col.fk_reference = f"{fk['target_table']}({fk['target_column']})"
        
        self._context = context
        return context
    
    def _parse_schema_sql(self, sql_content: str) -> SchemaContext:
        """Parse schema SQL to extract structure"""
        context = SchemaContext()
        
        # Extract ENUM types
        enum_pattern = r"CREATE TYPE (\w+) AS ENUM \(([^)]+)\)"
        for match in re.finditer(enum_pattern, sql_content, re.IGNORECASE):
            enum_name = match.group(1)
            values = [v.strip().strip("'\"") for v in match.group(2).split(",")]
            context.enum_types[enum_name] = values
        
        # Extract table definitions
        table_pattern = r"CREATE TABLE (\w+)\s*\(([^;]+)\);"
        for match in re.finditer(table_pattern, sql_content, re.IGNORECASE | re.DOTALL):
            table_name = match.group(1)
            columns_text = match.group(2)
            
            table_info = TableInfo(name=table_name)
            
            # Extract table comments
            comment_pattern = rf"COMMENT ON TABLE {table_name} IS '([^']+)'"
            comment_match = re.search(comment_pattern, sql_content, re.IGNORECASE)
            if comment_match:
                table_info.description = comment_match.group(1)
            
            # Parse columns
            for line in columns_text.split("\n"):
                line = line.strip().rstrip(",")
                if not line or line.startswith("--") or line.upper().startswith(("UNIQUE", "CONSTRAINT", "CREATE")):
                    continue
                
                # Match column definition
                col_match = re.match(r"(\w+)\s+(\w+[\w\(\),\s]*?)(?:\s+(NOT NULL|NULL|PRIMARY KEY|REFERENCES|DEFAULT|UNIQUE).*)?$", line, re.IGNORECASE)
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2).strip()
                    
                    col_info = ColumnInfo(
                        name=col_name,
                        data_type=col_type,
                        is_primary_key="PRIMARY KEY" in line.upper(),
                        is_nullable="NOT NULL" not in line.upper()
                    )
                    
                    # Check if it's an enum type
                    if col_type in context.enum_types:
                        col_info.enum_values = context.enum_types[col_type]
                    
                    # Check for foreign key
                    fk_match = re.search(r"REFERENCES\s+(\w+)\((\w+)\)", line, re.IGNORECASE)
                    if fk_match:
                        col_info.is_foreign_key = True
                        col_info.fk_reference = f"{fk_match.group(1)}({fk_match.group(2)})"
                        context.foreign_keys.append({
                            'source_table': table_name,
                            'source_column': col_name,
                            'target_table': fk_match.group(1),
                            'target_column': fk_match.group(2)
                        })
                    
                    if col_info.is_primary_key:
                        table_info.primary_key = col_name
                    
                    table_info.columns.append(col_info)
            
            context.tables[table_name.lower()] = table_info
        
        # Extract views
        view_pattern = r"CREATE OR REPLACE VIEW (\w+) AS\s+(SELECT[^;]+);"
        for match in re.finditer(view_pattern, sql_content, re.IGNORECASE | re.DOTALL):
            context.views[match.group(1)] = match.group(2).strip()
        
        self._context = context
        logger.info(f"Parsed schema: {len(context.tables)} tables, {len(context.enum_types)} enums, {len(context.views)} views")
        return context
    
    def get_context(self) -> SchemaContext:
        """Get cached context or build from file"""
        if self._context is None:
            self._context = self.build_from_file()
        return self._context
    
    def get_relevant_tables(self, keywords: List[str]) -> List[str]:
        """
        Find tables relevant to given keywords.
        
        Uses table names, column names, and descriptions for matching.
        """
        context = self.get_context()
        scores: Dict[str, int] = {}
        
        keywords_lower = [k.lower() for k in keywords]
        
        for table_name, table_info in context.tables.items():
            score = 0
            
            # Check table name
            for kw in keywords_lower:
                if kw in table_name:
                    score += 10
            
            # Check description
            if table_info.description:
                for kw in keywords_lower:
                    if kw in table_info.description.lower():
                        score += 5
            
            # Check column names
            for col in table_info.columns:
                for kw in keywords_lower:
                    if kw in col.name.lower():
                        score += 3
            
            if score > 0:
                scores[table_name] = score
        
        # Sort by relevance score
        sorted_tables = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
        return sorted_tables


# Convenience function
def get_schema_context() -> SchemaContext:
    """Get default schema context"""
    builder = SchemaContextBuilder()
    return builder.get_context()

"""
Schema Linker for CHASE-SQL.

Implements the Divide-and-Conquer schema linking approach from the CHASE-SQL paper.
Analyzes natural language queries and identifies relevant database tables/columns.
"""
import re
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field

from .config import default_config
from .schema_context import SchemaContextBuilder, SchemaContext, get_schema_context
from .llm_client import BaseLLMClient, get_llm_client
from .prompts.clinical_prompts import CLINICAL_DOMAIN_CONTEXT, TERM_MAPPINGS
from .prompts.schema_linking import SCHEMA_LINKING_PROMPT, ENTITY_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class LinkedSchema:
    """Result of schema linking process"""
    tables: List[str] = field(default_factory=list)
    columns: Dict[str, List[str]] = field(default_factory=dict)  # table -> columns
    join_path: List[Tuple[str, str, str, str]] = field(default_factory=list)  # (table1, col1, table2, col2)
    filters: List[Dict[str, Any]] = field(default_factory=list)
    aggregation: Optional[str] = None
    entities: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.0


class SchemaLinker:
    """
    Schema Linker for CHASE-SQL.
    
    Implements divide-and-conquer schema linking:
    1. Extract entities and conditions from natural language
    2. Map entities to database tables
    3. Identify required columns and join paths
    4. Prune schema to relevant elements
    """
    
    def __init__(
        self,
        schema_context: Optional[SchemaContext] = None,
        llm_client: Optional[BaseLLMClient] = None
    ):
        self.schema_context = schema_context or get_schema_context()
        self.llm_client = llm_client or get_llm_client()
        
        # Build inverted index for keyword matching
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build index from keywords to tables/columns"""
        self.keyword_to_tables: Dict[str, Set[str]] = {}
        
        for table_name, table_info in self.schema_context.tables.items():
            # Index table name
            for word in self._tokenize(table_name):
                self.keyword_to_tables.setdefault(word, set()).add(table_name)
            
            # Index column names
            for col in table_info.columns:
                for word in self._tokenize(col.name):
                    self.keyword_to_tables.setdefault(word, set()).add(table_name)
            
            # Index description
            if table_info.description:
                for word in self._tokenize(table_info.description):
                    self.keyword_to_tables.setdefault(word, set()).add(table_name)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into keywords"""
        # Split on underscores and camelCase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = text.replace('_', ' ')
        words = text.lower().split()
        return [w for w in words if len(w) > 2]
    
    def link(self, question: str) -> LinkedSchema:
        """
        Main entry point: link natural language question to schema elements.
        
        Implements the divide-and-conquer approach:
        1. Quick keyword-based matching (fast path)
        2. LLM-based entity extraction if needed
        3. Build join paths between tables
        """
        result = LinkedSchema()
        
        # Step 1: Extract keywords and find matching tables
        keywords = self._tokenize(question.lower())
        matched_tables = self._match_tables_by_keywords(keywords)
        
        # Step 2: Check for clinical term mappings
        for term, (table, column, value) in TERM_MAPPINGS.items():
            if term.lower() in question.lower():
                matched_tables.add(table)
                if value:
                    result.filters.append({
                        "table": table,
                        "column": column,
                        "operator": "=",
                        "value": value
                    })
        
        # Step 3: Extract study/site/subject identifiers
        identifiers = self._extract_identifiers(question)
        for id_type, id_value in identifiers:
            if id_type == "study":
                matched_tables.add("studies")
                result.filters.append({
                    "table": "studies",
                    "column": "study_code",
                    "operator": "=",
                    "value": id_value
                })
            elif id_type == "site":
                matched_tables.add("sites")
                result.filters.append({
                    "table": "sites",
                    "column": "site_number",
                    "operator": "=",
                    "value": id_value
                })
            elif id_type == "subject":
                matched_tables.add("subjects")
                result.filters.append({
                    "table": "subjects",
                    "column": "subject_number",
                    "operator": "=",
                    "value": id_value
                })
        
        # Step 4: If we need more precise linking, use LLM
        if len(matched_tables) > 5 or len(matched_tables) == 0:
            llm_result = self._llm_schema_linking(question)
            if llm_result:
                matched_tables.update(llm_result.tables)
                result.filters.extend(llm_result.filters)
                result.entities = llm_result.entities
                result.reasoning = llm_result.reasoning
        
        # Step 5: Build join paths
        result.tables = list(matched_tables)
        result.join_path = self._build_join_path(result.tables)
        
        # Step 6: Select relevant columns for each table
        result.columns = self._select_columns(result.tables, keywords, result.filters)
        
        # Step 7: Detect aggregation
        result.aggregation = self._detect_aggregation(question)
        
        logger.info(f"Schema linking: {len(result.tables)} tables, {len(result.filters)} filters")
        return result
    
    def _match_tables_by_keywords(self, keywords: List[str]) -> Set[str]:
        """Find tables matching the given keywords"""
        table_scores: Dict[str, int] = {}
        
        for kw in keywords:
            if kw in self.keyword_to_tables:
                for table in self.keyword_to_tables[kw]:
                    table_scores[table] = table_scores.get(table, 0) + 1
        
        # Return tables with at least 1 match, sorted by score
        matched = sorted(table_scores.keys(), key=lambda t: table_scores[t], reverse=True)
        return set(matched[:10])  # Limit to top 10
    
    def _extract_identifiers(self, question: str) -> List[Tuple[str, str]]:
        """Extract study/site/subject identifiers"""
        identifiers = []
        
        # Study identifiers: "Study 1", "Study 15", etc.
        study_pattern = r"Study\s*(\d+)"
        for match in re.finditer(study_pattern, question, re.IGNORECASE):
            identifiers.append(("study", f"Study {match.group(1)}"))
        
        # Site identifiers: "Site 18", "Site 2", etc.
        site_pattern = r"Site\s*(\d+)"
        for match in re.finditer(site_pattern, question, re.IGNORECASE):
            identifiers.append(("site", f"Site {match.group(1)}"))
        
        # Subject identifiers: "Subject 63", etc.
        subject_pattern = r"Subject\s*(\d+)"
        for match in re.finditer(subject_pattern, question, re.IGNORECASE):
            identifiers.append(("subject", f"Subject {match.group(1)}"))
        
        return identifiers
    
    def _llm_schema_linking(self, question: str) -> Optional[LinkedSchema]:
        """Use LLM for precise schema linking"""
        try:
            # Build compact schema context
            schema_str = self.schema_context.to_prompt_context(
                include_samples=False,
                max_tables=20
            )
            
            prompt = SCHEMA_LINKING_PROMPT.format(
                schema_context=schema_str,
                domain_context=CLINICAL_DOMAIN_CONTEXT,
                question=question
            )
            
            response = self.llm_client.complete(prompt)
            parsed = self.llm_client.extract_json(response)
            
            if parsed:
                result = LinkedSchema()
                result.tables = parsed.get("tables_needed", [])
                result.reasoning = parsed.get("reasoning", "")
                result.filters = parsed.get("filters", [])
                result.entities = parsed.get("entities_found", [])
                return result
                
        except Exception as e:
            logger.warning(f"LLM schema linking failed: {e}")
        
        return None
    
    def _build_join_path(self, tables: List[str]) -> List[Tuple[str, str, str, str]]:
        """Build join path between tables using foreign keys"""
        join_path = []
        processed = set()
        
        # Start with core tables
        core_order = ['studies', 'sites', 'subjects', 'visits']
        ordered_tables = [t for t in core_order if t in tables]
        ordered_tables.extend([t for t in tables if t not in core_order])
        
        for table in ordered_tables:
            if table in processed:
                continue
                
            for fk in self.schema_context.foreign_keys:
                src, src_col = fk['source_table'].lower(), fk['source_column']
                tgt, tgt_col = fk['target_table'].lower(), fk['target_column']
                
                if src == table and tgt in tables and tgt in processed:
                    join_path.append((src, src_col, tgt, tgt_col))
                elif tgt == table and src in tables and src in processed:
                    join_path.append((src, src_col, tgt, tgt_col))
            
            processed.add(table)
        
        return join_path
    
    def _select_columns(
        self, 
        tables: List[str], 
        keywords: List[str],
        filters: List[Dict]
    ) -> Dict[str, List[str]]:
        """Select relevant columns for each table"""
        columns = {}
        
        for table_name in tables:
            table_info = self.schema_context.get_table(table_name)
            if not table_info:
                continue
            
            selected = []
            
            # Always include primary key
            if table_info.primary_key:
                selected.append(table_info.primary_key)
            
            # Include columns matching keywords
            for col in table_info.columns:
                col_keywords = self._tokenize(col.name)
                if any(kw in col_keywords for kw in keywords):
                    selected.append(col.name)
                    
                # Include FK columns for joins
                if col.is_foreign_key and col.name not in selected:
                    selected.append(col.name)
            
            # Include filter columns
            for flt in filters:
                if flt.get("table") == table_name:
                    col = flt.get("column")
                    if col and col not in selected:
                        selected.append(col)
            
            # If no specific columns, include key identifiers
            if len(selected) <= 1:
                for name_pattern in ['name', 'number', 'code', 'status', 'date']:
                    for col in table_info.columns:
                        if name_pattern in col.name.lower() and col.name not in selected:
                            selected.append(col.name)
                            break
            
            columns[table_name] = selected[:10]  # Limit columns
        
        return columns
    
    def _detect_aggregation(self, question: str) -> Optional[str]:
        """Detect if the question requires aggregation"""
        question_lower = question.lower()
        
        if any(w in question_lower for w in ['how many', 'count', 'total number']):
            return "COUNT"
        if any(w in question_lower for w in ['average', 'avg', 'mean']):
            return "AVG"
        if any(w in question_lower for w in ['maximum', 'max', 'highest']):
            return "MAX"
        if any(w in question_lower for w in ['minimum', 'min', 'lowest']):
            return "MIN"
        if any(w in question_lower for w in ['sum', 'total']):
            return "SUM"
        
        return None
    
    def get_filtered_schema(self, linked: LinkedSchema) -> str:
        """Get schema context filtered to linked tables only"""
        return self.schema_context.to_prompt_context(
            tables=linked.tables,
            include_samples=True,
            max_tables=len(linked.tables)
        )

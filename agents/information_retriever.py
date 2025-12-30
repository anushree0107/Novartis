"""
Information Retriever Agent (IR)
CHESS Agent 1: Gathers relevant information related to input

Tools:
1. extract_keywords - Extract main keywords from natural language question
2. retrieve_entity - Search for similar values in database using LSH
3. retrieve_context - Get relevant schema descriptions from vector DB
"""
from typing import Dict, Any, List, Optional
import time

from agents.base_agent import BaseAgent, BaseTool, AgentResult, ToolResult
from database.schema_manager import SchemaManager, schema_manager
from preprocessing.indexer import DatabasePreprocessor, preprocessor
from utils.llm_client import GroqLLMClient
from config.settings import MODELS


# ============== TOOLS ==============

class ExtractKeywordsTool(BaseTool):
    """
    Tool: extract_keywords
    Extracts primary keywords and key phrases from the natural language question.
    Uses few-shot LLM prompting.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="extract_keywords",
            description="Extract keywords from natural language question",
            llm_client=llm_client
        )
    
    def execute(self, question: str) -> ToolResult:
        """Extract keywords from the question"""
        
        system_prompt = """You are a keyword extraction expert for clinical trial databases.
Extract the most important keywords and phrases from questions that would help find relevant database tables and values.

Focus on:
1. Entity names (patients, sites, studies, visits)
2. Metric names (counts, rates, percentages)
3. Status values (open, closed, complete, missing)
4. Specific values that might be in the database
5. Clinical terms (eSAE, SDV, CRF, EDC, query)

Return a JSON object with:
{
    "keywords": ["keyword1", "keyword2", ...],
    "entities": ["entity values to search for"],
    "clinical_terms": ["domain-specific terms"],
    "filters": ["filter conditions mentioned"]
}"""

        user_content = f"""Extract keywords from this clinical trial database question:

Question: "{question}"

Examples:
Q: "How many open queries are there for site 101?"
A: {{"keywords": ["open", "queries", "site"], "entities": ["101", "site 101"], "clinical_terms": ["queries"], "filters": ["open"]}}

Q: "Show patients with missing visit data in Study 5"
A: {{"keywords": ["patients", "missing", "visit", "data", "study"], "entities": ["Study 5", "5"], "clinical_terms": ["visit"], "filters": ["missing"]}}

Now extract for the given question:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(messages, json_mode=True, max_tokens=512)
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error=response.get('error', 'Failed to extract keywords')
            )
        
        keywords_data = self.llm.extract_json(response['content'])
        
        if not keywords_data:
            # Fallback: simple extraction
            keywords_data = {
                "keywords": question.lower().split(),
                "entities": [],
                "clinical_terms": [],
                "filters": []
            }
        
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=True,
            data=keywords_data,
            tool_name=self.name,
            tokens_used=tokens
        )


class RetrieveEntityTool(BaseTool):
    """
    Tool: retrieve_entity
    Searches for similar values in the database using LSH + edit distance.
    Returns matching values with their table/column information.
    """
    
    def __init__(self, preprocessor_instance: DatabasePreprocessor):
        super().__init__(
            name="retrieve_entity",
            description="Search for similar values in database"
        )
        self.preprocessor = preprocessor_instance
    
    def execute(self, keywords: List[str], top_k: int = 5) -> ToolResult:
        """
        Search for entities matching keywords
        
        Args:
            keywords: List of keywords/entities to search for
            top_k: Number of results per keyword
        """
        all_results = {}
        
        for keyword in keywords:
            if len(keyword) < 2:  # Skip very short keywords
                continue
            
            matches = self.preprocessor.retrieve_entities(keyword, top_k=top_k)
            if matches:
                all_results[keyword] = matches
        
        return ToolResult(
            success=True,
            data={
                "matched_entities": all_results,
                "total_matches": sum(len(v) for v in all_results.values())
            },
            tool_name=self.name,
            tokens_used=0  # No LLM call
        )


class RetrieveContextTool(BaseTool):
    """
    Tool: retrieve_context
    Retrieves relevant schema descriptions from vector database.
    Provides contextual information about tables and columns.
    """
    
    def __init__(self, preprocessor_instance: DatabasePreprocessor):
        super().__init__(
            name="retrieve_context",
            description="Get relevant schema context from database catalog"
        )
        self.preprocessor = preprocessor_instance
    
    def execute(self, question: str, top_k: int = 10) -> ToolResult:
        """
        Retrieve context relevant to the question
        
        Args:
            question: Natural language question
            top_k: Number of context items to retrieve
        """
        context_items = self.preprocessor.retrieve_context(question, top_k=top_k)
        
        # Organize by table
        tables_context = {}
        for item in context_items:
            table = item['table']
            if table not in tables_context:
                tables_context[table] = {
                    'description': item.get('description', ''),
                    'columns': [],
                    'relevance': item['similarity']
                }
            if item.get('column'):
                tables_context[table]['columns'].append(item['column'])
        
        return ToolResult(
            success=True,
            data={
                "context_items": context_items,
                "relevant_tables": tables_context,
                "num_tables": len(tables_context)
            },
            tool_name=self.name,
            tokens_used=0  # No LLM call
        )


# ============== AGENT ==============

class InformationRetrieverAgent(BaseAgent):
    """
    Agent 1: Information Retriever (IR)
    
    Gathers relevant information related to the input:
    - Extracts keywords from the question
    - Retrieves matching entities from database
    - Gets relevant context from schema descriptions
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        schema_mgr: SchemaManager = None,
        preprocess: DatabasePreprocessor = None,
        **kwargs
    ):
        self.schema = schema_mgr or schema_manager
        self.preprocessor = preprocess or preprocessor
        super().__init__(llm_client, model=MODELS.get('evaluator'), **kwargs)
        self.name = "InformationRetriever"
    
    def _register_tools(self):
        """Register IR agent tools"""
        self.add_tool(ExtractKeywordsTool(self.llm))
        self.add_tool(RetrieveEntityTool(self.preprocessor))
        self.add_tool(RetrieveContextTool(self.preprocessor))
    
    def get_system_prompt(self) -> str:
        return """You are an Information Retrieval agent for clinical trial databases.
Your job is to gather all relevant information needed to answer questions about clinical data."""

    def execute(self, question: str, additional_context: str = "") -> AgentResult:
        """
        Execute IR agent pipeline:
        1. Extract keywords from question
        2. Retrieve matching entities from database
        3. Get relevant schema context
        
        Args:
            question: Natural language question
            additional_context: Any extra context provided
            
        Returns:
            AgentResult with gathered information
        """
        start_time = time.time()
        tool_calls = []
        total_tokens = 0
        
        # Step 1: Extract keywords
        self.log("Extracting keywords...")
        keywords_result = self.call_tool("extract_keywords", question=question)
        tool_calls.append(keywords_result)
        total_tokens += keywords_result.tokens_used
        
        if not keywords_result.success:
            return AgentResult(
                success=False,
                data=None,
                error="Failed to extract keywords",
                tool_calls=tool_calls,
                execution_time=time.time() - start_time
            )
        
        keywords_data = keywords_result.data
        
        # Step 2: Retrieve entities
        self.log("Retrieving entities from database...")
        all_keywords = (
            keywords_data.get('keywords', []) + 
            keywords_data.get('entities', [])
        )
        
        entity_result = self.call_tool(
            "retrieve_entity",
            keywords=all_keywords,
            top_k=5
        )
        tool_calls.append(entity_result)
        
        # Step 3: Retrieve context
        self.log("Retrieving schema context...")
        context_result = self.call_tool(
            "retrieve_context",
            question=question,
            top_k=10
        )
        tool_calls.append(context_result)
        
        # Combine all retrieved information
        retrieved_info = {
            "question": question,
            "keywords": keywords_data,
            "entities": entity_result.data if entity_result.success else {},
            "context": context_result.data if context_result.success else {},
            "relevant_tables": self._identify_relevant_tables(
                keywords_data,
                entity_result.data if entity_result.success else {},
                context_result.data if context_result.success else {},
                question=question
            )
        }
        
        self.log(f"Retrieved info for {len(retrieved_info['relevant_tables'])} relevant tables", "success")
        
        return AgentResult(
            success=True,
            data=retrieved_info,
            reasoning=f"Extracted {len(all_keywords)} keywords, "
                     f"found {entity_result.data.get('total_matches', 0) if entity_result.success else 0} entity matches",
            tokens_used=total_tokens,
            execution_time=time.time() - start_time,
            tool_calls=tool_calls
        )
    
    def _identify_relevant_tables(
        self,
        keywords_data: Dict,
        entity_data: Dict,
        context_data: Dict,
        question: str = ""
    ) -> List[str]:
        """Identify relevant tables from all gathered information"""
        tables = set()
        
        # Check for meta-questions about the database itself
        question_lower = question.lower() if question else ""
        meta_keywords = ['how many studies', 'number of studies', 'count studies', 
                        'list studies', 'all studies', 'which studies', 'what studies',
                        'total studies', 'studies are there', 'studies exist',
                        'how many tables', 'database info', 'database structure']
        
        if any(mk in question_lower for mk in meta_keywords):
            # Add metadata tables for meta-questions
            tables.add('_studies')
            tables.add('_table_metadata')
        
        # From entity matches
        for keyword, matches in entity_data.get('matched_entities', {}).items():
            for match in matches:
                tables.add(match['table'])
        
        # From context
        for table in context_data.get('relevant_tables', {}).keys():
            tables.add(table)
        
        # From clinical terms mapping
        term_to_category = {
            'visit': 'visit',
            'patient': 'visit',
            'subject': 'visit',
            'query': 'query',
            'queries': 'query',
            'edrr': 'query',
            'safety': 'safety',
            'sae': 'safety',
            'esae': 'safety',
            'adverse': 'safety',
            'coding': 'coding',
            'meddra': 'coding',
            'whodd': 'coding',
            'lab': 'lab',
            'laboratory': 'lab',
            'edc': 'edc_metrics',
            'metrics': 'edc_metrics',
            'form': 'forms',
            'page': 'pages',
            'missing': 'pages'
        }
        
        for term in keywords_data.get('clinical_terms', []) + keywords_data.get('keywords', []):
            term_lower = term.lower()
            for key, category in term_to_category.items():
                if key in term_lower:
                    category_tables = self.schema.get_tables_by_category(category)
                    for t in category_tables[:3]:  # Limit per category
                        tables.add(t.name)
        
        return list(tables)

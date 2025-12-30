"""SAGE-Flow Router: Intelligent query classification."""
import json
import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from prompts import ROUTER_SYSTEM_PROMPT


class QueryIntent(Enum):
    SQL_ONLY = "SQL_ONLY"
    GRAPH_ONLY = "GRAPH_ONLY"
    SQL_THEN_GRAPH = "SQL_THEN_GRAPH"
    GRAPH_THEN_SQL = "GRAPH_THEN_SQL"


@dataclass
class RouterResult:
    intent: QueryIntent
    reasoning: str
    sql_hint: Optional[str] = None
    graph_hint: Optional[str] = None
    confidence: float = 1.0


class IntentRouter:
    """Routes queries to optimal execution path using fast heuristics + LLM fallback."""
    
    def __init__(self, llm, use_fast_classification: bool = True):
        self.llm = llm
        self.use_fast_classification = use_fast_classification
        self._sql_patterns = [
            r'\bhow many\b', r'\bcount\b', r'\btotal\b', r'\blist all\b',
            r'\baverage\b', r'\bsum\b', r'\bmax\b', r'\bmin\b',
        ]
        self._graph_patterns = [
            r'\bexplain\b', r'\bdescribe\b', r'\brelationship\b', r'\bconnected\b',
            r'\bwhy\b', r'\bsafety\b', r'\binvestigate\b',
        ]
        self._synergy_sql_first = [r'\b(top|largest|biggest|most|highest)\s+\d+\b']
        self._synergy_graph_first = [r'\b(related to|similar to)\b']
    
    def _fast_classify(self, question: str) -> Optional[QueryIntent]:
        q_lower = question.lower()
        for pattern in self._synergy_sql_first:
            if re.search(pattern, q_lower):
                return QueryIntent.SQL_THEN_GRAPH
        for pattern in self._synergy_graph_first:
            if re.search(pattern, q_lower):
                return QueryIntent.GRAPH_THEN_SQL
        sql_score = sum(1 for p in self._sql_patterns if re.search(p, q_lower))
        graph_score = sum(1 for p in self._graph_patterns if re.search(p, q_lower))
        if sql_score >= 2 and graph_score == 0:
            return QueryIntent.SQL_ONLY
        if graph_score >= 2 and sql_score == 0:
            return QueryIntent.GRAPH_ONLY
        return None
    
    def _llm_classify(self, question: str) -> RouterResult:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"Classify this question: {question}")
        ]
        response = self.llm.invoke(messages)
        content = response.content
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            data = json.loads(json_match.group()) if json_match else json.loads(content)
            intent = QueryIntent(data.get('classification', 'GRAPH_ONLY'))
            return RouterResult(
                intent=intent,
                reasoning=data.get('reasoning', ''),
                sql_hint=data.get('sql_hint'),
                graph_hint=data.get('graph_hint')
            )
        except (json.JSONDecodeError, ValueError):
            return RouterResult(intent=QueryIntent.GRAPH_ONLY, reasoning="Default fallback", confidence=0.5)
    
    def classify(self, question: str) -> RouterResult:
        if self.use_fast_classification:
            fast_result = self._fast_classify(question)
            if fast_result:
                return RouterResult(intent=fast_result, reasoning="Fast heuristics", confidence=0.85)
        return self._llm_classify(question)

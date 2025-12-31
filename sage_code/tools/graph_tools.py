"""Graph Query Tools."""

from typing import Optional, List, Dict, Type
from pydantic import BaseModel, Field
import networkx as nx
from collections import defaultdict

try:
    from .base_tool import BaseTool
except ImportError:
    from .base_tool import BaseTool


class StudyQueryInput(BaseModel):
    study_id: Optional[str] = Field(default=None, description="Study ID")

class SubjectQueryInput(BaseModel):
    min_issues: int = Field(default=1, description="Minimum issues")
    limit: int = Field(default=20, description="Max results")

class SafetyReviewInput(BaseModel):
    status: str = Field(default="Pending", description="Review status")
    limit: int = Field(default=20, description="Max results")

class MissingPagesInput(BaseModel):
    min_days: float = Field(default=30, description="Minimum days missing")
    limit: int = Field(default=20, description="Max results")

class SiteRiskInput(BaseModel):
    limit: int = Field(default=10, description="Top sites")

class FlexibleQueryInput(BaseModel):
    source_type: str = Field(description="Source node type")
    target_type: str = Field(description="Target node type")
    filter_property: Optional[str] = Field(default=None, description="Filter property")
    filter_value: Optional[str] = Field(default=None, description="Filter value")
    limit: int = Field(default=10, description="Max results")


class GraphQueryMixin:
    def __init__(self, graph: nx.DiGraph = None, **kwargs):
        self.graph = graph
        super().__init__(**kwargs)
    
    def _nodes_by_type(self, t: str) -> List[str]:
        return [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == t] if self.graph else []
    
    def _props(self, node: str) -> Dict:
        return dict(self.graph.nodes[node]) if self.graph and self.graph.has_node(node) else {}
    
    def _neighbors(self, node: str, edge_type: str = None) -> List[tuple]:
        if not self.graph:
            return []
        result = []
        for _, t, d in self.graph.out_edges(node, data=True):
            if not edge_type or d.get("edge_type") == edge_type:
                result.append((t, d))
        for s, _, d in self.graph.in_edges(node, data=True):
            if not edge_type or d.get("edge_type") == edge_type:
                result.append((s, d))
        return result


class StudyInfoTool(GraphQueryMixin, BaseTool):
    name = "get_study_info"
    description = "Get study information and metrics."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return StudyQueryInput
    
    def _run(self, study_id: str = None) -> str:
        studies = self._nodes_by_type("Study")
        if study_id:
            props = self._props(f"STUDY:{study_id}")
            return f"Study {study_id}: {props.get('total_issues', 0)} issues" if props else f"Study '{study_id}' not found"
        return f"Found {len(studies)} studies:\n" + "\n".join(f"- {self._props(n).get('study_id')}: {self._props(n).get('total_issues', 0)} issues" for n in studies[:10])


class SubjectIssuesTool(GraphQueryMixin, BaseTool):
    name = "find_subjects_with_issues"
    description = "Find subjects with open issues."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return SubjectQueryInput
    
    def _run(self, min_issues: int = 1, limit: int = 20) -> str:
        results = [(self._props(n).get("subject_id"), int(self._props(n).get("open_issue_count", 0))) 
                   for n in self._nodes_by_type("Subject")]
        results = sorted([(s, i) for s, i in results if i >= min_issues], key=lambda x: -x[1])[:limit]
        return f"Found {len(results)} subjects:\n" + "\n".join(f"- {s}: {i} issues" for s, i in results) if results else f"No subjects with >= {min_issues} issues"


class SafetyReviewTool(GraphQueryMixin, BaseTool):
    name = "find_safety_reviews"
    description = "Find safety discrepancies by status."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return SafetyReviewInput
    
    def _run(self, status: str = "Pending", limit: int = 20) -> str:
        results = []
        for n in self._nodes_by_type("SafetyDiscrepancy"):
            p = self._props(n)
            if status.lower() in p.get("review_status", "").lower():
                for nb, _ in self._neighbors(n, "HAS_DISCREPANCY"):
                    if "SUBJECT:" in nb:
                        results.append((p.get("discrepancy_id"), self._props(nb).get("subject_id")))
                        break
        return f"Found {min(len(results), limit)} reviews:\n" + "\n".join(f"- {d}: {s}" for d, s in results[:limit]) if results else "No reviews found"


class SafetyReviewsBySiteTool(GraphQueryMixin, BaseTool):
    name = "get_safety_reviews_by_site"
    description = "Aggregate safety reviews by site."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return SafetyReviewInput
    
    def _run(self, status: str = "Pending", limit: int = 10) -> str:
        counts = defaultdict(int)
        for d in self._nodes_by_type("SafetyDiscrepancy"):
            if status.lower() not in self._props(d).get("review_status", "").lower():
                continue
            for s, _ in self._neighbors(d, "HAS_DISCREPANCY"):
                if "SUBJECT:" in s:
                    for site, _ in self._neighbors(s, "ENROLLED_AT"):
                        if "SITE:" in site:
                            counts[self._props(site).get("site_id", site)] += 1
        results = sorted(counts.items(), key=lambda x: -x[1])[:limit]
        return f"Sites with {status} reviews:\n" + "\n".join(f"- {s}: {c}" for s, c in results) if results else "No sites found"


class MissingPagesTool(GraphQueryMixin, BaseTool):
    name = "find_missing_pages"
    description = "Find aged missing pages."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return MissingPagesInput
    
    def _run(self, min_days: float = 30, limit: int = 20) -> str:
        results = [(float(self._props(n).get("days_missing", 0)), n) for n in self._nodes_by_type("MissingPage")]
        results = sorted([(d, n) for d, n in results if d >= min_days], key=lambda x: -x[0])[:limit]
        return f"Found {len(results)} missing pages:\n" + "\n".join(f"- {d:.0f} days" for d, _ in results) if results else "No missing pages found"


class SiteRiskTool(GraphQueryMixin, BaseTool):
    name = "get_site_risk_summary"
    description = "Get risk summary by site."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return SiteRiskInput
    
    def _run(self, limit: int = 10) -> str:
        stats = defaultdict(lambda: {"issues": 0, "subjects": 0})
        for s in self._nodes_by_type("Subject"):
            issues = int(self._props(s).get("open_issue_count", 0))
            for site, _ in self._neighbors(s, "ENROLLED_AT"):
                name = self._props(site).get("site_id", site)
                stats[name]["issues"] += issues
                stats[name]["subjects"] += 1
        results = sorted(stats.items(), key=lambda x: -x[1]["issues"])[:limit]
        return "\n".join(f"- {s}: {d['issues']} issues ({d['subjects']} subjects)" for s, d in results)


class FlexibleGraphQueryTool(GraphQueryMixin, BaseTool):
    name = "query_graph_flexible"
    description = "Flexible source→target aggregation query."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return FlexibleQueryInput
    
    def _find_target(self, start: str, target_type: str) -> Optional[str]:
        visited, queue = set(), [(start, 0)]
        while queue:
            node, hop = queue.pop(0)
            if node in visited or hop > 4:
                continue
            visited.add(node)
            if self._props(node).get("node_type") == target_type:
                return node
            queue.extend((n, hop + 1) for n, _ in self._neighbors(node) if n not in visited)
        return None
    
    def _run(self, source_type: str, target_type: str, filter_property: str = None, filter_value: str = None, limit: int = 10) -> str:
        agg = defaultdict(int)
        for src in self._nodes_by_type(source_type):
            p = self._props(src)
            if filter_property and filter_value and filter_value.lower() not in str(p.get(filter_property, "")).lower():
                continue
            tgt = self._find_target(src, target_type)
            if tgt:
                tp = self._props(tgt)
                tid = tp.get("study_id") or tp.get("site_id") or tp.get("country_code") or tgt.split(":")[-1]
                agg[tid] += 1
        results = sorted(agg.items(), key=lambda x: -x[1])[:limit]
        return f"{source_type} → {target_type}:\n" + "\n".join(f"- {t}: {c}" for t, c in results) if results else "No results"


class MultiHopQueryInput(BaseModel):
    query: str = Field(description="Complex query requiring multi-hop reasoning")
    n_hops: int = Field(default=2, description="Number of hops to traverse")
    top_k: int = Field(default=5, description="Number of results to return")


class MultiHopQueryTool(GraphQueryMixin, BaseTool):
    name = "multi_hop_graph_query"
    description = """Use for complex questions requiring information from multiple connected entities.
    Examples:
    - "Which sites have subjects with both open issues AND pending safety reviews?"
    - "Find studies where subjects have both coding problems and missing pages"
    - "What subjects at Site X have discrepancies older than 30 days?"
    Best for: Cross-entity analysis, multi-condition queries, relationship exploration."""
    
    def __init__(self, graph: nx.DiGraph = None, hop_engine=None, **kwargs):
        super().__init__(graph=graph, **kwargs)
        self._hop_engine = hop_engine
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return MultiHopQueryInput
    
    def _run(self, query: str, n_hops: int = 2, top_k: int = 5) -> str:
        if not self._hop_engine:
            # Lazy init if not provided
            try:
                from ..hop_rag import CodeAugmentedGraphEngine
            except ImportError:
                from graph_rag.hop_rag import CodeAugmentedGraphEngine
            
            # Use provided LLM or let engine init it
            self._hop_engine = CodeAugmentedGraphEngine(self.graph)
            # If we were given an LLM in kwargs during init but didn't make engine yet
            # Note: MultiHopQueryTool usually gets engine passed in if created via create_multi_hop_tool
            # But if created via registry/init, we might lack engine.
            # Ideally the agent injects the engine or LLM.
        
        # Execute retrieve-reason-prune
        results = self._hop_engine.retrieve_reason_prune(
            query=query,
            top_k=top_k,
            n_hops=n_hops
        )
        
        if not results:
            return "No relevant information found for this multi-hop query."
        
        # Format results
        context = self._hop_engine.format_results_for_context(results)
        
        # Add summary
        node_types = {}
        for r in results:
            node_types[r.node_type] = node_types.get(r.node_type, 0) + 1
        
        type_summary = ", ".join(f"{count} {t}s" for t, count in node_types.items())
        
        return f"Multi-hop query found {len(results)} relevant nodes ({type_summary}):\n{context}"


def create_graph_tools(graph: nx.DiGraph = None, hop_engine=None) -> List[BaseTool]:
    tools = [
        StudyInfoTool(graph=graph),
        SubjectIssuesTool(graph=graph),
        SafetyReviewTool(graph=graph),
        SafetyReviewsBySiteTool(graph=graph),
        MissingPagesTool(graph=graph),
        SiteRiskTool(graph=graph),
        FlexibleGraphQueryTool(graph=graph),
    ]
    
    # Create multi-hop tool with engine
    mh_tool = MultiHopQueryTool(graph=graph, hop_engine=hop_engine)
    if not hop_engine and graph:
        # If no engine provided, we'll try to create one lazily, but it won't have shared LLM
        # unless we modify this signature further. For now this is valid.
        pass
        
    tools.append(mh_tool)
    return tools


def create_multi_hop_tool(graph: nx.DiGraph, hop_engine=None) -> BaseTool:
    """Create a multi-hop query tool with optional pre-configured engine."""
    return MultiHopQueryTool(graph=graph, hop_engine=hop_engine)


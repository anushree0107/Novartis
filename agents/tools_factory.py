
from typing import List, Dict, Any
import pandas as pd
import networkx as nx
from langchain_core.tools import tool

class DebateTools:
    def __init__(self, graph: nx.DiGraph, data: Dict[str, pd.DataFrame]):
        self.graph = graph
        self.data = data

    def get_tools(self) -> List[Any]:
        """Returns the list of tools bound to the current data context."""
        
        @tool
        def query_graph_neighbors(node_id: str) -> str:
            """
            Explore the Knowledge Graph. 
            Input: node_id (e.g., "Site 2" or "Study 21").
            Output: List of connected nodes and their relationship types.
            Use this to find what Study a Site belongs to, or what Subjects are at a Site.
            """
            # Try exact match or prefix match
            target_node = None
            if self.graph.has_node(node_id):
                target_node = node_id
            else:
                # Try formatting: "Site:Site 2" or "Site 2" -> "Site:2"? 
                possible_keys = [node_id, f"Site:{node_id}", f"Study:{node_id}"]
                for k in possible_keys:
                    if self.graph.has_node(k):
                        target_node = k
                        break
            
            if not target_node:
                return f"Node '{node_id}' not found in graph."

            neighbors = list(self.graph.neighbors(target_node))
            return f"Node '{target_node}' is connected to {len(neighbors)} entities: {neighbors[:50]}..."  # Limit output

        @tool
        def query_site_data(site_id: str, query_type: str) -> str:
            """
            Query specific metric dataframes for a site.
            Input:
                - site_id: The site number (e.g., "Site 2")
                - query_type: "missing_pages" or "visit_projection"
            Output: Specific rows or summary stats for that site.
            """
            if query_type == "missing_pages":
                df = self.data.get("missing_pages")
                if df is None: return "Missing Pages data not available."
                # Filter assuming 'sitenumber' column
                res = df[df['sitenumber'] == site_id]
                if res.empty: return f"No missing pages records found for {site_id}."
                return f"Found {len(res)} records. Total Missing Days: {res['no___days_page_missing'].sum()}. Avg: {res['no___days_page_missing'].mean():.2f}"
            
            elif query_type == "visit_projection":
                df = self.data.get("visit_projection")
                if df is None: return "Visit Projection data not available."
                # Filter assuming 'site' column
                res = df[df['site'] == site_id]
                if res.empty: return f"No visit projection records found for {site_id}."
                total_outstanding = res['__days_outstanding'].sum()
                return f"Found {len(res)} visits. Total Days Outstanding: {total_outstanding}."
            
            return "Unknown query_type. Use 'missing_pages' or 'visit_projection'."

        return [query_graph_neighbors, query_site_data]

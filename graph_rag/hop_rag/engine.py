"""HopRAG Engine - Multi-Hop Reasoning for Graph RAG."""

import os
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
import networkx as nx

from .config import HopRAGConfig
from .models import HopResult
from .prompts import PSEUDO_QUERY_PROMPT

logger = logging.getLogger("hop_rag")


class HopRAGEngine:
    def __init__(self, graph: nx.DiGraph, llm=None, config: HopRAGConfig = None):
        self.graph = graph
        self.llm = llm
        self.config = config or HopRAGConfig()
        self._node_index = self._build_node_index()
        self._pseudo_query_cache: Dict[str, Dict[str, List[str]]] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[HopRAG] %(levelname)s: %(message)s"))
            logger.addHandler(handler)
        logger.setLevel(level)
    
    def set_llm(self, llm):
        self.llm = llm
    
    def _init_llm(self):
        if self.llm is None and self.config.use_llm_reasoning:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model=self.config.llm_model,
                    temperature=0.0,
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
                logger.info(f"Initialized LLM: {self.config.llm_model}")
            except Exception as e:
                logger.warning(f"LLM init failed: {e}, using heuristics")
                self.config.use_llm_reasoning = False
    
    def _build_node_index(self) -> Dict[str, List[str]]:
        index = {}
        self._keyword_index = {} # word -> set of node_ids
        
        # Use regex to split words
        import re
        
        count = 0
        for node_id, data in self.graph.nodes(data=True):
            # Type index
            node_type = data.get("node_type", "Unknown")
            if node_type not in index:
                index[node_type] = []
            index[node_type].append(node_id)
            
            # fast inverted index build
            words = set()
            # Split node_id by non-alphanumeric
            words.update(token.lower() for token in re.split(r'[^a-zA-Z0-9]', str(node_id)) if token)
            
            # Attributes
            for key in ['name', 'title', 'id', 'label', 'description', 'node_type']:
                if key in data:
                    val = str(data[key])
                    # Split by non-alphanumeric
                    words.update(token.lower() for token in re.split(r'[^a-zA-Z0-9]', val) if token)
            
            for w in words:
                if w not in self._keyword_index:
                    self._keyword_index[w] = []
                self._keyword_index[w].append(node_id)
            
            count += 1
            if count % 50000 == 0:
                logger.debug(f"Indexed {count} nodes...")
                
        return index
    
    def get_node_types(self) -> List[str]:
        return list(self._node_index.keys())
    
    def get_nodes_by_type(self, node_type: str) -> List[str]:
        return self._node_index.get(node_type, [])
    
    def _format_node_attributes(self, node_id: str) -> str:
        if not self.graph.has_node(node_id):
            return ""
        data = self.graph.nodes[node_id]
        attrs = [f"- {k}: {v}" for k, v in data.items() if k != "node_type" and v]
        return "\n".join(attrs[:10])
    
    def _format_node_edges(self, node_id: str) -> str:
        edges = []
        for _, target, data in self.graph.out_edges(node_id, data=True):
            edge_type = data.get("edge_type", "CONNECTED_TO")
            target_type = self.graph.nodes[target].get("node_type", "Unknown")
            edges.append(f"- --[{edge_type}]--> {target} ({target_type})")
        for source, _, data in self.graph.in_edges(node_id, data=True):
            edge_type = data.get("edge_type", "CONNECTED_TO")
            source_type = self.graph.nodes[source].get("node_type", "Unknown")
            edges.append(f"- <--[{edge_type}]-- {source} ({source_type})")
        return "\n".join(edges[:10])
    
    def generate_pseudo_queries_llm(self, node_id: str) -> Dict[str, List[str]]:
        if node_id in self._pseudo_query_cache:
            return self._pseudo_query_cache[node_id]
        
        self._init_llm()
        
        if not self.llm or not self.config.use_llm_reasoning:
            logger.error("LLM required for pseudo-query generation but not available/enabled")
            return {"in_coming": [], "out_coming": []}
        
        node_data = self.graph.nodes.get(node_id, {})
        node_type = node_data.get("node_type", "Unknown")
        
        prompt = PSEUDO_QUERY_PROMPT.format(
            node_type=node_type,
            node_id=node_id,
            attributes=self._format_node_attributes(node_id),
            edges=self._format_node_edges(node_id)
        )
        
        try:
            logger.debug(f"Generating pseudo-queries for {node_id}")
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            queries = self._parse_pseudo_queries(content)
            self._pseudo_query_cache[node_id] = queries
            logger.info(f"Generated {len(queries.get('in_coming', []))} in / {len(queries.get('out_coming', []))} out queries for {node_id}")
            return queries
        except Exception as e:
            logger.error(f"LLM query gen failed: {e}")
            return {"in_coming": [], "out_coming": []}
    
    def _parse_pseudo_queries(self, response: str) -> Dict[str, List[str]]:
        in_coming, out_coming = [], []
        current_section = None
        
        for line in response.split("\n"):
            line = line.strip()
            if "IN_COMING" in line.upper() or "IN-COMING" in line.upper():
                current_section = "in_coming"
            elif "OUT_COMING" in line.upper() or "OUT-COMING" in line.upper():
                current_section = "out_coming"
            elif line.startswith("-") and current_section:
                query = line.lstrip("- ").strip()
                if query:
                    if current_section == "in_coming":
                        in_coming.append(query)
                    else:
                        out_coming.append(query)
        
        return {"in_coming": in_coming, "out_coming": out_coming}
    
    # Removed reason_best_edge_llm and _select_best_neighbors as part of batch optimization
    
    def initial_retrieve(self, query: str, top_k: int = None) -> List[HopResult]:
        top_k = top_k or self.config.top_k
        logger.info(f"Initial retrieve for: '{query[:50]}...' (top_k={top_k})")
        
        # Ensure index exists
        if not hasattr(self, '_keyword_index'):
             logger.warning("Keyword index missing, rebuilding...")
             self._build_node_index()

        # Improved query tokenization
        import re
        query_words = set(token.lower() for token in re.split(r'[^a-zA-Z0-9]', query) if token)
        
        candidate_counts = {} # node_id -> match_count
        
        # O(query_words) lookup using inverted index
        for word in query_words:
            if word in self._keyword_index:
                for node_id in self._keyword_index[word]:
                    candidate_counts[node_id] = candidate_counts.get(node_id, 0) + 1
        
        results = []
        
        # 1. Keyword Matches
        if candidate_counts:
            scored_nodes = []
            for node_id, count in candidate_counts.items():
                score = count / len(query_words)
                if score > 0:
                     scored_nodes.append((node_id, score))
            
            scored_nodes.sort(key=lambda x: x[1], reverse=True)
            
            for node_id, score in scored_nodes[:top_k]:
                 data = self.graph.nodes[node_id]
                 results.append(HopResult(
                    node_id=node_id,
                    node_type=data.get("node_type", "Unknown"),
                    node_data=dict(data),
                    similarity_score=score,
                    hop_path=[node_id]
                 ))
        
        # 2. Type Fallback (if too few results)
        if len(results) < top_k:
            logger.info("Few keyword matches, using Type Fallback")
            known_types = self.get_node_types()
            # Check if any known type is mentioned in the query
            found_types = [t for t in known_types if t.lower() in query.lower()]
            
            for t in found_types:
                if len(results) >= top_k: break
                
                type_nodes = self.get_nodes_by_type(t)
                import random
                # Sample random nodes of this type
                needed = top_k - len(results)
                extras = random.sample(type_nodes, min(len(type_nodes), needed + 5)) # take a few more
                
                existing_ids = set(r.node_id for r in results)
                for node_id in extras:
                    if node_id not in existing_ids:
                        data = self.graph.nodes[node_id]
                        results.append(HopResult(
                            node_id=node_id,
                            node_type=data.get("node_type", "Unknown"),
                            node_data=dict(data),
                            similarity_score=0.5, # Lower score for fallback
                            hop_path=[node_id]
                        ))
                        if len(results) >= top_k: break
        
        logger.info(f"Initial retrieve found {len(results)} nodes")
        return results
    
    def reason_batch_edges_llm(self, query: str, node_candidates: Dict[str, List[Tuple[str, Dict]]]) -> Dict[str, str]:
        """Reason about best edges for multiple nodes in one LLM call."""
        self._init_llm()
        if not self.llm or not self.config.use_llm_reasoning or not node_candidates:
            return {}
        
        # Prepare tasks text
        tasks = []
        for node_id, candidates in node_candidates.items():
            if not candidates:
                continue
                
            node_data = self.graph.nodes.get(node_id, {})
            node_type = node_data.get("node_type", "Unknown")
            
            edges_desc = []
            for neighbor_id, edge_data in candidates[:5]:  # Limit candidates per node
                nb_data = self.graph.nodes.get(neighbor_id, {})
                nb_type = nb_data.get("node_type", "Unknown")
                edge_type = edge_data.get("edge_type", "CONNECTED")
                nb_info = ", ".join(f"{k}={v}" for k, v in list(nb_data.items())[:2] if v)
                edges_desc.append(f"  - ID: {neighbor_id} ({nb_type}) [{edge_type}] {nb_info}")
            
            tasks.append(f"SOURCE NODE: {node_id} ({node_type})\nCandidates:\n" + "\n".join(edges_desc))
        
        if not tasks:
            return {}
            
        # Chunk tasks if too many (max 5 per batch to avoid context overflow)
        chunk_size = 5
        batches = [tasks[i:i+chunk_size] for i in range(0, len(tasks), chunk_size)]
        
        results = {}
        import json
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from .prompts import BATCH_EDGE_REASONING_PROMPT
        
        def process_batch(chunk_tasks):
            try:
                prompt_text = BATCH_EDGE_REASONING_PROMPT.format(
                    query=query,
                    tasks_text="\n\n".join(chunk_tasks)
                )
                logger.debug(f"Batch reasoning for {len(chunk_tasks)} nodes (parallel)")
                response = self.llm.invoke(prompt_text)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Clean and parse JSON
                content = content.replace("```json", "").replace("```", "").strip()
                idx_start = content.find("{")
                idx_end = content.rfind("}")
                if idx_start != -1 and idx_end != -1:
                    content = content[idx_start:idx_end+1]
                
                return json.loads(content)
            except Exception as e:
                logger.error(f"Batch reasoning failed: {e}")
                return {}
        
        # Execute batches in parallel
        # Max workers = 5 to perform significantly faster than sequential
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_batch = {executor.submit(process_batch, batch): batch for batch in batches}
            for future in as_completed(future_to_batch):
                batch_res = future.result()
                if batch_res:
                    results.update(batch_res)
        
        return results

    def multi_hop_traverse(self, query: str, start_nodes: List[HopResult], n_hops: int = None) -> Dict[str, HopResult]:
        n_hops = n_hops or self.config.n_hops
        logger.info(f"Multi-hop traverse (Optimized): {len(start_nodes)} start nodes, {n_hops} hops")
        
        visited: Set[str] = set(r.node_id for r in start_nodes)
        visit_counter: Dict[str, HopResult] = {r.node_id: r for r in start_nodes}
        
        current_layer = start_nodes
        
        for hop_idx in range(n_hops):
            logger.info(f"Processing Hop {hop_idx + 1}/{n_hops} with {len(current_layer)} nodes")
            
            if not current_layer:
                break
                
            # 1. Collect candidates for all nodes in current layer
            layer_candidates: Dict[str, List[Tuple[str, Dict]]] = {}
            
            for result in current_layer:
                node_id = result.node_id
                candidates = []
                # Out-edges
                for _, target, edge_data in self.graph.out_edges(node_id, data=True):
                    if target not in visited:
                        candidates.append((target, edge_data))
                # In-edges
                for source, _, edge_data in self.graph.in_edges(node_id, data=True):
                    if source not in visited:
                        candidates.append((source, edge_data))
                
                if candidates:
                    layer_candidates[node_id] = candidates
            
            if not layer_candidates:
                break
            
            # 2. Batch reason about best edges
            decisions = self.reason_batch_edges_llm(query, layer_candidates)
            
            # 3. Process decisions and expand
            next_layer = []
            
            for node_id, candidates in layer_candidates.items():
                selected_neighbor = decisions.get(node_id)
                
                # Helper to find edge data for selected neighbor
                best_edge_candidates = []
                if selected_neighbor and selected_neighbor != "NONE":
                    for cand_id, cand_data in candidates:
                        if cand_id == selected_neighbor or cand_id in selected_neighbor: # heuristics string match
                             best_edge_candidates.append((cand_id, cand_data))
                             break
                
                # If LLM failed or returned NONE, maybe fallback? 
                # For now, strict: if LLM didn't pick, we don't expand this node.
                # Except if we want to include 'heuristic fallback' inside the method?
                # User said "optimise latency", so skipping is faster than fallback.
                
                if best_edge_candidates:
                     neighbor_id, edge_data = best_edge_candidates[0]
                     
                     if neighbor_id in visited:
                         if neighbor_id in visit_counter:
                             visit_counter[neighbor_id].visit_count += 1
                         continue
                     
                     visited.add(neighbor_id)
                     node_data = dict(self.graph.nodes[neighbor_id])
                     
                     # Get parent result
                     parent_result = visit_counter.get(node_id) 
                     parent_path = parent_result.hop_path if parent_result else []
                     
                     new_result = HopResult(
                        node_id=neighbor_id,
                        node_type=node_data.get("node_type", "Unknown"),
                        node_data=node_data,
                        visit_count=1,
                        similarity_score=1.0, # Selected by LLM
                        hop_path=parent_path + [neighbor_id]
                     )
                     
                     visit_counter[neighbor_id] = new_result
                     next_layer.append(new_result)
            
            current_layer = next_layer
            
        logger.info(f"Traverse complete: {len(visit_counter)} total nodes visited")
        return visit_counter
    
    def compute_helpfulness(self, query: str, results: Dict[str, HopResult]) -> List[Tuple[HopResult, float]]:
        if not results:
            return []
        
        max_visits = max(r.visit_count for r in results.values()) or 1
        
        scored_results = []
        for result in results.values():
            sim_score = result.similarity_score
            imp_score = result.visit_count / max_visits
            helpfulness = self.config.similarity_weight * sim_score + (1 - self.config.similarity_weight) * imp_score
            scored_results.append((result, helpfulness))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results
    
    def prune_results(self, scored_results: List[Tuple[HopResult, float]], top_k: int = None) -> List[HopResult]:
        top_k = top_k or self.config.top_k
        
        filtered = [(r, s) for r, s in scored_results if s >= self.config.prune_threshold]
        pruned = [result for result, _ in filtered[:top_k]]
        
        logger.info(f"Pruned to {len(pruned)} results (threshold={self.config.prune_threshold})")
        return pruned
    
    def retrieve_reason_prune(self, query: str, top_k: int = None, n_hops: int = None) -> List[HopResult]:
        top_k = top_k or self.config.top_k
        n_hops = n_hops or self.config.n_hops
        
        logger.info(f"=== HopRAG Pipeline Start ===")
        logger.info(f"Query: {query[:80]}...")
        
        self._init_llm()
        
        initial_results = self.initial_retrieve(query, top_k=top_k)
        if not initial_results:
            logger.warning("No initial results found")
            return []
        
        all_results = self.multi_hop_traverse(query, initial_results, n_hops=n_hops)
        scored_results = self.compute_helpfulness(query, all_results)
        final_results = self.prune_results(scored_results, top_k=top_k)
        
        logger.info(f"=== HopRAG Pipeline Complete: {len(final_results)} results ===")
        return final_results
    
    def format_results_for_context(self, results: List[HopResult]) -> str:
        if not results:
            return "No relevant information found."
        
        context_parts = []
        by_type: Dict[str, List[HopResult]] = {}
        
        for result in results:
            if result.node_type not in by_type:
                by_type[result.node_type] = []
            by_type[result.node_type].append(result)
        
        for node_type, type_results in by_type.items():
            context_parts.append(f"\n## {node_type}s ({len(type_results)} found)")
            
            for result in type_results[:5]:
                attrs = [f"{k}={v}" for k, v in result.node_data.items() if k != "node_type" and v]
                attrs_str = ", ".join(attrs[:5])
                hop_info = f" (hops: {len(result.hop_path)})" if len(result.hop_path) > 1 else ""
                context_parts.append(f"- {result.node_id}: {attrs_str}{hop_info}")
        
        return "\n".join(context_parts)

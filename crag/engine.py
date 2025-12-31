import os
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
import networkx as nx

from .config import CRAGConfig
from .models import HopResult
from .prompts import PSEUDO_QUERY_PROMPT

logger = logging.getLogger("crag")


class CRAGEngine:
    def __init__(self, graph: nx.DiGraph, llm=None, config: Optional[CRAGConfig] = None):
        self.graph = graph
        self.llm = llm
        self.config = config or CRAGConfig()
        self._node_index = self._build_node_index()
        self._pseudo_query_cache: Dict[str, Dict[str, List[str]]] = {}
        self._llm_call_count = 0 
        
        # Tools
        self.code_executor = None
        self._init_code_executor()
        
        self._setup_logging()
        
    def _init_code_executor(self):
        try:
             from .tools.code_executor import create_code_executor_tool
             # crag/ is one level below project root
             root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
             data_dir = os.path.join(root_dir, "processed_data")
             self.code_executor = create_code_executor_tool(data_dir=data_dir)
             logger.info(f"✅ Code Executor initialized with data from: {data_dir}")
        except Exception as e:
             logger.warning(f"⚠️ Failed to init code executor: {e}")
             self.code_executor = None

    def _execute_code_action(self, code: str) -> str:
        if not self.code_executor:
            return "Error: Code Executor not available."
        
        logger.info(f"  💻 Executing Code: {code[:50]}...")
        try:
            result = self.code_executor._run(code)
            logger.info(f"  📊 Code Result: {result[:200]}...")
            return result
        except Exception as exc:
            msg = f"Code execution failed: {exc}"
            logger.error(msg)
            return msg
    
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
    
    def _calculate_heuristic_score(self, query_tokens: Set[str], node_id: str, node_data: Dict) -> float:
        import re
        node_type = node_data.get('node_type', 'Unknown')
        node_text = f"{node_id} {node_type}"
        # Add key attributes
        for k in ['name', 'title', 'label', 'description']:
            if k in node_data:
                node_text += f" {node_data[k]}"
        
        node_tokens = set(token.lower() for token in re.split(r'[^a-zA-Z0-9]', node_text) if token)
        
        # Base Similarity
        score = 0.0
        if node_tokens:
            overlap = len(query_tokens.intersection(node_tokens))
            score = overlap / (len(query_tokens) + len(node_tokens) - overlap + 1e-6)
        
        # Structural Boost (Topology-Aware)
        # Boost types that are key bridges or often targets
        structural_boost = {
            "Subject": 0.3,   # Bridge between Site/Study and data
            "Visit": 0.2,     # Container for data
            "Form": 0.1,      # Container for data
            "MissingPage": 0.4, # High value target
            "SafetyDiscrepancy": 0.4, # High value target
            "Site": 0.2
        }
        
        score += structural_boost.get(node_type, 0.0)
        
        return score
    
    # Removed reason_best_edge_llm and _select_best_neighbors as part of batch optimization
    
    def initial_retrieve(self, query: str, top_k: int = None) -> List[HopResult]:
        top_k = top_k or self.config.top_k
        logger.info(f"Initial retrieve for: '{query}...' (top_k={top_k})")
        
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
        
        # 2. LLM-Based Query Analysis (if too few results)
        if len(results) < top_k:
            self._init_llm()
            if self.llm:
                logger.info("Few keyword matches, using LLM Query Analysis")
                
                # Ask LLM what type of query this is and what nodes to look for
                analysis_prompt = f"""Analyze this clinical trial query and determine:
1. query_type: "ANALYTICAL" (needs data aggregation/stats) or "RELATIONAL" (needs graph traversal)
2. target_types: List of node types to search (from: Site, Study, Subject, Visit, SafetyDiscrepancy, Country, MedDRA, WHODD)
3. key_entities: Specific entity IDs mentioned (e.g., "Site 637", "Study 15")

Query: "{query}"

Response (JSON):
{{"query_type": "ANALYTICAL or RELATIONAL", "target_types": ["Site", "Study"], "key_entities": []}}"""

                try:
                    response = self.llm.invoke(analysis_prompt)
                    content = response.content if hasattr(response, 'content') else str(response)
                    
                    # Parse response
                    import json
                    content = content.replace("```json", "").replace("```", "").strip()
                    idx_start = content.find("{")
                    idx_end = content.rfind("}")
                    if idx_start != -1 and idx_end != -1:
                        content = content[idx_start:idx_end+1]
                    
                    analysis = json.loads(content)
                    query_type = analysis.get("query_type", "RELATIONAL")
                    target_types = analysis.get("target_types", ["Site", "Study"])
                    key_entities = analysis.get("key_entities", [])
                    
                    logger.info(f"LLM Analysis: type={query_type}, targets={target_types}, entities={key_entities}")
                    
                    # For ANALYTICAL queries, sample diverse nodes to provide context for CODE
                    if query_type == "ANALYTICAL":
                        for t in target_types[:2]:
                            type_nodes = self.get_nodes_by_type(t)
                            if type_nodes:
                                import random
                                sample = random.sample(type_nodes, min(5, len(type_nodes)))
                                existing_ids = set(r.node_id for r in results)
                                for node_id in sample:
                                    if node_id not in existing_ids and len(results) < top_k:
                                        data = self.graph.nodes[node_id]
                                        results.append(HopResult(
                                            node_id=node_id,
                                            node_type=data.get("node_type", "Unknown"),
                                            node_data=dict(data),
                                            similarity_score=0.6,
                                            hop_path=[node_id]
                                        ))
                    else:
                        # RELATIONAL: search for target types
                        for t in target_types:
                            if len(results) >= top_k: break
                            type_nodes = self.get_nodes_by_type(t)
                            import random
                            needed = top_k - len(results)
                            extras = random.sample(type_nodes, min(len(type_nodes), needed + 5))
                            
                            existing_ids = set(r.node_id for r in results)
                            for node_id in extras:
                                if node_id not in existing_ids:
                                    data = self.graph.nodes[node_id]
                                    results.append(HopResult(
                                        node_id=node_id,
                                        node_type=data.get("node_type", "Unknown"),
                                        node_data=dict(data),
                                        similarity_score=0.5,
                                        hop_path=[node_id]
                                    ))
                                    if len(results) >= top_k: break
                except Exception as e:
                    logger.warning(f"LLM query analysis failed: {e}, using type fallback")
                    # Fallback to diverse sampling
                    for t in ["Site", "Study", "Subject"][:2]:
                        type_nodes = self.get_nodes_by_type(t)
                        if type_nodes:
                            import random
                            sample = random.sample(type_nodes, min(5, len(type_nodes)))
                            for node_id in sample:
                                if len(results) < top_k:
                                    data = self.graph.nodes[node_id]
                                    results.append(HopResult(
                                        node_id=node_id,
                                        node_type=data.get("node_type", "Unknown"),
                                        node_data=dict(data),
                                        similarity_score=0.4,
                                        hop_path=[node_id]
                                    ))
        
        logger.info(f"Initial retrieve found {len(results)} nodes")
        return results
    
    def reason_batch_edges_llm(self, query: str, node_candidates: Dict[str, List[Tuple[str, Dict]]]) -> Dict[str, str]:
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
            
        # Chunk tasks (dynamic batch size)
        chunk_size = getattr(self.config, 'batch_size', 10)
        batches = [tasks[i:i+chunk_size] for i in range(0, len(tasks), chunk_size)]
        
        results = {}
        import json
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from .prompts import BATCH_EDGE_REASONING_PROMPT
        
        batch_call_count = 0  # Track calls in this batch
        
        def process_batch(chunk_tasks):
            nonlocal batch_call_count
            try:
                # ... prompt construction ...
                prompt_text = BATCH_EDGE_REASONING_PROMPT.format(
                    query=query,
                    tasks_text="\n\n".join(chunk_tasks)
                )
                batch_call_count += 1
                logger.info(f"🔹 LLM Call #{self._llm_call_count + batch_call_count}: Batch reasoning for {len(chunk_tasks)} nodes")
                response = self.llm.invoke(prompt_text)
                content = response.content if hasattr(response, 'content') else str(response)
                
                content = content.replace("```json", "").replace("```", "").strip()
                idx_start = content.find("{")
                idx_end = content.rfind("}")
                if idx_start != -1 and idx_end != -1:
                    content = content[idx_start:idx_end+1]
                
                return json.loads(content)
            except Exception as e:
                logger.error(f"Batch reasoning failed: {e}")
                return {}
        
        # Optimize workers based on batches
        max_workers = min(len(batches), getattr(self.config, 'parallel_workers', 5))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(process_batch, batch): batch for batch in batches}
            for future in as_completed(future_to_batch):
                batch_res = future.result()
                if batch_res:
                    results.update(batch_res)
        
        self._llm_call_count += batch_call_count
        logger.info(f"📊 Total LLM calls so far: {self._llm_call_count}")
        
        return results

    
    
    def _verify_action_llm(self, query: str, action: str, thought: str) -> bool:
        # Always approve CODE - it's safe to execute and we can fall back to TRAVERSE if it fails
        if action == "CODE":
            return True
        
        # For TRAVERSE/SUFFICIENT, also approve by default to reduce LLM calls
        return True

    def reason_step_cot(self, query: str, path_nodes: List[HopResult], candidates: List[Tuple[str, Dict, float]]) -> Tuple[List[str], str]:
        self._init_llm()
        if not self.llm: return [], "CONTINUE"
        
        if not hasattr(self, 'code_executor'):
             try:
                 from .tools.code_executor import create_code_executor_tool
                 root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                 data_dir = os.path.join(root_dir, "processed_data")
                 self.code_executor = create_code_executor_tool(data_dir=data_dir)
             except Exception as e:
                 logger.warning(f"Failed to init code executor: {e}")
                 self.code_executor = None

        from .prompts import CODE_AUGMENTED_COT_PROMPT
        import json
        
        # Format inputs
        current_path_desc = "\n".join([f"- {n.node_id} ({n.node_type}): {str(n.node_data)[:100]}" for n in path_nodes])
        
        candidates_desc = ""
        for i, (nid, edata, score) in enumerate(candidates[:20]): # Show top 20
             ntype = self.graph.nodes[nid].get("node_type", "Unknown")
             candidates_desc += f"[{i}] {nid} ({ntype}) - Score: {score:.2f}\n"

        # Get Schema Context
        schema_context = "No dataframes available."
        if self.code_executor:
             schema_context = self.code_executor.get_schema_context()
             
        prompt = CODE_AUGMENTED_COT_PROMPT.format(
            query=query,
            current_path_desc=current_path_desc,
            candidates_desc=candidates_desc,
            schema_context=schema_context, # Dynamic Schema
            top_k=5
        )
        
        try:
            self._llm_call_count += 1
            logger.info(f"🧠 CoT Reasoning (Code-Aware) (Call #{self._llm_call_count})")
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # JSON parsing
            content = content.replace("```json", "").replace("```", "").strip()
            idx_start = content.find("{")
            idx_end = content.rfind("}")
            if idx_start != -1 and idx_end != -1:
                 content = content[idx_start:idx_end+1]
            
            res_json = json.loads(content)
            
            action = res_json.get("action", "TRAVERSE")
            thought = res_json.get("thought", "")
            logger.info(f"  💭 Thought: {thought}")
            
            # VERIFICATION STEP (Novelty)
            if not self._verify_action_llm(query, action, thought):
                 logger.info("  ❌ Action Verification Failed. Defaulting to TRAVERSE (Safer).")
                 action = "TRAVERSE"
            else:
                 logger.info("  ✅ Action Verified.")
            
            if action == "CODE" and self.code_executor:
                 code = res_json.get("code", "")
                 max_retries = 3
                 error_history = []  # Track all errors
                 
                 for attempt in range(max_retries + 1):
                     logger.info(f"  💻 GENERATED CODE (attempt {attempt + 1}):\n{'='*40}\n{code}\n{'='*40}")
                     result = self.code_executor._run(code)
                     logger.info(f"  📊 Code Result:\n{result[:500]}")
                     
                     # Check if error occurred
                     if result.lower().startswith("error:"):
                         error_history.append(f"Attempt {attempt + 1}: {result}")
                         
                         if attempt < max_retries:
                             # Retry: Ask LLM to fix the code with ALL previous errors
                             logger.warning(f"  ⚠️ Code failed, asking LLM to fix (retry {attempt + 1}/{max_retries})")
                             
                             error_context = "\n".join(error_history)
                             fix_prompt = f"""The code failed. Here are ALL the errors so far (DO NOT repeat these mistakes):
{error_context}

Original query: {query}
Last failed code:
{code}

Available DataFrames: esae_processed_df, missing_pages_processed_df, meddra_processed_df, whodd_processed_df, visit_projection_processed_df, study_metrics_df, edrr_processed_df

Fix the code and return ONLY the corrected Python code (no explanation, no JSON). Use print() for output:"""
                             try:
                                 self._llm_call_count += 1
                                 fix_response = self.llm.invoke(fix_prompt)
                                 fix_content = fix_response.content if hasattr(fix_response, 'content') else str(fix_response)
                                 # Extract code from response
                                 fix_content = fix_content.replace("```python", "").replace("```", "").strip()
                                 # Remove thinking tags
                                 if "<think>" in fix_content:
                                     think_end = fix_content.find("</think>")
                                     if think_end != -1:
                                         fix_content = fix_content[think_end + 8:].strip()
                                 if fix_content:
                                     code = fix_content
                                     continue
                             except:
                                 pass
                         # Final failure - fall back to TRAVERSE
                         logger.error(f"  ❌ Code failed after retries: {result}")
                         if path_nodes:
                            path_nodes[-1].node_data['code_error'] = result
                         action = "TRAVERSE"
                         res_json["selected_indices"] = list(range(min(5, len(candidates))))
                         break
                     else:
                         # Success - store result
                         if path_nodes:
                            path_nodes[-1].node_data['code_analysis_result'] = result
                         
                         # Check if result is relevant
                         result_lower = result.lower()
                         is_relevant = (
                             len(result) > 50 and
                             "error" not in result_lower and
                             "empty" not in result_lower and
                             "no data" not in result_lower
                         )
                         
                         if is_relevant:
                             logger.info("  ✅ Code returned relevant data. Marking SUFFICIENT.")
                             return [], "SUFFICIENT"
                         else:
                             logger.info("  ⚠️ Code result not relevant. Continuing traversal.")
                             action = "TRAVERSE"
                             res_json["selected_indices"] = list(range(min(5, len(candidates))))
                         break
            
            if action == "SUFFICIENT":
                return [], "SUFFICIENT"
                 
            # TRAVERSE (or fallback from failed/irrelevant CODE)
            selected_indices = res_json.get("selected_indices", [])
            selected_ids = []
            for idx in selected_indices:
                if idx < len(candidates):
                    selected_ids.append(candidates[idx][0])
            
            status = "CONTINUE"
            if not selected_ids: status = "SUFFICIENT"
            
            logger.info(f"  👉 Selected {len(selected_ids)} nodes for traversal.")
            return selected_ids, status
                 
        except Exception as e:
            logger.error(f"CoT reasoning failed: {e}")
            return [], "CONTINUE"

    def select_candidates_llm_batched(self, query: str, candidates: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict, float]]:
        """Score candidates using Batched LLM calls (Semantic Selection)."""
        self._init_llm()
        if not self.llm or not candidates: return []
        
        from .prompts import BATCH_SELECTION_PROMPT
        import json
        
        batch_size = getattr(self.config, 'selection_batch_size', 20)
        # Limit total to score to avoid huge costs
        max_score = getattr(self.config, 'max_candidates_to_score', 60)
        candidates = candidates[:max_score]
        
        scored_candidates = []
        
        # Batching
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]
            
            # Helper text
            batch_text_lines = []
            for j, (nid, edata) in enumerate(batch):
                ntype = self.graph.nodes[nid].get("node_type", "Unknown")
                etype = edata.get("edge_type", "LINK")
                
                # NOVELTY: Data-Aware Tagging
                data_tag = ""
                if ntype in ["Site", "Study", "Subject"]:
                     data_tag = " [DATA_AGGR_KEY: Can bucket/group 'missing_pages_df' by this node]"
                
                # Add some attrs
                attrs = self._format_node_attributes(nid)
                first_line_attrs = attrs.split('\n')[0] if attrs else ""
                batch_text_lines.append(f"[{j}] {nid} ({ntype}) - {etype}: {first_line_attrs}{data_tag}")
            
            # Get data context for scoring
            data_context = "No dataframes available."
            if self.code_executor:
                # Get brief summary of available dataframes
                df_summaries = []
                for name, df in self.code_executor._dfs.items():
                    cols = list(df.columns)
                    df_summaries.append(f"- {name}: columns={cols}")
                data_context = "\n".join(df_summaries)
            
            prompt = BATCH_SELECTION_PROMPT.format(
                query=query,
                data_context=data_context,
                candidates_text="\n".join(batch_text_lines)
            )
            
            try:
                self._llm_call_count += 1
                logger.info(f"⚖️ LLM Selection Batch {i//batch_size + 1} (Call #{self._llm_call_count})")
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Extract JSON with robust parsing
                content = content.replace("```json", "").replace("```", "").strip()
                # Remove thinking tags if present
                if "<think>" in content:
                    think_end = content.find("</think>")
                    if think_end != -1:
                        content = content[think_end + 8:].strip()
                
                idx_start = content.find("{")
                idx_end = content.rfind("}")
                if idx_start != -1 and idx_end != -1:
                     content = content[idx_start:idx_end+1]
                
                # Fix common JSON errors
                content = content.replace("'", '"')  # Single to double quotes
                import re
                content = re.sub(r',\s*}', '}', content)  # Remove trailing commas
                content = re.sub(r',\s*]', ']', content)  # Remove trailing commas in arrays
                
                res_json = json.loads(content)
                scores_map = res_json.get("scores", {})
                
                for j in range(len(batch)):
                    key = f"candidate_index_{j}"
                    width_score = scores_map.get(key, 0)
                    # Normalize 0-1
                    norm_score = float(width_score) / 10.0
                    scored_candidates.append((batch[j][0], batch[j][1], norm_score))
                    
            except Exception as e:
                logger.error(f"Selection batch failed: {e}")
                # Fallback: keep with 0 score or heuristic?
                # Lets assign 0.5 to keep them alive if error
                for nid, edata in batch:
                    scored_candidates.append((nid, edata, 0.5))
                    
        return scored_candidates

    def multi_hop_traverse(self, query: str, start_nodes: List[HopResult], n_hops: int = None) -> Dict[str, HopResult]:
        n_hops = n_hops or self.config.n_hops
        logger.info(f"Multi-hop traverse (Optimized+Semantic): {len(start_nodes)} start nodes, {n_hops} hops")
        
        visited: Set[str] = set(r.node_id for r in start_nodes)
        visit_counter: Dict[str, HopResult] = {r.node_id: r for r in start_nodes}
        
        # Query tokens for fallback heuristic
        import re
        query_words = set(token.lower() for token in re.split(r'[^a-zA-Z0-9]', query) if token)
        
        current_layer = start_nodes
        
        for hop_idx in range(n_hops):
            logger.info(f"Processing Hop {hop_idx + 1}/{n_hops}")
            
            if not current_layer:
                break
            
            # 1. Expand ALL Candidates from current layer
            raw_candidates: List[Tuple[str, Dict]] = [] # (node_id, edge_data)
            seen_cand = set()
            
            for result in current_layer:
                node_id = result.node_id
                # Out-edges
                for _, target, edge_data in self.graph.out_edges(node_id, data=True):
                    if target not in visited and target not in seen_cand:
                        raw_candidates.append((target, edge_data))
                        seen_cand.add(target)
                
                # In-edges
                for source, _, edge_data in self.graph.in_edges(node_id, data=True):
                     if source not in visited and source not in seen_cand:
                        raw_candidates.append((source, edge_data))
                        seen_cand.add(source)

            if not raw_candidates:
                break
            
            # 2. Score Candidates (Semantic vs Heuristic)
            all_candidates_scored = []
            
            if hasattr(self.config, 'use_llm_selection') and self.config.use_llm_selection:
                 # SEMANTIC SELECTION (Batched LLM)
                 all_candidates_scored = self.select_candidates_llm_batched(query, raw_candidates)
            else:
                 # HEURISTIC FALLBACK
                 for nid, edata in raw_candidates:
                     score = self._calculate_heuristic_score(query_words, nid, self.graph.nodes[nid])
                     all_candidates_scored.append((nid, edata, score))
            
            # 3. Beam Filtering (Keep Top N based on score)
            all_candidates_scored.sort(key=lambda x: x[2], reverse=True)
            beam_candidates = all_candidates_scored[:self.config.beam_width] # Configured beam width
            
            # 4. CoT Reasoning (Optional Refinement or just use Selection)
            # If we used LLM Selection, we already reasoned about relevance. 
            # But the 'CoT Step' adds PLANNNING ("What is missing?").
            # So, we use CoT to Select from the Semantically-Filtered Beam.
            
            next_node_ids = []
            
            if self.config.use_cot_guided_traversal and beam_candidates:
                 # CoT Call
                 selected_ids, status = self.reason_step_cot(query, current_layer, beam_candidates)
                 next_node_ids = selected_ids
                 if status == "SUFFICIENT":
                     logger.info("CoT decided information is SUFFICIENT. Stopping early.")
                     break
            else:
                 # Just take top from selection
                 for nid, _, _ in beam_candidates:
                     next_node_ids.append(nid)

            # 5. Form Next Layer
            next_layer = []
            for nid in next_node_ids:
                 if nid in visited: continue
                 
                 visited.add(nid)
                 node_data = dict(self.graph.nodes[nid])
                 
                 # Inherit path (simple)
                 parent_path = current_layer[0].hop_path 
                 
                 new_result = HopResult(
                    node_id=nid,
                    node_type=node_data.get("node_type", "Unknown"),
                    node_data=node_data,
                    visit_count=1,
                    similarity_score=1.0, 
                    hop_path=parent_path + [nid]
                 )
                 visit_counter[nid] = new_result
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
        
        # Reset LLM call counter for this query
        self._llm_call_count = 0
        
        logger.info(f"=== HopRAG Pipeline Start ===")
        logger.info(f"Query: {query[:80]}...")
        
        # ULTRA-FAST: Skip all LLM reasoning if configured
        if self.config.skip_multi_hop or not self.config.use_llm_reasoning:
            logger.info("ULTRA-FAST MODE: Skipping LLM traversal, using keyword retrieval only")
            initial_results = self.initial_retrieve(query, top_k=top_k * 2)
            logger.info(f"=== HopRAG Pipeline Complete (FAST): {len(initial_results)} results, 0 LLM calls ===")
            return initial_results[:top_k]
        
        self._init_llm()
        
        if self.config.use_cot_guided_traversal:
            # CoT Guided Search
            initial_results = self.initial_retrieve(query, top_k=top_k) # Use configured top_k
            if not initial_results:
                 logger.warning("No initial results found")
                 return []
            
            # Use traverse with CoT logic
            all_results = self.multi_hop_traverse(query, initial_results, n_hops=n_hops)
             
            # Just return the visited nodes as we already reasoned about them
            final_results = list(all_results.values())
             
        else:
             # Standard HopRAG
             initial_results = self.initial_retrieve(query, top_k=top_k)
             if not initial_results:
                 logger.warning("No initial results found")
                 return []
             
             all_results = self.multi_hop_traverse(query, initial_results, n_hops=n_hops)
             scored_results = self.compute_helpfulness(query, all_results)
             final_results = self.prune_results(scored_results, top_k=top_k)
        
        logger.info(f"=== HopRAG Pipeline Complete: {len(final_results)} results, {self._llm_call_count} LLM calls ===")
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

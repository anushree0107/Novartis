"""
Unit Tester Agent (UT)
CHESS Agent 4: Selects the best SQL candidate using unit tests

Tools:
1. generate_unit_test - Generate unit tests to differentiate candidates
2. evaluate - Evaluate candidates against unit tests
"""
from typing import Dict, Any, List, Optional
import time

from agents.base_agent import BaseAgent, BaseTool, AgentResult, ToolResult
from database.connection import DatabaseManager, db_manager
from utils.llm_client import GroqLLMClient
from config.settings import MODELS


# ============== TOOLS ==============

class GenerateUnitTestTool(BaseTool):
    """
    Tool: generate_unit_test
    Generates unit tests designed to differentiate between candidate queries.
    Tests highlight semantic differences between candidates.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="generate_unit_test",
            description="Generate unit tests to differentiate SQL candidates",
            llm_client=llm_client
        )
    
    def execute(
        self,
        question: str,
        candidates: List[Dict],
        num_tests: int = 5
    ) -> ToolResult:
        """
        Generate unit tests for candidate evaluation
        
        Args:
            question: Original natural language question
            candidates: List of SQL candidate dicts
            num_tests: Number of unit tests to generate
        """
        # Format candidates for the prompt
        candidates_text = ""
        for i, cand in enumerate(candidates):
            candidates_text += f"\n--- Candidate {i+1} ({cand.get('strategy', 'unknown')}) ---\n"
            candidates_text += f"{cand.get('sql', 'N/A')}\n"
        
        system_prompt = """You are a SQL testing expert.
Generate unit tests that can differentiate between SQL query candidates.

Good unit tests:
1. Check if the query returns the expected type of data
2. Verify column names and data types
3. Test edge cases (empty results, NULL handling)
4. Check aggregation correctness
5. Verify filtering logic
6. Test JOIN correctness

Each test should be a clear statement that only the correct query should pass.

Return JSON with an array of test objects."""

        user_content = f"""Generate {num_tests} unit tests for these SQL candidates:

QUESTION: {question}

CANDIDATE QUERIES:
{candidates_text}

Generate unit tests that would help identify the correct query.
Focus on tests that highlight differences between the candidates.

Return JSON:
{{
    "unit_tests": [
        {{
            "id": 1,
            "test_description": "Description of what this test checks",
            "expected_behavior": "What the correct query should do",
            "test_type": "columns|aggregation|filter|join|result_type"
        }},
        ...
    ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_generator'),
            json_mode=True,
            max_tokens=1500
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error="Failed to generate unit tests"
            )
        
        result = self.llm.extract_json(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        unit_tests = result.get('unit_tests', []) if result else []
        
        return ToolResult(
            success=len(unit_tests) > 0,
            data={"unit_tests": unit_tests},
            tool_name=self.name,
            tokens_used=tokens,
            error=None if unit_tests else "No unit tests generated"
        )


class EvaluateTool(BaseTool):
    """
    Tool: evaluate
    Evaluates candidate queries against a unit test.
    Determines which candidates pass each test.
    """
    
    def __init__(self, llm_client: GroqLLMClient, db: DatabaseManager = None):
        super().__init__(
            name="evaluate",
            description="Evaluate SQL candidates against a unit test",
            llm_client=llm_client
        )
        self.db = db or db_manager
    
    def execute(
        self,
        candidates: List[Dict],
        unit_test: Dict,
        question: str
    ) -> ToolResult:
        """
        Evaluate candidates against a single unit test
        
        Args:
            candidates: List of SQL candidate dicts
            unit_test: Unit test to evaluate against
            question: Original question for context
        """
        # Format candidates with execution results
        candidates_text = ""
        for i, cand in enumerate(candidates):
            sql = cand.get('sql', '')
            preview = cand.get('result_preview', {})
            
            candidates_text += f"\n--- Candidate {i+1} ---\n"
            candidates_text += f"SQL: {sql}\n"
            candidates_text += f"Valid: {cand.get('is_valid', False)}\n"
            
            if preview:
                candidates_text += f"Columns: {preview.get('columns', [])}\n"
                candidates_text += f"Row count: {preview.get('row_count', 0)}\n"
                if preview.get('sample_rows'):
                    candidates_text += f"Sample: {preview['sample_rows'][:2]}\n"
        
        system_prompt = """You are a SQL testing expert evaluating query candidates.
For each candidate, determine if it passes the given unit test.

Consider:
1. Does the query structure match what the test expects?
2. Would the query produce the expected results?
3. Does the query correctly implement the required logic?

Be strict but fair in evaluation.
Return your evaluation as JSON."""

        user_content = f"""Evaluate these SQL candidates against the unit test:

ORIGINAL QUESTION: {question}

UNIT TEST:
- Description: {unit_test.get('test_description', '')}
- Expected behavior: {unit_test.get('expected_behavior', '')}
- Test type: {unit_test.get('test_type', 'general')}

CANDIDATES:
{candidates_text}

For each candidate, determine if it PASSES or FAILS this test.

Return JSON:
{{
    "evaluations": [
        {{
            "candidate_index": 0,
            "passes": true/false,
            "reasoning": "Why it passes or fails"
        }},
        ...
    ],
    "best_for_test": <index of best candidate for this test>
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('evaluator'),
            json_mode=True,
            max_tokens=1000
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error="Failed to evaluate candidates"
            )
        
        result = self.llm.extract_json(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=result is not None,
            data=result or {"evaluations": [], "best_for_test": None},
            tool_name=self.name,
            tokens_used=tokens
        )


# ============== AGENT ==============

class UnitTesterAgent(BaseAgent):
    """
    Agent 4: Unit Tester (UT)
    
    Selects the best SQL candidate by:
    - Generating unit tests that differentiate candidates
    - Evaluating each candidate against the tests
    - Scoring candidates based on tests passed
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        db: DatabaseManager = None,
        **kwargs
    ):
        self.db = db or db_manager
        super().__init__(llm_client, model=MODELS.get('evaluator'), **kwargs)
        self.name = "UnitTester"
    
    def _register_tools(self):
        """Register UT agent tools"""
        self.add_tool(GenerateUnitTestTool(self.llm))
        self.add_tool(EvaluateTool(self.llm, self.db))
    
    def get_system_prompt(self) -> str:
        return """You are a Unit Tester agent for SQL synthesis.
Your job is to select the best SQL query from candidates using unit tests."""

    # Simple in-memory cache for UT results
    _ut_cache = {}

    def execute(
        self,
        question: str,
        candidates: List[Dict],
        num_tests: int = 5
    ) -> AgentResult:
        """
        Execute UT agent pipeline in parallel:
        1. Generate unit tests for candidates
        2. Evaluate each candidate against tests (parallelized)
        3. Score and rank candidates
        4. Select the best candidate
        Uses a simple cache to avoid recomputation.
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        start_time = time.time()
        tool_calls = []
        total_tokens = 0

        # Filter to valid candidates only for testing
        valid_candidates = [c for c in candidates if c.get('is_valid', False)]

        cache_key = (question.strip().lower(), str(valid_candidates), num_tests)
        if cache_key in self._ut_cache:
            cached = self._ut_cache[cache_key]
            cached.execution_time = time.time() - start_time
            return cached

        # If only one valid candidate, return it directly
        if len(valid_candidates) == 1:
            self.log("Only one valid candidate, selecting directly", "success")
            agent_result = AgentResult(
                success=True,
                data={
                    'selected_sql': valid_candidates[0]['sql'],
                    'selected_candidate': valid_candidates[0],
                    'selection_method': 'single_valid',
                    'scores': {0: 1.0}
                },
                reasoning="Single valid candidate selected",
                tokens_used=0,
                execution_time=time.time() - start_time,
                tool_calls=[]
            )
            self._ut_cache[cache_key] = agent_result
            return agent_result

        # If no valid candidates, try to select best invalid one
        if len(valid_candidates) == 0:
            self.log("No valid candidates, selecting best effort", "warning")
            if candidates:
                agent_result = AgentResult(
                    success=True,
                    data={
                        'selected_sql': candidates[0]['sql'],
                        'selected_candidate': candidates[0],
                        'selection_method': 'best_effort',
                        'scores': {}
                    },
                    reasoning="No valid candidates, best effort selection",
                    tokens_used=0,
                    execution_time=time.time() - start_time,
                    tool_calls=[]
                )
                self._ut_cache[cache_key] = agent_result
                return agent_result
            agent_result = AgentResult(
                success=False,
                data=None,
                error="No candidates available",
                execution_time=time.time() - start_time
            )
            self._ut_cache[cache_key] = agent_result
            return agent_result

        # Step 1: Generate unit tests
        self.log(f"Generating {num_tests} unit tests for {len(valid_candidates)} candidates...")

        tests_result = self.call_tool(
            "generate_unit_test",
            question=question,
            candidates=valid_candidates,
            num_tests=num_tests
        )
        tool_calls.append(tests_result)
        total_tokens += tests_result.tokens_used

        if not tests_result.success or not tests_result.data.get('unit_tests'):
            # Fallback: select first valid candidate
            self.log("Unit test generation failed, selecting first valid candidate", "warning")
            agent_result = AgentResult(
                success=True,
                data={
                    'selected_sql': valid_candidates[0]['sql'],
                    'selected_candidate': valid_candidates[0],
                    'selection_method': 'fallback_first_valid',
                    'scores': {}
                },
                reasoning="Fallback selection (test generation failed)",
                tokens_used=total_tokens,
                execution_time=time.time() - start_time,
                tool_calls=tool_calls
            )
            self._ut_cache[cache_key] = agent_result
            return agent_result

        unit_tests = tests_result.data['unit_tests']
        self.log(f"Generated {len(unit_tests)} unit tests")

        # Step 2: Evaluate candidates against each test in parallel
        scores = {i: 0 for i in range(len(valid_candidates))}
        evaluation_details = []

        def eval_test(test):
            self.log(f"Evaluating against: {test.get('test_description', 'test')[:50]}...")
            eval_result = self.call_tool(
                "evaluate",
                candidates=valid_candidates,
                unit_test=test,
                question=question
            )
            return (test, eval_result)

        with ThreadPoolExecutor(max_workers=min(4, len(unit_tests))) as executor:
            futures = [executor.submit(eval_test, test) for test in unit_tests]
            for future in as_completed(futures):
                test, eval_result = future.result()
                tool_calls.append(eval_result)
                total_tokens += eval_result.tokens_used
                if eval_result.success and eval_result.data.get('evaluations'):
                    for evaluation in eval_result.data['evaluations']:
                        idx = evaluation.get('candidate_index', 0)
                        if evaluation.get('passes', False) and idx < len(valid_candidates):
                            scores[idx] += 1
                    evaluation_details.append({
                        'test': test,
                        'evaluations': eval_result.data['evaluations']
                    })

        # Step 3: Select best candidate based on scores
        best_idx = max(scores, key=scores.get)
        best_candidate = valid_candidates[best_idx]

        self.log(f"Selected candidate {best_idx + 1} with score {scores[best_idx]}/{len(unit_tests)}", "success")

        agent_result = AgentResult(
            success=True,
            data={
                'selected_sql': best_candidate['sql'],
                'selected_candidate': best_candidate,
                'selection_method': 'unit_test_scoring',
                'scores': scores,
                'max_score': len(unit_tests),
                'unit_tests': unit_tests,
                'evaluations': evaluation_details
            },
            reasoning=f"Selected candidate {best_idx + 1} with score {scores[best_idx]}/{len(unit_tests)} "
                     f"({scores[best_idx]/len(unit_tests)*100:.0f}%)",
            tokens_used=total_tokens,
            execution_time=time.time() - start_time,
            tool_calls=tool_calls
        )
        self._ut_cache[cache_key] = agent_result
        return agent_result

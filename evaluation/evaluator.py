"""
Text-to-SQL Evaluation Module
Evaluates the system using the testbench without requiring ground truth SQL
"""
import json
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case"""
    test_id: int
    question: str
    difficulty: str
    success: bool
    generated_sql: Optional[str] = None
    actual_answer: Any = None
    expected_answer: Any = None
    answer_matches: bool = False
    execution_success: bool = False
    error: Optional[str] = None
    time_taken: float = 0.0
    tokens_used: int = 0


@dataclass
class EvaluationSummary:
    """Summary of all evaluation results"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    execution_errors: int = 0
    by_difficulty: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_category: Dict[str, Dict[str, int]] = field(default_factory=dict)
    avg_time: float = 0.0
    total_tokens: int = 0


class TestbenchEvaluator:
    """Evaluates Text-to-SQL system against testbench"""
    
    def __init__(self, testbench_path: str = None):
        if testbench_path is None:
            testbench_path = os.path.join(
                os.path.dirname(__file__), 
                "testbench.json"
            )
        
        with open(testbench_path, 'r') as f:
            self.testbench = json.load(f)
        
        self.results: List[EvaluationResult] = []
        
    def load_pipeline(self):
        """Load the Text-to-SQL pipeline"""
        from pipeline.orchestrator import create_pipeline
        self.pipeline = create_pipeline(verbose=False)
        
    def compare_answers(
        self, 
        expected: Any, 
        actual: Any, 
        answer_type: str,
        tolerance: float = 0.01
    ) -> bool:
        """Compare expected and actual answers based on type"""
        
        if expected == "varies":
            # For dynamic answers, just check if we got something
            return actual is not None
        
        if answer_type == "single_value":
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                return abs(expected - actual) <= tolerance
            return str(expected).lower() == str(actual).lower()
        
        elif answer_type == "boolean":
            if isinstance(actual, bool):
                return expected == actual
            # Check if result indicates true/false
            if actual in [0, None, [], '']:
                return expected == False
            return expected == True
        
        elif answer_type == "list":
            if not isinstance(actual, (list, set)):
                return False
            expected_set = set(str(x).upper() for x in expected)
            actual_set = set(str(x).upper() for x in actual)
            return expected_set == actual_set
        
        elif answer_type == "ordered_list":
            if not isinstance(actual, list):
                return False
            if len(expected) != len(actual):
                return False
            return all(
                str(e).upper() == str(a).upper() 
                for e, a in zip(expected, actual)
            )
        
        elif answer_type == "key_value_pairs":
            if not isinstance(actual, dict):
                return False
            # Check if keys match and values are close
            for key, value in expected.items():
                if key not in actual:
                    return False
                if isinstance(value, (int, float)):
                    if abs(value - actual[key]) > tolerance:
                        return False
            return True
        
        elif answer_type == "comparison":
            # For comparison types, just verify we got a valid answer
            return actual is not None
        
        elif answer_type == "table":
            # For table results, verify structure
            return isinstance(actual, (list, dict)) and len(actual) > 0
        
        return False
    
    def extract_answer_from_result(self, result, answer_type: str) -> Any:
        """Extract the answer value from pipeline result"""
        if not result.execution_result or not result.execution_result.get('success'):
            return None
        
        data = result.execution_result.get('data', [])
        if not data:
            return None
        
        if answer_type == "single_value":
            # Get first value from first row
            first_row = data[0]
            if isinstance(first_row, dict):
                return list(first_row.values())[0]
            return first_row
        
        elif answer_type == "boolean":
            first_row = data[0]
            if isinstance(first_row, dict):
                val = list(first_row.values())[0]
                return val > 0 if isinstance(val, (int, float)) else bool(val)
            return bool(first_row)
        
        elif answer_type in ["list", "ordered_list"]:
            # Extract single column as list
            result_list = []
            for row in data:
                if isinstance(row, dict):
                    result_list.append(list(row.values())[0])
                else:
                    result_list.append(row)
            return result_list
        
        elif answer_type == "key_value_pairs":
            # Extract as dict (assumes 2 columns: key, value)
            result_dict = {}
            for row in data:
                if isinstance(row, dict):
                    values = list(row.values())
                    if len(values) >= 2:
                        result_dict[values[0]] = values[1]
            return result_dict
        
        elif answer_type == "table":
            return data
        
        return data
    
    def run_single_test(self, test_case: Dict) -> EvaluationResult:
        """Run a single test case"""
        import time
        
        start_time = time.time()
        
        result = EvaluationResult(
            test_id=test_case['id'],
            question=test_case['question'],
            difficulty=test_case['difficulty'],
            success=False,
            expected_answer=test_case['expected_answer']
        )
        
        try:
            pipeline_result = self.pipeline.run(
                question=test_case['question'],
                num_candidates=3,
                num_unit_tests=3,
                execute_result=True,
                explain_result=False
            )
            
            result.generated_sql = pipeline_result.sql
            result.tokens_used = pipeline_result.total_tokens
            result.execution_success = (
                pipeline_result.execution_result is not None and 
                pipeline_result.execution_result.get('success', False)
            )
            
            if result.execution_success:
                result.actual_answer = self.extract_answer_from_result(
                    pipeline_result,
                    test_case.get('answer_type', 'single_value')
                )
                
                tolerance = test_case.get('tolerance', 0.01)
                result.answer_matches = self.compare_answers(
                    test_case['expected_answer'],
                    result.actual_answer,
                    test_case.get('answer_type', 'single_value'),
                    tolerance
                )
                
                result.success = result.answer_matches
            else:
                result.error = pipeline_result.error or "Execution failed"
                
        except Exception as e:
            result.error = str(e)
        
        result.time_taken = time.time() - start_time
        return result
    
    def run_evaluation(
        self, 
        difficulty_filter: List[str] = None,
        category_filter: List[str] = None,
        test_ids: List[int] = None
    ) -> EvaluationSummary:
        """Run full evaluation against testbench"""
        
        self.load_pipeline()
        
        test_cases = self.testbench['test_cases']
        
        # Apply filters
        if difficulty_filter:
            test_cases = [t for t in test_cases if t['difficulty'] in difficulty_filter]
        if category_filter:
            test_cases = [t for t in test_cases if t['category'] in category_filter]
        if test_ids:
            test_cases = [t for t in test_cases if t['id'] in test_ids]
        
        self.results = []
        summary = EvaluationSummary(total_tests=len(test_cases))
        
        console.print(Panel.fit(
            f"[bold]Running {len(test_cases)} test cases[/bold]",
            title="Evaluation"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Evaluating...", total=len(test_cases))
            
            for test_case in test_cases:
                progress.update(
                    task, 
                    description=f"Test {test_case['id']}: {test_case['question'][:40]}..."
                )
                
                result = self.run_single_test(test_case)
                self.results.append(result)
                
                # Update summary
                if result.success:
                    summary.passed += 1
                else:
                    summary.failed += 1
                
                if not result.execution_success:
                    summary.execution_errors += 1
                
                summary.total_tokens += result.tokens_used
                
                # By difficulty
                diff = result.difficulty
                if diff not in summary.by_difficulty:
                    summary.by_difficulty[diff] = {'passed': 0, 'failed': 0, 'total': 0}
                summary.by_difficulty[diff]['total'] += 1
                if result.success:
                    summary.by_difficulty[diff]['passed'] += 1
                else:
                    summary.by_difficulty[diff]['failed'] += 1
                
                # By category
                cat = test_case.get('category', 'unknown')
                if cat not in summary.by_category:
                    summary.by_category[cat] = {'passed': 0, 'failed': 0, 'total': 0}
                summary.by_category[cat]['total'] += 1
                if result.success:
                    summary.by_category[cat]['passed'] += 1
                else:
                    summary.by_category[cat]['failed'] += 1
                
                progress.advance(task)
        
        # Calculate averages
        total_time = sum(r.time_taken for r in self.results)
        summary.avg_time = total_time / len(self.results) if self.results else 0
        
        return summary
    
    def print_results(self, summary: EvaluationSummary):
        """Print evaluation results"""
        
        # Overall summary
        pass_rate = (summary.passed / summary.total_tests * 100) if summary.total_tests > 0 else 0
        
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]Passed: {summary.passed}/{summary.total_tests} ({pass_rate:.1f}%)[/bold green]\n"
            f"[bold red]Failed: {summary.failed}[/bold red]\n"
            f"[yellow]Execution Errors: {summary.execution_errors}[/yellow]\n"
            f"[dim]Avg Time: {summary.avg_time:.2f}s | Total Tokens: {summary.total_tokens}[/dim]",
            title="📊 Evaluation Summary"
        ))
        
        # By difficulty
        table = Table(title="Results by Difficulty")
        table.add_column("Difficulty")
        table.add_column("Passed")
        table.add_column("Failed")
        table.add_column("Pass Rate")
        
        for diff in ['easy', 'medium', 'hard']:
            if diff in summary.by_difficulty:
                stats = summary.by_difficulty[diff]
                rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
                table.add_row(
                    diff.capitalize(),
                    str(stats['passed']),
                    str(stats['failed']),
                    f"{rate:.1f}%"
                )
        
        console.print(table)
        
        # By category
        table2 = Table(title="Results by Category")
        table2.add_column("Category")
        table2.add_column("Passed")
        table2.add_column("Failed")
        table2.add_column("Pass Rate")
        
        for cat, stats in sorted(summary.by_category.items()):
            rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            table2.add_row(
                cat,
                str(stats['passed']),
                str(stats['failed']),
                f"{rate:.1f}%"
            )
        
        console.print(table2)
        
        # Failed tests details
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            console.print("\n[bold red]Failed Test Cases:[/bold red]")
            for r in failed_results[:10]:  # Show first 10
                console.print(f"  [{r.difficulty}] Q{r.test_id}: {r.question[:50]}...")
                if r.error:
                    console.print(f"    Error: {r.error[:80]}")
                else:
                    console.print(f"    Expected: {r.expected_answer}")
                    console.print(f"    Got: {r.actual_answer}")
    
    def save_results(self, filepath: str = None):
        """Save results to JSON file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                os.path.dirname(__file__),
                f"results_{timestamp}.json"
            )
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "test_id": r.test_id,
                    "question": r.question,
                    "difficulty": r.difficulty,
                    "success": r.success,
                    "generated_sql": r.generated_sql,
                    "expected_answer": r.expected_answer,
                    "actual_answer": r.actual_answer,
                    "answer_matches": r.answer_matches,
                    "execution_success": r.execution_success,
                    "error": r.error,
                    "time_taken": r.time_taken,
                    "tokens_used": r.tokens_used
                }
                for r in self.results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        console.print(f"\n[green]Results saved to {filepath}[/green]")


def main():
    """CLI for running evaluation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate Text-to-SQL system")
    parser.add_argument("--difficulty", "-d", nargs="+", 
                        choices=["easy", "medium", "hard"],
                        help="Filter by difficulty")
    parser.add_argument("--category", "-c", nargs="+",
                        help="Filter by category")
    parser.add_argument("--ids", "-i", nargs="+", type=int,
                        help="Run specific test IDs")
    parser.add_argument("--save", "-s", action="store_true",
                        help="Save results to file")
    
    args = parser.parse_args()
    
    evaluator = TestbenchEvaluator()
    
    summary = evaluator.run_evaluation(
        difficulty_filter=args.difficulty,
        category_filter=args.category,
        test_ids=args.ids
    )
    
    evaluator.print_results(summary)
    
    if args.save:
        evaluator.save_results()


if __name__ == "__main__":
    main()

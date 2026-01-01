#!/usr/bin/env python
"""
SAGE-BENCH Evaluation Runner
============================
Run Text-to-SQL evaluation tests with flexible options.

Usage:
    python -m sage_bench.run_evaluation --easy              # Run only easy tests
    python -m sage_bench.run_evaluation --medium            # Run only medium tests
    python -m sage_bench.run_evaluation --hard              # Run only hard tests
    python -m sage_bench.run_evaluation --all               # Run all tests
    python -m sage_bench.run_evaluation --easy --medium     # Run easy and medium
    python -m sage_bench.run_evaluation --ids 1 2 3         # Run specific test IDs
    python -m sage_bench.run_evaluation --ids 1-5           # Run test IDs 1 to 5
    python -m sage_bench.run_evaluation --category count    # Run tests by category
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# Path to testbench
TESTBENCH_PATH = Path(__file__).parent / "new_testbench.json"
RESULTS_DIR = Path(__file__).parent / "results"


@dataclass
class TestResult:
    """Result of a single test case"""
    test_id: int
    question: str
    difficulty: str
    category: str
    expected_answer: Any
    actual_answer: Any
    generated_sql: str
    passed: bool
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


@dataclass
class EvaluationSummary:
    """Summary of evaluation results"""
    total_tests: int
    passed: int
    failed: int
    accuracy: float
    by_difficulty: Dict[str, Dict[str, int]]
    by_category: Dict[str, Dict[str, int]]
    total_time: float
    total_tokens: int


def load_testbench() -> Dict:
    """Load the SAGE-BENCH testbench"""
    if not TESTBENCH_PATH.exists():
        console.print(f"[red]Error: Testbench not found at {TESTBENCH_PATH}[/red]")
        sys.exit(1)
    
    with open(TESTBENCH_PATH, 'r') as f:
        return json.load(f)


def get_tests_by_difficulty(testbench: Dict, difficulties: List[str]) -> List[Dict]:
    """Get tests filtered by difficulty levels"""
    tests = []
    for difficulty in difficulties:
        if difficulty in testbench.get('tests', {}):
            tests.extend(testbench['tests'][difficulty])
    return tests


def get_tests_by_ids(testbench: Dict, test_ids: List[int]) -> List[Dict]:
    """Get tests by specific IDs"""
    all_tests = []
    for difficulty in ['easy', 'medium', 'hard']:
        if difficulty in testbench.get('tests', {}):
            all_tests.extend(testbench['tests'][difficulty])
    
    return [t for t in all_tests if t['id'] in test_ids]


def get_tests_by_category(testbench: Dict, categories: List[str]) -> List[Dict]:
    """Get tests filtered by category"""
    all_tests = []
    for difficulty in ['easy', 'medium', 'hard']:
        if difficulty in testbench.get('tests', {}):
            all_tests.extend(testbench['tests'][difficulty])
    
    return [t for t in all_tests if t.get('category') in categories]


def parse_id_range(id_str: str) -> List[int]:
    """Parse ID range like '1-5' or single ID '3'"""
    if '-' in id_str:
        start, end = id_str.split('-')
        return list(range(int(start), int(end) + 1))
    return [int(id_str)]


def compare_answers(expected: Any, actual: Any, expected_type: str, tolerance: float = None) -> bool:
    """Compare expected and actual answers with type awareness"""
    if actual is None:
        return False
    
    if expected_type == "number":
        try:
            expected_num = float(expected)
            actual_num = float(actual)
            if tolerance:
                return abs(expected_num - actual_num) <= tolerance
            return expected_num == actual_num
        except (ValueError, TypeError):
            return False
    
    elif expected_type == "percentage":
        try:
            expected_num = float(expected)
            actual_num = float(actual)
            tol = tolerance if tolerance else 0.5
            return abs(expected_num - actual_num) <= tol
        except (ValueError, TypeError):
            return False
    
    elif expected_type == "string":
        return str(expected).lower().strip() == str(actual).lower().strip()
    
    elif expected_type == "list":
        if not isinstance(actual, list):
            return False
        expected_set = set(str(e).lower().strip() for e in expected)
        actual_set = set(str(a).lower().strip() for a in actual)
        return expected_set == actual_set
    
    return str(expected) == str(actual)


def run_single_test(pipeline, test: Dict) -> TestResult:
    """Run a single test case"""
    import time
    
    start_time = time.time()
    
    try:
        result = pipeline.run(
            test['question'],
            num_candidates=3,
            execute_result=True,
            explain_result=False,
            disable_unit_test=True
        )
        
        execution_time = time.time() - start_time
        
        # Extract actual answer from result
        actual_answer = None
        if result.execution_result and result.execution_result.get('data'):
            data = result.execution_result['data']
            if len(data) == 1 and len(data[0]) == 1:
                actual_answer = data[0][0]
            elif len(data) == 1:
                actual_answer = data[0][0] if data[0] else None
            else:
                # Multiple rows - return as list
                actual_answer = [row[0] for row in data if row]
        
        # Compare answers
        passed = compare_answers(
            test['expected_answer'],
            actual_answer,
            test['expected_type'],
            test.get('tolerance')
        )
        
        return TestResult(
            test_id=test['id'],
            question=test['question'],
            difficulty=test['difficulty'],
            category=test['category'],
            expected_answer=test['expected_answer'],
            actual_answer=actual_answer,
            generated_sql=result.sql,
            passed=passed,
            execution_time=execution_time,
            tokens_used=result.total_tokens
        )
        
    except Exception as e:
        return TestResult(
            test_id=test['id'],
            question=test['question'],
            difficulty=test['difficulty'],
            category=test['category'],
            expected_answer=test['expected_answer'],
            actual_answer=None,
            generated_sql="",
            passed=False,
            error=str(e),
            execution_time=time.time() - start_time
        )


def run_evaluation(tests: List[Dict], verbose: bool = True) -> tuple[List[TestResult], EvaluationSummary]:
    """Run evaluation on a list of tests"""
    from chess_sql import create_pipeline
    
    # Create pipeline
    console.print("\n[bold blue]Initializing CHESS Pipeline...[/bold blue]")
    pipeline = create_pipeline(verbose=False)
    
    results: List[TestResult] = []
    total_tokens = 0
    total_time = 0.0
    
    # Progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running tests...", total=len(tests))
        
        for test in tests:
            progress.update(task, description=f"[cyan]Test {test['id']}: {test['question'][:40]}...")
            
            result = run_single_test(pipeline, test)
            results.append(result)
            
            total_tokens += result.tokens_used
            total_time += result.execution_time
            
            # Show result indicator
            status = "[green]✓[/green]" if result.passed else "[red]✗[/red]"
            if verbose:
                console.print(f"  {status} Test {test['id']}: {'PASSED' if result.passed else 'FAILED'}")
            
            progress.advance(task)
    
    # Calculate summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    by_difficulty = {}
    by_category = {}
    
    for r in results:
        # By difficulty
        if r.difficulty not in by_difficulty:
            by_difficulty[r.difficulty] = {'passed': 0, 'failed': 0}
        if r.passed:
            by_difficulty[r.difficulty]['passed'] += 1
        else:
            by_difficulty[r.difficulty]['failed'] += 1
        
        # By category
        if r.category not in by_category:
            by_category[r.category] = {'passed': 0, 'failed': 0}
        if r.passed:
            by_category[r.category]['passed'] += 1
        else:
            by_category[r.category]['failed'] += 1
    
    summary = EvaluationSummary(
        total_tests=len(results),
        passed=passed,
        failed=failed,
        accuracy=passed / len(results) * 100 if results else 0,
        by_difficulty=by_difficulty,
        by_category=by_category,
        total_time=total_time,
        total_tokens=total_tokens
    )
    
    return results, summary


def display_results(results: List[TestResult], summary: EvaluationSummary):
    """Display evaluation results in a formatted table"""
    
    # Results table
    table = Table(title="SAGE-BENCH Evaluation Results", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Difficulty", width=8)
    table.add_column("Category", width=15)
    table.add_column("Status", width=8)
    table.add_column("Expected", width=15)
    table.add_column("Actual", width=15)
    table.add_column("Time (s)", width=8)
    
    for r in results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(
            str(r.test_id),
            r.difficulty,
            r.category,
            status,
            str(r.expected_answer)[:15],
            str(r.actual_answer)[:15] if r.actual_answer else "N/A",
            f"{r.execution_time:.2f}"
        )
    
    console.print(table)
    
    # Summary panel
    summary_text = f"""
**Overall Accuracy:** {summary.accuracy:.1f}% ({summary.passed}/{summary.total_tests})

**By Difficulty:**
"""
    for diff, stats in summary.by_difficulty.items():
        total = stats['passed'] + stats['failed']
        acc = stats['passed'] / total * 100 if total > 0 else 0
        summary_text += f"- {diff.capitalize()}: {stats['passed']}/{total} ({acc:.1f}%)\n"
    
    summary_text += f"""
**Metrics:**
- Total Time: {summary.total_time:.2f}s
- Total Tokens: {summary.total_tokens:,}
- Avg Time/Test: {summary.total_time / summary.total_tests:.2f}s
"""
    
    console.print(Panel(Markdown(summary_text), title="📊 Summary", border_style="green"))


def save_results(results: List[TestResult], summary: EvaluationSummary, output_path: Optional[str] = None):
    """Save results to JSON file"""
    RESULTS_DIR.mkdir(exist_ok=True)
    
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = RESULTS_DIR / f"evaluation_{timestamp}.json"
    else:
        output_path = Path(output_path)
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'summary': asdict(summary),
        'results': [asdict(r) for r in results]
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    console.print(f"\n[dim]Results saved to: {output_path}[/dim]")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="SAGE-BENCH: SQL Accuracy and Generation Evaluation Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m sage_bench.run_evaluation --easy              # Run easy tests only
  python -m sage_bench.run_evaluation --medium --hard     # Run medium and hard tests
  python -m sage_bench.run_evaluation --all               # Run all tests
  python -m sage_bench.run_evaluation --ids 1 2 3         # Run specific test IDs
  python -m sage_bench.run_evaluation --ids 1-5 10-15     # Run ID ranges
  python -m sage_bench.run_evaluation --category count    # Run by category
  python -m sage_bench.run_evaluation --list              # List all available tests
        """
    )
    
    # Difficulty filters
    parser.add_argument('--easy', action='store_true', help='Run easy difficulty tests')
    parser.add_argument('--medium', action='store_true', help='Run medium difficulty tests')
    parser.add_argument('--hard', action='store_true', help='Run hard difficulty tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    # ID-based selection
    parser.add_argument('--ids', nargs='+', help='Run specific test IDs (e.g., 1 2 3 or 1-5)')
    
    # Category filter
    parser.add_argument('--category', nargs='+', help='Run tests by category')
    
    # Other options
    parser.add_argument('--list', action='store_true', help='List all available tests')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to file')
    
    args = parser.parse_args()
    
    # Load testbench
    testbench = load_testbench()
    
    # List tests mode
    if args.list:
        console.print(Panel(f"[bold]{testbench['name']}[/bold]\n{testbench['description']}", 
                           title="SAGE-BENCH", border_style="blue"))
        
        table = Table(title="Available Tests", show_header=True)
        table.add_column("ID", width=4)
        table.add_column("Difficulty", width=10)
        table.add_column("Category", width=15)
        table.add_column("Question", width=50)
        
        for difficulty in ['easy', 'medium', 'hard']:
            for test in testbench.get('tests', {}).get(difficulty, []):
                table.add_row(
                    str(test['id']),
                    difficulty,
                    test['category'],
                    test['question'][:50]
                )
        
        console.print(table)
        return
    
    # Determine which tests to run
    tests = []
    
    if args.all:
        tests = get_tests_by_difficulty(testbench, ['easy', 'medium', 'hard'])
    elif args.ids:
        # Parse ID arguments (support ranges like 1-5)
        test_ids = []
        for id_arg in args.ids:
            test_ids.extend(parse_id_range(id_arg))
        tests = get_tests_by_ids(testbench, test_ids)
    elif args.category:
        tests = get_tests_by_category(testbench, args.category)
    else:
        # Filter by difficulty flags
        difficulties = []
        if args.easy:
            difficulties.append('easy')
        if args.medium:
            difficulties.append('medium')
        if args.hard:
            difficulties.append('hard')
        
        if difficulties:
            tests = get_tests_by_difficulty(testbench, difficulties)
        else:
            # Default: show help
            parser.print_help()
            console.print("\n[yellow]Please specify which tests to run (--easy, --medium, --hard, --all, or --ids)[/yellow]")
            return
    
    if not tests:
        console.print("[red]No tests found matching the specified criteria[/red]")
        return
    
    # Display header
    console.print(Panel(
        f"[bold blue]SAGE-BENCH Evaluation[/bold blue]\n"
        f"Running {len(tests)} test(s)...",
        border_style="blue"
    ))
    
    # Run evaluation
    results, summary = run_evaluation(tests, verbose=not args.quiet)
    
    # Display results
    if not args.quiet:
        display_results(results, summary)
    else:
        console.print(f"\n[bold]Accuracy: {summary.accuracy:.1f}% ({summary.passed}/{summary.total_tests})[/bold]")
    
    # Save results
    if not args.no_save:
        save_results(results, summary, args.output)


if __name__ == "__main__":
    main()

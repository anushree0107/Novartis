"""
Test runner for new_testbench.json
Runs tests one by one with delays to avoid rate limits
"""
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.orchestrator import CHESSPipeline
from rich.console import Console
from rich.table import Table

console = Console()

def load_testbench():
    """Load the new testbench"""
    with open("evaluation/new_testbench.json", "r") as f:
        return json.load(f)

def extract_answer(result):
    """Extract the answer from query result"""
    if not result or not result.get('results'):
        return None
    
    rows = result['results']
    if not rows:
        return None
    
    # Get first row, first value
    first_row = rows[0]
    if isinstance(first_row, dict):
        values = list(first_row.values())
        if values:
            return values[0]
    return first_row

def compare_answers(expected, actual, expected_type, tolerance=None):
    """Compare expected and actual answers"""
    if actual is None:
        return False
    
    if expected_type == "number":
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            if tolerance:
                return abs(actual_num - expected_num) <= tolerance
            return actual_num == expected_num
        except:
            return False
    
    elif expected_type == "string":
        return str(actual).strip().lower() == str(expected).strip().lower()
    
    elif expected_type == "list":
        if isinstance(actual, list):
            return all(str(e).lower() in [str(a).lower() for a in actual] for e in expected)
        return False
    
    elif expected_type == "percentage":
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            tol = tolerance or 1.0
            return abs(actual_num - expected_num) <= tol
        except:
            return False
    
    return str(actual) == str(expected)

def run_single_test(pipeline, test, verbose=True):
    """Run a single test"""
    question = test["question"]
    expected = test["expected_answer"]
    expected_type = test["expected_type"]
    tolerance = test.get("tolerance")
    
    if verbose:
        console.print(f"\n[bold cyan]Test {test['id']}:[/bold cyan] {question}")
        console.print(f"[dim]Expected: {expected} ({expected_type})[/dim]")
    
    try:
        result = pipeline.run(question, explain_result=False)
        actual = extract_answer(result)
        passed = compare_answers(expected, actual, expected_type, tolerance)
        
        if verbose:
            status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
            console.print(f"Actual: {actual}")
            console.print(f"SQL: {result.get('sql', 'N/A')[:100]}...")
            console.print(status)
        
        return {
            "test_id": test["id"],
            "question": question,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "sql": result.get("sql", ""),
            "error": None
        }
    
    except Exception as e:
        if verbose:
            console.print(f"[red]ERROR: {e}[/red]")
        return {
            "test_id": test["id"],
            "question": question,
            "expected": expected,
            "actual": None,
            "passed": False,
            "sql": "",
            "error": str(e)
        }

def run_tests(difficulty="easy", delay_seconds=30, max_tests=None):
    """Run tests of specified difficulty"""
    testbench = load_testbench()
    tests = testbench["tests"].get(difficulty, [])
    
    if max_tests:
        tests = tests[:max_tests]
    
    console.print(f"\n[bold]Running {len(tests)} {difficulty} tests[/bold]")
    console.print(f"[dim]Delay between tests: {delay_seconds}s[/dim]\n")
    
    pipeline = CHESSPipeline()
    results = []
    
    for i, test in enumerate(tests):
        if i > 0 and delay_seconds > 0:
            console.print(f"\n[yellow]Waiting {delay_seconds}s to avoid rate limit...[/yellow]")
            time.sleep(delay_seconds)
        
        result = run_single_test(pipeline, test)
        results.append(result)
    
    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    console.print("\n" + "=" * 60)
    console.print(f"[bold]SUMMARY: {passed}/{total} passed ({100*passed/total:.0f}%)[/bold]")
    console.print("=" * 60)
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "difficulty": difficulty,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{100*passed/total:.1f}%"
        },
        "results": results
    }
    
    output_path = f"evaluation/test_results_{difficulty}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    console.print(f"\nResults saved to: {output_path}")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run testbench")
    parser.add_argument("--difficulty", "-d", default="easy", choices=["easy", "medium", "hard", "all"])
    parser.add_argument("--delay", type=int, default=30, help="Delay between tests in seconds")
    parser.add_argument("--max", "-m", type=int, default=None, help="Max tests to run")
    
    args = parser.parse_args()
    
    if args.difficulty == "all":
        for diff in ["easy", "medium", "hard"]:
            run_tests(diff, args.delay, args.max)
    else:
        run_tests(args.difficulty, args.delay, args.max)

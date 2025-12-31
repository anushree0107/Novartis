"""
Run easy tests from testbench on new processed data schema
"""
import json
import time
from datetime import datetime
from database.connection import db_manager
from pipeline.orchestrator import ChessPipeline
from rich.console import Console
from rich.table import Table

console = Console()

# Load testbench
with open('evaluation/testbench.json', 'r') as f:
    testbench = json.load(f)

# Get easy tests only
easy_tests = [t for t in testbench['test_cases'] if t['difficulty'] == 'easy']

console.print(f"\n[bold]Found {len(easy_tests)} easy tests[/bold]\n")

# Initialize pipeline
pipeline = ChessPipeline()

results = []

for i, test in enumerate(easy_tests):
    console.print(f"\n{'='*60}")
    console.print(f"[bold cyan]Test {test['id']}: {test['question']}[/bold cyan]")
    console.print(f"Expected: {test['expected_answer']}")
    console.print('='*60)
    
    try:
        result = pipeline.run(test['question'], explain_result=False)
        
        actual = result.get('result')
        sql = result.get('sql', '')
        
        # Extract actual value
        if actual and len(actual) > 0:
            if isinstance(actual[0], dict):
                actual_value = list(actual[0].values())[0]
            else:
                actual_value = actual[0]
        else:
            actual_value = None
        
        console.print(f"\n[green]SQL:[/green] {sql[:200]}...")
        console.print(f"[green]Result:[/green] {actual_value}")
        
        # Check pass
        expected = test['expected_answer']
        passed = False
        if expected == 'varies':
            passed = actual_value is not None and actual_value > 0
        elif isinstance(expected, bool):
            passed = bool(actual_value) == expected
        elif isinstance(expected, list):
            if isinstance(actual_value, list):
                passed = set(actual_value) == set(expected)
            else:
                passed = False
        else:
            passed = actual_value == expected
        
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        console.print(f"\nStatus: {status}")
        
        results.append({
            'test_id': test['id'],
            'question': test['question'],
            'expected': expected,
            'actual': actual_value,
            'passed': passed,
            'sql': sql
        })
        
    except Exception as e:
        console.print(f"[red]ERROR: {e}[/red]")
        results.append({
            'test_id': test['id'],
            'question': test['question'],
            'expected': test['expected_answer'],
            'actual': None,
            'passed': False,
            'error': str(e)
        })
    
    # Wait between tests to avoid rate limit
    if i < len(easy_tests) - 1:
        console.print("\n[yellow]Waiting 90 seconds to avoid rate limit...[/yellow]")
        time.sleep(90)

# Summary
console.print("\n" + "="*60)
console.print("[bold]SUMMARY[/bold]")
console.print("="*60)

passed = sum(1 for r in results if r['passed'])
total = len(results)
console.print(f"Passed: {passed}/{total} ({100*passed/total:.0f}%)")

# Save results
output = {
    'timestamp': datetime.now().isoformat(),
    'schema': 'processed_data',
    'summary': {'passed': passed, 'total': total},
    'results': results
}

with open('evaluation/easy_test_results_new.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

console.print("\nResults saved to evaluation/easy_test_results_new.json")

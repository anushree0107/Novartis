"""
Simple batch test runner - runs tests with 90s delays
Save results after each test
"""
import json
import time
import subprocess
import re
from datetime import datetime

def run_query(question):
    """Run a query and extract the result"""
    cmd = [
        r".\novartis\Scripts\python.exe",
        "-m", "cli.main", "query",
        question,
        "--no-explain"
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,
            cwd=r"c:\Users\agniv\OneDrive\Documents\Nova-text-to-sql"
        )
        output = result.stdout + result.stderr
        
        # Extract SQL
        sql_match = re.search(r'Generated SQL:\s*\n(.*?)\n\nResults:', output, re.DOTALL)
        sql = sql_match.group(1).strip() if sql_match else ""
        
        # Clean SQL - remove line numbers
        sql_lines = []
        for line in sql.split('\n'):
            # Remove leading line numbers like "  1 " or " 10 "
            cleaned = re.sub(r'^\s*\d+\s+', '', line)
            sql_lines.append(cleaned)
        sql = '\n'.join(sql_lines)
        
        # Extract result value - look for the table content
        # Pattern for single value in table
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if '│' in line and '┃' not in line:
                # This might be a data row
                val = line.replace('│', '').strip()
                if val and not val.startswith('─') and val not in ['Query Results', 'rows)']:
                    try:
                        return int(val), sql
                    except:
                        return val, sql
        
        return None, sql
        
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    except Exception as e:
        return None, str(e)

def main():
    # Load testbench
    with open("evaluation/new_testbench.json") as f:
        testbench = json.load(f)
    
    medium_tests = testbench['tests']['medium']
    
    # Load existing results if any
    results_file = "evaluation/medium_results_batch.json"
    try:
        with open(results_file) as f:
            results = json.load(f)
    except:
        results = {"tests": [], "summary": {}}
    
    # Find which tests are already done
    done_ids = {r['id'] for r in results.get('tests', [])}
    
    print(f"Found {len(medium_tests)} medium tests, {len(done_ids)} already completed")
    
    for test in medium_tests:
        if test['id'] in done_ids:
            print(f"Skipping test {test['id']} (already done)")
            continue
        
        print(f"\n{'='*60}")
        print(f"Test {test['id']}: {test['question']}")
        print(f"Expected: {test['expected_answer']}")
        print("="*60)
        
        actual, sql = run_query(test['question'])
        
        # Compare
        passed = False
        if actual is not None:
            if test['expected_type'] == 'number':
                try:
                    passed = int(actual) == int(test['expected_answer'])
                except:
                    passed = False
            else:
                passed = str(actual).lower().strip() == str(test['expected_answer']).lower().strip()
        
        status = "PASS" if passed else "FAIL"
        print(f"Actual: {actual}")
        print(f"Status: {status}")
        print(f"SQL: {sql[:80]}...")
        
        # Save result
        results['tests'].append({
            "id": test['id'],
            "question": test['question'],
            "expected": test['expected_answer'],
            "actual": actual,
            "passed": passed,
            "sql": sql,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update summary
        passed_count = sum(1 for r in results['tests'] if r['passed'])
        results['summary'] = {
            "total": len(results['tests']),
            "passed": passed_count,
            "failed": len(results['tests']) - passed_count,
            "pass_rate": f"{100*passed_count//len(results['tests'])}%"
        }
        
        # Save after each test
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nProgress: {results['summary']['passed']}/{results['summary']['total']} passed")
        
        # Wait before next test
        if test['id'] < len(medium_tests):
            print(f"\nWaiting 90 seconds before next test...")
            time.sleep(90)
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    for r in results['tests']:
        status = "✓" if r['passed'] else "✗"
        print(f"{status} Test {r['id']}: {r['question'][:40]}... -> {r['actual']} (expected {r['expected']})")
    
    print(f"\nPass Rate: {results['summary']['pass_rate']}")

if __name__ == "__main__":
    main()

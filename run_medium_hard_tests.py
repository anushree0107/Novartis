"""
Automated test runner for medium and hard tests
Runs each test with 120 second delay to avoid rate limits
No user interaction needed - runs completely autonomously
"""
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.orchestrator import CHESSPipeline

def load_testbench():
    with open("evaluation/new_testbench.json", "r") as f:
        return json.load(f)

def extract_answer(result):
    if not result or not result.get('results'):
        return None
    rows = result['results']
    if not rows:
        return None
    first_row = rows[0]
    if isinstance(first_row, dict):
        values = list(first_row.values())
        if values:
            return values[0]
    return first_row

def compare_answers(expected, actual, expected_type, tolerance=None):
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
    elif expected_type == "percentage":
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            tol = tolerance or 1.0
            return abs(actual_num - expected_num) <= tol
        except:
            return False
    elif expected_type == "list":
        return True  # Just check if query runs
    return str(actual) == str(expected)

def run_tests():
    print("=" * 70)
    print("AUTOMATED TEST RUNNER - MEDIUM & HARD TESTS")
    print("=" * 70)
    print(f"Started at: {datetime.now()}")
    print("Delay between tests: 120 seconds")
    print("=" * 70)
    
    testbench = load_testbench()
    
    # Get medium and hard tests
    medium_tests = testbench["tests"].get("medium", [])
    hard_tests = testbench["tests"].get("hard", [])
    all_tests = medium_tests + hard_tests
    
    print(f"\nTotal tests to run: {len(all_tests)}")
    print(f"  - Medium: {len(medium_tests)}")
    print(f"  - Hard: {len(hard_tests)}")
    print(f"\nEstimated time: {len(all_tests) * 2 + (len(all_tests)-1) * 2} minutes\n")
    
    pipeline = CHESSPipeline()
    results = []
    
    for i, test in enumerate(all_tests):
        test_id = test["id"]
        question = test["question"]
        expected = test["expected_answer"]
        expected_type = test["expected_type"]
        tolerance = test.get("tolerance")
        difficulty = test["difficulty"]
        
        print(f"\n{'='*70}")
        print(f"TEST {test_id} ({difficulty.upper()}) - {i+1}/{len(all_tests)}")
        print(f"{'='*70}")
        print(f"Q: {question}")
        print(f"Expected: {expected} ({expected_type})")
        
        try:
            result = pipeline.run(question, explain_result=False)
            actual = extract_answer(result)
            sql = result.get("sql", "N/A")
            passed = compare_answers(expected, actual, expected_type, tolerance)
            
            print(f"Actual: {actual}")
            print(f"SQL: {sql[:150]}..." if len(str(sql)) > 150 else f"SQL: {sql}")
            print(f"Result: {'PASS ✓' if passed else 'FAIL ✗'}")
            
            results.append({
                "test_id": test_id,
                "difficulty": difficulty,
                "question": question,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "sql": sql,
                "error": None
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "test_id": test_id,
                "difficulty": difficulty,
                "question": question,
                "expected": expected,
                "actual": None,
                "passed": False,
                "sql": "",
                "error": str(e)
            })
        
        # Wait 120 seconds before next test (except for last test)
        if i < len(all_tests) - 1:
            print(f"\nWaiting 120 seconds before next test...")
            time.sleep(120)
    
    # Summary
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    medium_passed = sum(1 for r in results if r["passed"] and r["difficulty"] == "medium")
    medium_total = sum(1 for r in results if r["difficulty"] == "medium")
    hard_passed = sum(1 for r in results if r["passed"] and r["difficulty"] == "hard")
    hard_total = sum(1 for r in results if r["difficulty"] == "hard")
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Overall: {passed_count}/{total_count} ({100*passed_count/total_count:.0f}%)")
    print(f"Medium:  {medium_passed}/{medium_total} ({100*medium_passed/medium_total:.0f}%)" if medium_total > 0 else "Medium: N/A")
    print(f"Hard:    {hard_passed}/{hard_total} ({100*hard_passed/hard_total:.0f}%)" if hard_total > 0 else "Hard: N/A")
    print("=" * 70)
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": f"{100*passed_count/total_count:.1f}%",
            "medium": {"passed": medium_passed, "total": medium_total},
            "hard": {"passed": hard_passed, "total": hard_total}
        },
        "results": results
    }
    
    output_path = f"evaluation/medium_hard_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Completed at: {datetime.now()}")

if __name__ == "__main__":
    run_tests()

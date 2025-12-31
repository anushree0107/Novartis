"""
Run easy tests one by one with delays to avoid rate limiting
"""
import time
import json
from datetime import datetime
from evaluation.evaluator import TestbenchEvaluator

def run_easy_tests_sequential():
    print("=" * 60)
    print("RUNNING EASY TESTS ONE BY ONE")
    print("2 minute delay between tests to avoid rate limits")
    print("=" * 60)
    
    evaluator = TestbenchEvaluator()
    evaluator.load_pipeline()
    
    easy_tests = [t for t in evaluator.testbench['test_cases'] if t['difficulty'] == 'easy']
    results = []
    
    for i, test in enumerate(easy_tests):
        print(f"\n{'='*60}")
        print(f"TEST {test['id']} ({i+1}/{len(easy_tests)})")
        print(f"Question: {test['question']}")
        print(f"Expected: {test['expected_answer']}")
        print("=" * 60)
        
        try:
            result = evaluator.run_single_test(test)
            
            print(f"\nGenerated SQL:")
            print("-" * 40)
            print(result.generated_sql if result.generated_sql else "None")
            print("-" * 40)
            print(f"Actual Answer: {result.actual_answer}")
            print(f"PASS: {result.success}")
            if result.error:
                print(f"Error: {result.error}")
            
            results.append({
                "test_id": test['id'],
                "question": test['question'],
                "expected_answer": test['expected_answer'],
                "actual_answer": result.actual_answer,
                "pass": result.success,
                "generated_sql": result.generated_sql,
                "error": result.error,
                "time_taken": result.time_taken,
                "tokens_used": result.tokens_used
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "test_id": test['id'],
                "question": test['question'],
                "expected_answer": test['expected_answer'],
                "actual_answer": None,
                "pass": False,
                "generated_sql": None,
                "error": str(e),
                "time_taken": 0,
                "tokens_used": 0
            })
        
        # Save intermediate results
        save_results(results)
        
        # Wait 2 minutes before next test (except for last one)
        if i < len(easy_tests) - 1:
            print(f"\nWaiting 2 minutes before next test...")
            for remaining in range(120, 0, -30):
                print(f"  {remaining} seconds remaining...")
                time.sleep(30)
            print("  Continuing...")
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r['pass'])
    print(f"Passed: {passed}/{len(results)} ({100*passed/len(results):.1f}%)")
    
    for r in results:
        status = "✅ PASS" if r['pass'] else "❌ FAIL"
        print(f"  Test {r['test_id']}: {status}")
    
    return results

def save_results(results):
    """Save results to JSON file"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "description": "Easy test results - sequential run with 2min delays",
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r['pass']),
            "failed": sum(1 for r in results if not r['pass'])
        },
        "results": results
    }
    
    with open("evaluation/easy_test_results_full.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"  [Results saved to easy_test_results_full.json]")

if __name__ == "__main__":
    run_easy_tests_sequential()

"""
SAGE-BENCH: SQL Accuracy and Generation Evaluation Benchmark
============================================================
A comprehensive evaluation framework for Text-to-SQL systems on clinical trial data.

Usage:
    # Run from command line
    python -m sage_bench.run_evaluation --easy
    python -m sage_bench.run_evaluation --all
    
    # Import programmatically
    from sage_bench import run_evaluation, load_testbench
"""

from pathlib import Path

__version__ = "2.0"
__all__ = ['run_evaluation', 'load_testbench', 'TestResult', 'EvaluationSummary']

SAGE_BENCH_DIR = Path(__file__).parent
TESTBENCH_PATH = SAGE_BENCH_DIR / "new_testbench.json"


def load_testbench():
    """Load the SAGE-BENCH testbench"""
    import json
    with open(TESTBENCH_PATH, 'r') as f:
        return json.load(f)


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'run_evaluation':
        from sage_bench.run_evaluation import run_evaluation
        return run_evaluation
    elif name == 'TestResult':
        from sage_bench.run_evaluation import TestResult
        return TestResult
    elif name == 'EvaluationSummary':
        from sage_bench.run_evaluation import EvaluationSummary
        return EvaluationSummary
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


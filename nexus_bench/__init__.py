"""
NEXUS-BENCH: Natural language EXecution and Understanding System Benchmark
==========================================================================
A comprehensive evaluation framework for Text-to-SQL systems on clinical trial data.

Usage:
    # Run from command line
    python -m nexus_bench.run_evaluation --easy
    python -m nexus_bench.run_evaluation --all
    
    # Import programmatically
    from nexus_bench import run_evaluation, load_testbench
"""

from pathlib import Path

__version__ = "2.0"
__all__ = ['run_evaluation', 'load_testbench', 'TestResult', 'EvaluationSummary']

NEXUS_BENCH_DIR = Path(__file__).parent
TESTBENCH_PATH = NEXUS_BENCH_DIR / "new_testbench.json"


def load_testbench():
    """Load the NEXUS-BENCH testbench"""
    import json
    with open(TESTBENCH_PATH, 'r') as f:
        return json.load(f)


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'run_evaluation':
        from nexus_bench.run_evaluation import run_evaluation
        return run_evaluation
    elif name == 'TestResult':
        from nexus_bench.run_evaluation import TestResult
        return TestResult
    elif name == 'EvaluationSummary':
        from nexus_bench.run_evaluation import EvaluationSummary
        return EvaluationSummary
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


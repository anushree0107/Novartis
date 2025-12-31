"""
Evaluation module for Text-to-SQL system
"""

__all__ = ['TestbenchEvaluator', 'EvaluationResult', 'EvaluationSummary']

def __getattr__(name):
    """Lazy import to avoid circular import issues"""
    if name in __all__:
        from evaluation.evaluator import TestbenchEvaluator, EvaluationResult, EvaluationSummary
        return {
            'TestbenchEvaluator': TestbenchEvaluator,
            'EvaluationResult': EvaluationResult,
            'EvaluationSummary': EvaluationSummary
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


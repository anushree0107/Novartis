#!/usr/bin/env python3
"""
Run a quick query using CHESS pipeline with unit testing disabled (fast path).
Usage:
  .\novartis\Scripts\python.exe run_quick_query.py "How many studies are there in the database?"
Options:
  --no-explain    Disable natural language explanation
  --candidates N  Number of SQL candidates to generate (default 3)
  --tests N       Number of unit tests (ignored when unit tests disabled)
"""
import argparse
import json

from pipeline.orchestrator import create_pipeline


def main():
    parser = argparse.ArgumentParser(description="Quick CHESS query (unit tests disabled)")
    parser.add_argument('question', nargs='?', default='How many studies are there in the database?', help='Natural language question')
    parser.add_argument('--no-explain', action='store_true', help='Disable natural language explanation')
    parser.add_argument('--candidates', type=int, default=3, help='Number of SQL candidates to generate')
    parser.add_argument('--tests', type=int, default=5, help='Number of unit tests (ignored here)')
    args = parser.parse_args()

    pipeline = create_pipeline(verbose=False)

    result = pipeline.run(
        question=args.question,
        num_candidates=args.candidates,
        num_unit_tests=args.tests,
        execute_result=True,
        explain_result=(not args.no_explain),
        disable_unit_test=True,
    )

    print('\nSQL:')
    print(result.sql or 'None')
    print('\nTime:', result.total_time)

    er = result.execution_result or {}
    print('Row count:', er.get('row_count'))
    print('Columns:', er.get('columns'))
    print('Data (first 5 rows):')
    data = er.get('data') or []
    try:
        print(json.dumps(data[:5], indent=2, default=str))
    except Exception:
        print(data[:5])

    first_val = None
    if data and isinstance(data, list) and len(data) > 0:
        first_row = data[0]
        if isinstance(first_row, dict):
            vals = list(first_row.values())
            first_val = vals[0] if vals else None
        elif isinstance(first_row, (list, tuple)):
            first_val = first_row[0] if len(first_row) > 0 else None

    print('First row value:', first_val)


if __name__ == '__main__':
    main()

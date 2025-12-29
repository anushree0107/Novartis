"""Code Executor Tool."""

import sys
import io
import os
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import pandas as pd

try:
    from ..core.base_tool import BaseTool
except ImportError:
    from core.base_tool import BaseTool

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "processed_data")


class CodeExecutorInput(BaseModel):
    code: str = Field(description="Python/pandas code. DataFrames: edrr_df, esae_df, meddra_df, whodd_df, missing_pages_df, visit_df, study_metrics_df")


class CodeExecutorTool(BaseTool):
    name = "execute_python_code"
    description = "Execute pandas code on CSVs. DataFrames: edrr_df, esae_df, meddra_df, whodd_df, missing_pages_df, visit_df, study_metrics_df"
    
    def __init__(self, data_dir: str = None, **kwargs):
        self.data_dir = data_dir or DATA_DIR
        self._dfs: Dict[str, pd.DataFrame] = {}
        self._load()
        super().__init__(**kwargs)
    
    def _load(self):
        files = {'edrr_df': 'edrr_processed.csv', 'esae_df': 'esae_processed.csv',
                 'meddra_df': 'meddra_processed.csv', 'whodd_df': 'whodd_processed.csv',
                 'missing_pages_df': 'missing_pages_processed.csv', 'visit_df': 'visit_projection_processed.csv',
                 'study_metrics_df': 'study_metrics.csv'}
        for name, file in files.items():
            path = os.path.join(self.data_dir, file)
            if os.path.exists(path):
                try:
                    self._dfs[name] = pd.read_csv(path)
                except:
                    pass
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return CodeExecutorInput
    
    def _run(self, code: str) -> str:
        if not self._dfs:
            return f"No data from {self.data_dir}"
        old_stdout, sys.stdout = sys.stdout, io.StringIO()
        try:
            globs = {'pd': pd, **self._dfs, '__builtins__': {
                'print': print, 'len': len, 'range': range, 'enumerate': enumerate, 'zip': zip,
                'sorted': sorted, 'list': list, 'dict': dict, 'set': set, 'str': str,
                'int': int, 'float': float, 'sum': sum, 'min': min, 'max': max}}
            try:
                import numpy as np
                globs['np'] = np
            except:
                pass
            exec(code, globs)
            return sys.stdout.getvalue() or "No output"
        except Exception as e:
            return f"Error: {e}"
        finally:
            sys.stdout = old_stdout


def create_code_executor_tool(data_dir: str = None) -> CodeExecutorTool:
    return CodeExecutorTool(data_dir=data_dir)

"""Code Executor Tool."""

import sys
import io
import os
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import pandas as pd

try:
    from .base_tool import BaseTool
except ImportError:
    from .base_tool import BaseTool

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "processed_data")


class CodeExecutorInput(BaseModel):
    code: str = Field(description="Python/pandas code. Use any available DataFrame by name (shown in schema context).")


class CodeExecutorTool(BaseTool):
    name = "execute_python_code"
    description = "Execute pandas code on clinical trial data. All CSVs from processed_data are loaded as DataFrames (see schema context for names and columns)."
    
    def __init__(self, data_dir: str = None, **kwargs):
        self.data_dir = data_dir or DATA_DIR
        self._dfs: Dict[str, pd.DataFrame] = {}
        self._load()
        super().__init__(**kwargs)
    
    def _load(self):
        """Dynamically load all CSV files from the data directory."""
        if not os.path.exists(self.data_dir):
            return

        import re
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    # Sanitize filename to create a valid python variable name
                    # e.g., 'Site-Data.csv' -> 'site_data_df'
                    clean_name = os.path.splitext(filename)[0]
                    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', clean_name).lower()
                    # Append _df if not present to imply it's a dataframe
                    if not clean_name.endswith("_df"):
                        clean_name += "_df"
                    
                    df = pd.read_csv(file_path)
                    self._dfs[clean_name] = df
                    # print(f"Loaded {clean_name} from {filename}") 
                except Exception as e:
                    pass
                    
    def get_schema_context(self) -> str:
        """Generate a rich schema description with sample values."""
        if not self._dfs:
            return "No data loaded."
            
        context = []
        for name, df in self._dfs.items():
            context.append(f"### DataFrame: {name}")
            try:
                # Columns and Types
                context.append(f"- Shape: {df.shape}")
                col_info = []
                for col in df.columns:
                    # Get sample values (first 3 unique, non-null)
                    samples = df[col].dropna().unique()[:3]
                    sample_str = ", ".join(map(str, samples))
                    col_info.append(f"  * {col} ({df[col].dtype}): e.g., [{sample_str}, ...]")
                context.append("\n".join(col_info))
            except Exception as e:
                context.append(f"Error profiling {name}: {e}")
            context.append("")
            
        return "\n".join(context)
    def args_schema(self) -> Type[BaseModel]:
        return CodeExecutorInput
    
    def _run(self, code: str) -> str:
        if not self._dfs:
            return f"No data from {self.data_dir}"
        
        # Clean common LLM mistakes
        code = code.replace(".to_frame()", "")  # Series doesn't need to_frame
        code = code.replace("pd.read_csv", "# SKIP pd.read_csv")  # Already loaded
        
        # Auto-fix: If no print() in code, wrap the last expression
        if "print(" not in code:
            lines = code.strip().split("\n")
            if lines:
                last_line = lines[-1].strip()
                # If last line is an expression (not assignment, if, for, etc.)
                if not any(last_line.startswith(kw) for kw in ['if ', 'for ', 'while ', 'def ', 'class ', 'import ', '#', 'try:', 'except', 'with ']):
                    if '=' in last_line and not last_line.startswith(' '):
                        # It's an assignment, add print after
                        var_name = last_line.split('=')[0].strip()
                        lines.append(f"print({var_name})")
                    else:
                        # Wrap the expression in print
                        lines[-1] = f"print({last_line})"
                    code = "\n".join(lines)
        
        old_stdout, sys.stdout = sys.stdout, io.StringIO()
        try:
            globs = {
                'pd': pd, 
                **self._dfs, 
                '__builtins__': {
                    'print': print, 'len': len, 'range': range, 'enumerate': enumerate, 
                    'zip': zip, 'sorted': sorted, 'list': list, 'dict': dict, 'set': set, 
                    'str': str, 'int': int, 'float': float, 'sum': sum, 'min': min, 'max': max,
                    'abs': abs, 'round': round, 'any': any, 'all': all, 'bool': bool,
                    'tuple': tuple, 'type': type, 'isinstance': isinstance,
                    '__import__': __import__
                }
            }
            try:
                import numpy as np
                globs['np'] = np
            except:
                pass
            exec(code, globs)
            output = sys.stdout.getvalue()
            return output if output else "Code executed successfully (no print output)"
        except Exception as e:
            return f"Error: {e}. Check variable names match loaded DataFrames."
        finally:
            sys.stdout = old_stdout


def create_code_executor_tool(data_dir: str = None) -> CodeExecutorTool:
    return CodeExecutorTool(data_dir=data_dir)

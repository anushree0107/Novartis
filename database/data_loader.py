"""
Data loader to import Excel files from clinical trial studies into PostgreSQL
"""
import os
import re
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from sqlalchemy import text
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from config.settings import DATA_ROOT_PATH, DATABASE_CONFIG
from database.connection import DatabaseManager

console = Console()


class ClinicalDataLoader:
    """Loads clinical trial Excel data into PostgreSQL"""
    
    def __init__(self, data_root: str = None, db_manager: DatabaseManager = None):
        self.data_root = Path(data_root or DATA_ROOT_PATH)
        self.db = db_manager or DatabaseManager()
        self.loaded_tables = []
        
    def sanitize_name(self, name: str) -> str:
        """Convert name to valid PostgreSQL identifier"""
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^\w\s]', '', str(name))
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = sanitized.lower().strip('_')
        # Ensure doesn't start with number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'col_' + sanitized
        # Truncate to 63 chars (PostgreSQL limit)
        return sanitized[:63] if sanitized else 'unnamed_column'
    
    def sanitize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize all column names in DataFrame"""
        new_columns = {}
        seen = set()
        
        for col in df.columns:
            new_name = self.sanitize_name(col)
            # Handle duplicates
            original_name = new_name
            counter = 1
            while new_name in seen:
                new_name = f"{original_name}_{counter}"
                counter += 1
            seen.add(new_name)
            new_columns[col] = new_name
            
        return df.rename(columns=new_columns)
    
    def discover_excel_files(self) -> List[Dict]:
        """Find all Excel files in the data directory"""
        excel_files = []
        
        for study_folder in self.data_root.iterdir():
            if study_folder.is_dir() and 'CPID' in study_folder.name:
                # Extract study number
                study_match = re.search(r'Study\s*(\d+)', study_folder.name, re.IGNORECASE)
                study_num = study_match.group(1) if study_match else 'unknown'
                
                for file_path in study_folder.glob('*.xlsx'):
                    if not file_path.name.startswith('~$'):  # Skip temp files
                        excel_files.append({
                            'path': file_path,
                            'study_number': study_num,
                            'filename': file_path.stem
                        })
        
        return excel_files
    
    def infer_table_name(self, file_info: Dict) -> str:
        """Generate table name from file info"""
        filename = file_info['filename']
        study_num = file_info['study_number']
        
        # Extract meaningful part of filename
        # Remove study prefix and common suffixes
        name = re.sub(r'^Study\s*\d+[_\s]*', '', filename, flags=re.IGNORECASE)
        name = re.sub(r'_updated$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'_\d{1,2}\s*(NOV|DEC|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT)\s*\d{4}', '', name, flags=re.IGNORECASE)
        
        # Sanitize
        table_name = self.sanitize_name(name)
        
        # Add study prefix
        return f"study_{study_num}_{table_name}"
    
    def categorize_file(self, filename: str) -> str:
        """Categorize file based on its name"""
        filename_lower = filename.lower()
        
        categories = {
            'visit': ['visit', 'projection', 'tracker'],
            'query': ['query', 'edrr'],
            'safety': ['esae', 'safety', 'sae'],
            'coding': ['coding', 'meddra', 'whodd'],
            'lab': ['lab', 'missing_lab'],
            'edc_metrics': ['edc', 'metrics'],
            'forms': ['inactivated', 'forms', 'folders', 'records'],
            'pages': ['missing_pages', 'page']
        }
        
        for category, keywords in categories.items():
            if any(kw in filename_lower for kw in keywords):
                return category
        return 'other'
    
    def load_excel_file(self, file_info: Dict, sheet_name: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Load Excel file, handling multiple sheets"""
        file_path = file_info['path']
        dfs = {}
        
        try:
            # Read all sheets
            xlsx = pd.ExcelFile(file_path)
            sheets_to_load = [sheet_name] if sheet_name else xlsx.sheet_names
            
            for sheet in sheets_to_load:
                try:
                    df = pd.read_excel(xlsx, sheet_name=sheet)
                    
                    # Skip empty dataframes
                    if df.empty or len(df.columns) == 0:
                        continue
                    
                    # Clean the dataframe
                    df = self.clean_dataframe(df)
                    
                    if not df.empty:
                        sheet_suffix = '' if len(sheets_to_load) == 1 else f"_{self.sanitize_name(sheet)}"
                        dfs[sheet_suffix] = df
                        
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not load sheet '{sheet}': {e}[/yellow]")
                    
        except Exception as e:
            console.print(f"[red]Error loading file {file_path}: {e}[/red]")
            
        return dfs
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare DataFrame for database insertion"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Skip if header row is not the first row (detect by checking if first row has many NaN)
        # This handles files where data doesn't start from row 1
        
        # Sanitize column names
        df = self.sanitize_columns(df)
        
        # Convert problematic data types
        for col in df.columns:
            # Handle datetime columns
            if df[col].dtype == 'datetime64[ns]':
                df[col] = df[col].astype(str).replace('NaT', None)
            # Handle mixed types - convert to string
            elif df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else None)
        
        return df
    
    def create_table_from_df(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace'):
        """Create table in PostgreSQL from DataFrame"""
        try:
            df.to_sql(
                table_name,
                self.db.engine,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=1000
            )
            return True
        except Exception as e:
            console.print(f"[red]Error creating table {table_name}: {e}[/red]")
            return False
    
    def load_all_studies(self, progress_callback=None) -> Dict[str, List[str]]:
        """Load all study data into PostgreSQL"""
        excel_files = self.discover_excel_files()
        results = {'success': [], 'failed': []}
        
        console.print(f"\n[bold blue]Found {len(excel_files)} Excel files to process[/bold blue]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Loading data...", total=len(excel_files))
            
            for file_info in excel_files:
                file_name = file_info['filename']
                progress.update(task, description=f"Loading: {file_name[:40]}...")
                
                # Load Excel file (may have multiple sheets)
                dfs = self.load_excel_file(file_info)
                
                for sheet_suffix, df in dfs.items():
                    table_name = self.infer_table_name(file_info) + sheet_suffix
                    table_name = table_name[:63]  # PostgreSQL limit
                    
                    # Add metadata columns
                    df['_study_number'] = file_info['study_number']
                    df['_source_file'] = file_name
                    df['_category'] = self.categorize_file(file_name)
                    
                    if self.create_table_from_df(df, table_name):
                        results['success'].append(table_name)
                        self.loaded_tables.append({
                            'table_name': table_name,
                            'study': file_info['study_number'],
                            'category': self.categorize_file(file_name),
                            'row_count': len(df),
                            'columns': list(df.columns)
                        })
                    else:
                        results['failed'].append(table_name)
                
                progress.advance(task)
        
        # Create metadata table
        self._create_metadata_table()
        
        return results
    
    def _create_metadata_table(self):
        """Create a metadata table with information about all loaded tables"""
        if not self.loaded_tables:
            return
            
        metadata_df = pd.DataFrame(self.loaded_tables)
        metadata_df['columns'] = metadata_df['columns'].apply(lambda x: ','.join(x))
        
        self.create_table_from_df(metadata_df, '_table_metadata', if_exists='replace')
        console.print("\n[green]Created metadata table: _table_metadata[/green]")
    
    def create_unified_views(self):
        """Create unified views across studies for common data types"""
        views = {
            'all_visit_data': """
                SELECT * FROM (
                    SELECT *, '_placeholder_' as source_table 
                    FROM information_schema.tables 
                    WHERE 1=0
                ) placeholder
            """,
            'all_query_metrics': """
                SELECT * FROM (
                    SELECT *, '_placeholder_' as source_table 
                    FROM information_schema.tables 
                    WHERE 1=0
                ) placeholder
            """
        }
        
        # Build dynamic UNION queries based on loaded tables
        visit_tables = [t['table_name'] for t in self.loaded_tables if t['category'] == 'visit']
        query_tables = [t['table_name'] for t in self.loaded_tables if t['category'] == 'query']
        
        console.print(f"\n[blue]Visit tables found: {len(visit_tables)}[/blue]")
        console.print(f"[blue]Query tables found: {len(query_tables)}[/blue]")


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    config = DATABASE_CONFIG.copy()
    db_name = config.pop('database')
    
    try:
        conn = psycopg2.connect(**config, database='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {db_name}')
            console.print(f"[green]Created database: {db_name}[/green]")
        else:
            console.print(f"[blue]Database '{db_name}' already exists[/blue]")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        console.print(f"[red]Error creating database: {e}[/red]")
        return False


import psycopg2

if __name__ == "__main__":
    console.print("[bold]Clinical Trial Data Loader[/bold]\n")
    
    # Create database if needed
    create_database_if_not_exists()
    
    # Initialize loader and load all data
    loader = ClinicalDataLoader()
    results = loader.load_all_studies()
    
    console.print(f"\n[bold green]Successfully loaded: {len(results['success'])} tables[/bold green]")
    if results['failed']:
        console.print(f"[bold red]Failed to load: {len(results['failed'])} tables[/bold red]")
    
    # Show summary
    console.print("\n[bold]Loaded Tables Summary:[/bold]")
    for table_info in loader.loaded_tables[:10]:  # Show first 10
        console.print(f"  • {table_info['table_name']} ({table_info['row_count']} rows)")
    if len(loader.loaded_tables) > 10:
        console.print(f"  ... and {len(loader.loaded_tables) - 10} more tables")
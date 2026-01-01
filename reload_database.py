"""
Script to reload database with processed CSV files
"""
import os
import pandas as pd
from sqlalchemy import text
from database.connection import db_manager
from rich.console import Console
from rich.progress import Progress

console = Console()

def drop_all_tables():
    """Drop all existing tables from the database"""
    console.print("[bold red]Dropping all existing tables...[/bold red]")
    
    tables = db_manager.get_all_tables()
    console.print(f"Found {len(tables)} tables to drop")
    
    with db_manager.engine.connect() as conn:
        # Disable foreign key checks
        conn.execute(text("SET session_replication_role = 'replica';"))
        
        for table in tables:
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                console.print(f"  Dropped: {table}")
            except Exception as e:
                console.print(f"  [red]Error dropping {table}: {e}[/red]")
        
        # Re-enable foreign key checks
        conn.execute(text("SET session_replication_role = 'origin';"))
        conn.commit()
    
    console.print("[green]All tables dropped![/green]\n")

def load_csv_files(folder="processed_data"):
    """Load all CSV files from the folder into database"""
    console.print(f"[bold blue]Loading CSV files from {folder}...[/bold blue]")
    
    csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
    console.print(f"Found {len(csv_files)} CSV files")
    
    results = {'success': [], 'failed': []}
    
    with Progress() as progress:
        task = progress.add_task("Loading...", total=len(csv_files))
        
        for csv_file in csv_files:
            filepath = os.path.join(folder, csv_file)
            # Table name from filename (remove .csv extension)
            table_name = csv_file.replace('.csv', '').replace('-', '_').lower()
            
            try:
                # Read CSV
                df = pd.read_csv(filepath)
                
                # Clean column names
                df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
                
                # Load to database
                df.to_sql(
                    table_name,
                    db_manager.engine,
                    if_exists='replace',
                    index=False,
                    method='multi',
                    chunksize=1000
                )
                
                results['success'].append({
                    'table': table_name,
                    'rows': len(df),
                    'columns': len(df.columns)
                })
                console.print(f"  [green]✓[/green] {table_name}: {len(df)} rows, {len(df.columns)} columns")
                
            except Exception as e:
                results['failed'].append({'file': csv_file, 'error': str(e)})
                console.print(f"  [red]✗[/red] {csv_file}: {e}")
            
            progress.advance(task)
    
    return results

def create_metadata_table():
    """Create metadata table for the loaded data"""
    console.print("\n[bold blue]Creating metadata table...[/bold blue]")
    
    tables = db_manager.get_all_tables()
    metadata = []
    
    for table in tables:
        if table.startswith('_'):
            continue
        try:
            result = db_manager.execute_query(f'SELECT COUNT(*) as cnt FROM "{table}"')
            row_count = result[0]['cnt']
            
            cols = db_manager.get_table_columns(table)
            
            metadata.append({
                'table_name': table,
                'row_count': row_count,
                'column_count': len(cols),
                'columns': ','.join([c['column_name'] for c in cols])
            })
        except Exception as e:
            console.print(f"  [yellow]Warning: Could not get metadata for {table}: {e}[/yellow]")
    
    if metadata:
        df = pd.DataFrame(metadata)
        df.to_sql('_table_metadata', db_manager.engine, if_exists='replace', index=False)
        console.print(f"[green]Created _table_metadata with {len(metadata)} entries[/green]")

def main():
    console.print("[bold]=" * 60)
    console.print("[bold]Database Reload Script[/bold]")
    console.print("[bold]=" * 60 + "\n")
    
    # Step 1: Drop all tables
    drop_all_tables()
    
    # Step 2: Load CSV files
    results = load_csv_files()
    
    # Step 3: Create metadata
    create_metadata_table()
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]SUMMARY[/bold green]")
    console.print("=" * 60)
    console.print(f"Successfully loaded: {len(results['success'])} tables")
    for t in results['success']:
        console.print(f"  • {t['table']}: {t['rows']} rows")
    
    if results['failed']:
        console.print(f"\n[red]Failed to load: {len(results['failed'])} files[/red]")
        for f in results['failed']:
            console.print(f"  • {f['file']}: {f['error']}")
    
    # Verify
    console.print("\n[bold]Verifying...[/bold]")
    tables = db_manager.get_all_tables()
    console.print(f"Total tables in database: {len(tables)}")
    for t in tables:
        console.print(f"  • {t}")

if __name__ == "__main__":
    main()

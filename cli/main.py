"""
CHESS Text-to-SQL CLI Interface
Command-line interface for the clinical trial data query system
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import GROQ_API_KEY
from database.connection import db_manager
from database.schema_manager import schema_manager
from preprocessing.indexer import preprocessor


app = typer.Typer(help="CHESS Text-to-SQL for Clinical Trial Data")
console = Console()


@app.command()
def setup():
    """
    Setup the database and preprocessing indices.
    Run this first before querying.
    """
    console.print(Panel.fit(
        "[bold blue]CHESS Text-to-SQL Setup[/bold blue]\n"
        "This will load data and build indices.",
        title="Setup"
    ))
    
    # Check API key
    if not GROQ_API_KEY:
        console.print("[red]Error: GROQ_API_KEY not set![/red]")
        console.print("Please create a .env file with your Groq API key.")
        console.print("Get your key from: https://console.groq.com/")
        raise typer.Exit(1)
    
    console.print("[green]✓ Groq API key found[/green]")
    
    # Test database connection
    console.print("\n[bold]Testing database connection...[/bold]")
    try:
        tables = db_manager.get_all_tables()
        console.print(f"[green]✓ Connected to database[/green]")
        console.print(f"  Found {len(tables)} tables")
    except Exception as e:
        console.print(f"[red]Error connecting to database: {e}[/red]")
        console.print("\nMake sure PostgreSQL is running and configured in .env")
        raise typer.Exit(1)
    
    # Load data if tables are empty
    if len(tables) == 0:
        console.print("\n[yellow]No tables found. Loading clinical trial data...[/yellow]")
        from database.data_loader import ClinicalDataLoader, create_database_if_not_exists
        
        create_database_if_not_exists()
        loader = ClinicalDataLoader()
        results = loader.load_all_studies()
        
        console.print(f"[green]✓ Loaded {len(results['success'])} tables[/green]")
    
    # Refresh schema
    console.print("\n[bold]Refreshing schema information...[/bold]")
    num_tables = schema_manager.refresh_schema(include_samples=True)
    console.print(f"[green]✓ Schema cached for {num_tables} tables[/green]")
    
    # Build preprocessing indices
    console.print("\n[bold]Building preprocessing indices...[/bold]")
    
    if not preprocessor.load_cache():
        stats = preprocessor.preprocess(db_manager, schema_manager)
        console.print(f"[green]✓ Indexed {stats['total_values_indexed']} values[/green]")
        console.print(f"[green]✓ Indexed {stats['total_descriptions']} schema descriptions[/green]")
    else:
        console.print("[green]✓ Loaded preprocessing cache[/green]")
    
    console.print("\n[bold green]Setup complete! You can now run queries.[/bold green]")
    console.print("Try: python -m cli.main query \"How many patients are in Study 1?\"")


@app.command()
def query(
    question: str = typer.Argument(..., help="Natural language question about the clinical trial data"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed agent output"),
    execute: bool = typer.Option(True, "--execute/--no-execute", help="Execute the generated SQL"),
    candidates: int = typer.Option(3, "--candidates", "-c", help="Number of SQL candidates"),
    tests: int = typer.Option(5, "--tests", "-t", help="Number of unit tests")
):
    """
    Query the clinical trial database using natural language.
    """
    from pipeline.orchestrator import create_pipeline
    
    console.print(Panel.fit(
        f"[bold]Question:[/bold] {question}",
        title="CHESS Query"
    ))
    
    try:
        pipeline = create_pipeline(verbose=verbose)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("Run 'python -m cli.main setup' first.")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Processing query...", total=None)
        
        result = pipeline.run(
            question=question,
            num_candidates=candidates,
            num_unit_tests=tests,
            execute_result=execute
        )
    
    # Display results
    if result.success and result.sql:
        console.print("\n[bold green]Generated SQL:[/bold green]")
        console.print(Syntax(result.sql, "sql", theme="monokai", line_numbers=True))
        
        if result.execution_result and result.execution_result.get('success'):
            data = result.execution_result.get('data', [])
            columns = result.execution_result.get('columns', [])
            row_count = result.execution_result.get('row_count', 0)
            
            console.print(f"\n[bold green]Results: {row_count} rows[/bold green]")
            
            if data and columns:
                table = Table(title="Query Results (first 10 rows)")
                for col in columns:
                    table.add_column(str(col)[:30], overflow="fold")
                
                for row in data[:10]:
                    table.add_row(*[str(v)[:50] if v else "NULL" for v in row.values()])
                
                console.print(table)
        elif result.execution_result:
            console.print(f"\n[yellow]Execution error: {result.execution_result.get('error')}[/yellow]")
    else:
        console.print(f"\n[red]Query failed: {result.error}[/red]")
    
    # Show metrics
    console.print(f"\n[dim]Metrics: {result.total_tokens} tokens, {result.total_time:.2f}s[/dim]")


@app.command()
def interactive():
    """
    Start an interactive query session.
    """
    from pipeline.orchestrator import create_pipeline
    
    console.print(Panel.fit(
        "[bold blue]CHESS Interactive Mode[/bold blue]\n"
        "Type your questions in natural language.\n"
        "Commands: /quit, /help, /schema, /tables",
        title="Interactive Query Session"
    ))
    
    try:
        pipeline = create_pipeline(verbose=False)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("Run 'python -m cli.main setup' first.")
        raise typer.Exit(1)
    
    while True:
        try:
            question = Prompt.ask("\n[bold cyan]Question[/bold cyan]")
            
            if not question.strip():
                continue
            
            # Handle commands
            if question.startswith('/'):
                cmd = question.lower().strip()
                
                if cmd in ['/quit', '/exit', '/q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif cmd == '/help':
                    console.print("""
[bold]Commands:[/bold]
  /quit     - Exit interactive mode
  /help     - Show this help
  /schema   - Show database schema summary
  /tables   - List all tables
  
Just type your question to query the database!
                    """)
                    continue
                elif cmd == '/schema':
                    console.print(schema_manager.get_schema_summary())
                    continue
                elif cmd == '/tables':
                    tables = schema_manager.get_all_tables()
                    console.print(f"\n[bold]Tables ({len(tables)}):[/bold]")
                    for t in tables:
                        console.print(f"  • {t}")
                    continue
                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                    continue
            
            # Process query
            with console.status("Processing...", spinner="dots"):
                result = pipeline.run(
                    question=question,
                    num_candidates=2,
                    num_unit_tests=3,
                    execute_result=True
                )
            
            if result.success and result.sql:
                console.print("\n[bold]SQL:[/bold]")
                console.print(Syntax(result.sql, "sql", theme="monokai"))
                
                if result.execution_result and result.execution_result.get('success'):
                    data = result.execution_result.get('data', [])
                    row_count = result.execution_result.get('row_count', 0)
                    columns = result.execution_result.get('columns', [])
                    
                    console.print(f"\n[green]{row_count} rows returned[/green]")
                    
                    if data:
                        table = Table()
                        for col in columns[:8]:  # Limit columns
                            table.add_column(str(col)[:20])
                        
                        for row in data[:5]:  # Limit rows
                            values = list(row.values())[:8]
                            table.add_row(*[str(v)[:30] if v else "NULL" for v in values])
                        
                        console.print(table)
                        
                        if row_count > 5:
                            console.print(f"[dim]... and {row_count - 5} more rows[/dim]")
            else:
                console.print(f"[red]Error: {result.error}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit to exit[/yellow]")
            continue


@app.command()
def schema(
    table: Optional[str] = typer.Argument(None, help="Specific table to show")
):
    """
    Show database schema information.
    """
    # Refresh schema if needed
    if not schema_manager.tables:
        schema_manager.refresh_schema()
    
    if table:
        info = schema_manager.get_table_info(table)
        if not info:
            console.print(f"[red]Table '{table}' not found[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[bold]Table: {info.name}[/bold]")
        console.print(f"Rows: {info.row_count}")
        console.print(f"Category: {info.category}")
        
        table_view = Table(title="Columns")
        table_view.add_column("Name")
        table_view.add_column("Type")
        table_view.add_column("Nullable")
        table_view.add_column("Sample Values")
        
        for col in info.columns:
            samples = ", ".join([str(v)[:20] for v in (col.sample_values or [])[:2]])
            table_view.add_row(
                col.name,
                col.data_type,
                "Yes" if col.is_nullable else "No",
                samples or "-"
            )
        
        console.print(table_view)
    else:
        console.print(schema_manager.get_schema_summary())


@app.command()
def load_data():
    """
    Load clinical trial Excel files into PostgreSQL.
    """
    from database.data_loader import ClinicalDataLoader, create_database_if_not_exists
    
    console.print("[bold]Loading Clinical Trial Data[/bold]\n")
    
    create_database_if_not_exists()
    
    loader = ClinicalDataLoader()
    results = loader.load_all_studies()
    
    console.print(f"\n[bold green]Successfully loaded: {len(results['success'])} tables[/bold green]")
    if results['failed']:
        console.print(f"[bold red]Failed to load: {len(results['failed'])} tables[/bold red]")


if __name__ == "__main__":
    app()

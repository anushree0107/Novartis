"""
CHASE-SQL Main Entry Point

Provides the main ChaseSQL class and CLI interface for text-to-SQL conversion.
"""
import sys
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

from .config import ChaseConfig, default_config, load_config_from_env, DatabaseConfig, LLMConfig
from .schema_context import SchemaContextBuilder, SchemaContext
from .schema_linker import SchemaLinker, LinkedSchema
from .sql_generator import SQLGenerator, SQLCandidate
from .sql_refiner import SQLRefiner, RefinementResult
from .database import DatabaseConnection, QueryResult
from .llm_client import create_llm_client, BaseLLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


@dataclass 
class ChaseResult:
    """Complete result of a CHASE-SQL conversion"""
    question: str
    sql: str
    success: bool
    linked_schema: Optional[LinkedSchema] = None
    query_result: Optional[QueryResult] = None
    refinement_result: Optional[RefinementResult] = None
    candidates: Optional[List[SQLCandidate]] = None


class ChaseSQL:
    """
    CHASE-SQL: Chain-of-thought Augmented Self-refinement for Enhanced SQL
    
    Main class for converting natural language to SQL queries
    against clinical trials databases.
    
    Example:
        chase = ChaseSQL()
        result = chase.text_to_sql("Show all open queries for Study 1")
        print(result.sql)
    """
    
    def __init__(
        self,
        config: Optional[ChaseConfig] = None,
        db_config: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CHASE-SQL.
        
        Args:
            config: Full ChaseConfig object
            db_config: Database config dict (host, database, user, password)
            llm_config: LLM config dict (provider, model, api_key)
        """
        # Build config from various sources
        self.config = config or default_config
        
        if db_config:
            self.config.database = DatabaseConfig(**db_config)
        if llm_config:
            self.config.llm = LLMConfig(**llm_config)
        
        # Initialize components lazily
        self._schema_context: Optional[SchemaContext] = None
        self._schema_linker: Optional[SchemaLinker] = None
        self._sql_generator: Optional[SQLGenerator] = None
        self._sql_refiner: Optional[SQLRefiner] = None
        self._db: Optional[DatabaseConnection] = None
        self._llm: Optional[BaseLLMClient] = None
    
    @property
    def schema_context(self) -> SchemaContext:
        """Get or build schema context"""
        if self._schema_context is None:
            builder = SchemaContextBuilder(self.config.schema_path)
            self._schema_context = builder.build_from_file()
        return self._schema_context
    
    @property
    def llm(self) -> BaseLLMClient:
        """Get or create LLM client"""
        if self._llm is None:
            self._llm = create_llm_client(self.config.llm)
        return self._llm
    
    @property
    def db(self) -> Optional[DatabaseConnection]:
        """Get or create database connection"""
        if self._db is None and self.config.execute_for_validation:
            try:
                self._db = DatabaseConnection(self.config.database)
            except Exception as e:
                logger.warning(f"Could not connect to database: {e}")
        return self._db
    
    @property
    def schema_linker(self) -> SchemaLinker:
        """Get or create schema linker"""
        if self._schema_linker is None:
            self._schema_linker = SchemaLinker(self.schema_context, self.llm)
        return self._schema_linker
    
    @property
    def sql_generator(self) -> SQLGenerator:
        """Get or create SQL generator"""
        if self._sql_generator is None:
            self._sql_generator = SQLGenerator(self.schema_context, self.llm)
        return self._sql_generator
    
    @property
    def sql_refiner(self) -> SQLRefiner:
        """Get or create SQL refiner"""
        if self._sql_refiner is None:
            self._sql_refiner = SQLRefiner(self.schema_context, self.db, self.llm)
        return self._sql_refiner
    
    def text_to_sql(
        self,
        question: str,
        execute: bool = False,
        refine: bool = True
    ) -> ChaseResult:
        """
        Convert natural language question to SQL.
        
        This is the main entry point implementing the full CHASE-SQL pipeline:
        1. Schema Linking - Identify relevant tables/columns
        2. SQL Generation - Generate SQL candidates
        3. Refinement - Iteratively fix errors
        
        Args:
            question: Natural language question
            execute: Whether to execute the final SQL
            refine: Whether to apply refinement loop
            
        Returns:
            ChaseResult with SQL and execution results
        """
        logger.info(f"Processing question: {question}")
        
        try:
            # Step 1: Schema Linking
            logger.debug("Step 1: Schema Linking")
            linked = self.schema_linker.link(question)
            
            if self.config.verbose:
                console.print(f"[dim]Linked tables: {', '.join(linked.tables)}[/dim]")
            
            # Step 2: SQL Generation
            logger.debug("Step 2: SQL Generation")
            candidates = self.sql_generator.generate(question, linked)
            
            if not candidates:
                return ChaseResult(
                    question=question,
                    sql="",
                    success=False,
                    linked_schema=linked
                )
            
            # Take best candidate (first one from CoT strategy)
            best_sql = candidates[0].sql
            
            if self.config.verbose:
                console.print(f"[dim]Generated SQL ({candidates[0].strategy}):[/dim]")
                console.print(Syntax(best_sql, "sql", theme="monokai"))
            
            # Step 3: Refinement (optional)
            refinement_result = None
            if refine and self.db:
                logger.debug("Step 3: Refinement")
                refinement_result = self.sql_refiner.refine(
                    best_sql, question, execute=True
                )
                best_sql = refinement_result.final_sql
            
            # Step 4: Execute (optional)
            query_result = None
            if execute and self.db:
                query_result = self.db.execute_query(best_sql)
            elif refinement_result:
                query_result = refinement_result.query_result
            
            return ChaseResult(
                question=question,
                sql=best_sql,
                success=True,
                linked_schema=linked,
                query_result=query_result,
                refinement_result=refinement_result,
                candidates=candidates
            )
            
        except Exception as e:
            logger.error(f"CHASE-SQL failed: {e}", exc_info=True)
            return ChaseResult(
                question=question,
                sql="",
                success=False
            )
    
    def execute(self, sql: str) -> QueryResult:
        """Execute a SQL query and return results"""
        if not self.db:
            raise RuntimeError("Database not configured")
        return self.db.execute_query(sql)


# CLI Interface
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """CHASE-SQL: Text-to-SQL for Clinical Trials"""
    ctx.ensure_object(dict)
    config = load_config_from_env()
    config.verbose = verbose
    ctx.obj['chase'] = ChaseSQL(config)


@cli.command()
@click.argument('question')
@click.option('--execute', '-e', is_flag=True, help='Execute the generated SQL')
@click.option('--no-refine', is_flag=True, help='Skip refinement loop')
@click.pass_context
def query(ctx, question: str, execute: bool, no_refine: bool):
    """Convert a natural language question to SQL"""
    chase: ChaseSQL = ctx.obj['chase']
    
    with console.status("[bold green]Processing..."):
        result = chase.text_to_sql(question, execute=execute, refine=not no_refine)
    
    if result.success:
        console.print(Panel(
            Syntax(result.sql, "sql", theme="monokai", word_wrap=True),
            title="[bold green]Generated SQL",
            border_style="green"
        ))
        
        if result.query_result and result.query_result.success:
            _display_results(result.query_result)
    else:
        console.print("[red]Failed to generate SQL[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive query mode"""
    chase: ChaseSQL = ctx.obj['chase']
    
    console.print("[bold]CHASE-SQL Interactive Mode[/bold]")
    console.print("Enter natural language questions. Type 'exit' to quit.\n")
    
    while True:
        try:
            question = console.input("[bold cyan]Question:[/bold cyan] ")
            
            if question.lower() in ('exit', 'quit', 'q'):
                break
            
            if not question.strip():
                continue
            
            with console.status("[bold green]Processing..."):
                result = chase.text_to_sql(question, execute=True)
            
            if result.success:
                console.print(Syntax(result.sql, "sql", theme="monokai"))
                if result.query_result:
                    _display_results(result.query_result)
            else:
                console.print("[red]Failed to generate SQL[/red]")
            
            console.print()
            
        except KeyboardInterrupt:
            break
    
    console.print("\n[dim]Goodbye![/dim]")


@cli.command()
@click.pass_context
def schema(ctx):
    """Display the parsed database schema"""
    chase: ChaseSQL = ctx.obj['chase']
    
    for table_name, table_info in list(chase.schema_context.tables.items())[:10]:
        console.print(f"\n[bold]{table_name}[/bold]")
        if table_info.description:
            console.print(f"  [dim]{table_info.description}[/dim]")
        for col in table_info.columns[:5]:
            pk = " (PK)" if col.is_primary_key else ""
            fk = f" → {col.fk_reference}" if col.is_foreign_key else ""
            console.print(f"  - {col.name}: {col.data_type}{pk}{fk}")


def _display_results(result: QueryResult):
    """Display query results in a formatted table"""
    if not result.data:
        console.print("[yellow]No results[/yellow]")
        return
    
    table = Table(title=f"Results ({result.row_count} rows)")
    
    # Add columns
    for col in result.columns[:10]:  # Limit columns
        table.add_column(col, style="cyan")
    
    # Add rows
    for row in result.data[:20]:  # Limit rows
        values = [str(row.get(col, ""))[:50] for col in result.columns[:10]]
        table.add_row(*values)
    
    if result.row_count > 20:
        console.print(f"[dim]... and {result.row_count - 20} more rows[/dim]")
    
    console.print(table)


def main():
    """Entry point for CLI"""
    cli(obj={})


if __name__ == "__main__":
    main()

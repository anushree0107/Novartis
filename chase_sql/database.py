"""
Database connection and SQL execution utilities for CHASE-SQL.

Provides safe SQL execution with error handling and result formatting.
"""
import psycopg2
from psycopg2 import sql, Error
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass
import logging

from .config import DatabaseConfig, default_config

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Encapsulates the result of a SQL query execution"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "row_count": self.row_count,
            "columns": self.columns,
            "data": self.data[:10] if self.data else None,  # Limit for display
            "error": self.error,
        }


class DatabaseConnection:
    """
    PostgreSQL database connection manager.
    
    Provides connection pooling, safe query execution, and schema introspection.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or default_config.database
        self._conn: Optional[psycopg2.extensions.connection] = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            # Build connection parameters
            conn_params = {
                "database": self.config.database,
                "user": self.config.user,
            }
            
            # Only add host/port if password is provided (TCP/IP connection)
            # Otherwise use Unix socket for peer authentication
            if self.config.password:
                conn_params["host"] = self.config.host
                conn_params["port"] = self.config.port
                conn_params["password"] = self.config.password
            
            self._conn = psycopg2.connect(**conn_params)
            self._conn.autocommit = True  # For read queries
            logger.info(f"Connected to database: {self.config.database}")
        except Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Disconnected from database")
    
    @property
    def connection(self) -> psycopg2.extensions.connection:
        """Get or create connection"""
        if self._conn is None or self._conn.closed:
            self.connect()
        return self._conn
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch_results: bool = True,
        max_rows: int = 1000
    ) -> QueryResult:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters for safe substitution
            fetch_results: Whether to fetch and return results
            max_rows: Maximum number of rows to return
            
        Returns:
            QueryResult with success status, data, or error information
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Add LIMIT if not present and fetching results
                if fetch_results and "limit" not in query.lower():
                    # Remove trailing semicolon before wrapping
                    clean_query = query.rstrip().rstrip(';')
                    query = f"SELECT * FROM ({clean_query}) AS subq LIMIT {max_rows}"
                
                cursor.execute(query, params)
                
                if fetch_results and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    data = [dict(row) for row in cursor.fetchall()]
                    return QueryResult(
                        success=True,
                        data=data,
                        columns=columns,
                        row_count=len(data)
                    )
                else:
                    return QueryResult(
                        success=True,
                        row_count=cursor.rowcount
                    )
                    
        except Error as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.warning(f"Query execution error ({error_type}): {error_msg}")
            return QueryResult(
                success=False,
                error=error_msg,
                error_type=error_type
            )
    
    def validate_sql(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query without executing it.
        
        Uses EXPLAIN to check syntax without running the query.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"EXPLAIN {query}")
                return True, None
        except Error as e:
            return False, str(e)
    
    def get_table_names(self) -> List[str]:
        """Get list of all tables in the database"""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        result = self.execute_query(query, (self.config.schema,))
        if result.success:
            return [row['table_name'] for row in result.data]
        return []
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a specific table"""
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        result = self.execute_query(query, (self.config.schema, table_name))
        return result.data if result.success else []
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample rows from a table"""
        # Use sql.Identifier to safely handle table names
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = self.execute_query(query)
        return result.data if result.success else []
    
    def get_foreign_keys(self) -> List[Dict[str, Any]]:
        """Get all foreign key relationships"""
        query = """
            SELECT 
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = %s
            ORDER BY tc.table_name
        """
        result = self.execute_query(query, (self.config.schema,))
        return result.data if result.success else []
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Singleton connection for convenience
_default_db: Optional[DatabaseConnection] = None


def get_database() -> DatabaseConnection:
    """Get or create default database connection"""
    global _default_db
    if _default_db is None:
        _default_db = DatabaseConnection()
    return _default_db


def execute_sql(query: str, params: Optional[Tuple] = None) -> QueryResult:
    """Convenience function to execute SQL using default connection"""
    return get_database().execute_query(query, params)

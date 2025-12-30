"""
Database connection and utilities for PostgreSQL
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, inspect
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import pandas as pd

from config.settings import DATABASE_CONFIG


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self, config: Dict[str, str] = None):
        self.config = config or DATABASE_CONFIG
        self._engine = None
    
    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string"""
        # URL-encode the password to handle special characters like @
        encoded_password = quote_plus(self.config['password'])
        return (
            f"postgresql://{self.config['user']}:{encoded_password}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
    
    @property
    def engine(self):
        """Get or create SQLAlchemy engine"""
        if self._engine is None:
            self._engine = create_engine(self.connection_string)
        return self._engine
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_query_df(self, query: str) -> pd.DataFrame:
        """Execute query and return as DataFrame"""
        return pd.read_sql(query, self.engine)
    
    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        with self.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """Check if a table exists"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            );
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (schema, table_name))
            result = cursor.fetchone()
            return result['exists']
    
    def get_all_tables(self, schema: str = 'public') -> List[str]:
        """Get all table names in the database"""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s
            ORDER BY table_name;
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (schema,))
            return [row['table_name'] for row in cursor.fetchall()]
    
    def get_table_columns(self, table_name: str, schema: str = 'public') -> List[Dict]:
        """Get column information for a table"""
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (schema, table_name))
            return list(cursor.fetchall())
    
    def get_table_sample(self, table_name: str, limit: int = 3, schema: str = 'public') -> List[Dict]:
        """Get sample rows from a table"""
        query = sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
            sql.Identifier(schema),
            sql.Identifier(table_name)
        )
        with self.get_cursor() as cursor:
            cursor.execute(query, (limit,))
            return list(cursor.fetchall())
    
    def get_table_row_count(self, table_name: str, schema: str = 'public') -> int:
        """Get the number of rows in a table"""
        query = sql.SQL("SELECT COUNT(*) as count FROM {}.{}").format(
            sql.Identifier(schema),
            sql.Identifier(table_name)
        )
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()['count']
    
    def get_primary_keys(self, table_name: str, schema: str = 'public') -> List[str]:
        """Get primary key columns for a table"""
        query = """
            SELECT a.attname as column_name
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            JOIN pg_class c ON c.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE i.indisprimary
            AND c.relname = %s
            AND n.nspname = %s;
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (table_name, schema))
            return [row['column_name'] for row in cursor.fetchall()]
    
    def get_foreign_keys(self, table_name: str, schema: str = 'public') -> List[Dict]:
        """Get foreign key relationships for a table"""
        query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
            AND tc.table_schema = %s;
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (table_name, schema))
            return list(cursor.fetchall())
    
    def validate_sql(self, query: str) -> Dict[str, Any]:
        """Validate SQL syntax without executing"""
        try:
            with self.get_cursor() as cursor:
                # Use EXPLAIN to validate without executing
                cursor.execute(f"EXPLAIN {query}")
                return {"valid": True, "error": None}
        except psycopg2.Error as e:
            return {"valid": False, "error": str(e)}
    
    def safe_execute(self, query: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """Execute query with timeout and error handling"""
        try:
            with self.get_connection() as conn:
                conn.set_session(autocommit=True)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Set statement timeout
                cursor.execute(f"SET statement_timeout = '{timeout_seconds * 1000}'")
                cursor.execute(query)
                
                # Check if it's a SELECT query
                if cursor.description:
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return {
                        "success": True,
                        "data": [dict(row) for row in results],
                        "columns": columns,
                        "row_count": len(results)
                    }
                else:
                    return {
                        "success": True,
                        "affected_rows": cursor.rowcount
                    }
        except psycopg2.Error as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.pgcode if hasattr(e, 'pgcode') else None
            }


# Singleton instance
db_manager = DatabaseManager()

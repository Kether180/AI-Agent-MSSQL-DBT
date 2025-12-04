"""
MSSQL Metadata Extractor

Connects to Microsoft SQL Server databases and extracts comprehensive metadata
including tables, views, stored procedures, columns, relationships, and indexes.

This is the real implementation that replaces mock data for the MVP.
"""

import pyodbc
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Column:
    """Represents a database column"""
    name: str
    data_type: str
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    default_value: Optional[str]
    description: Optional[str] = None


@dataclass
class Table:
    """Represents a database table"""
    schema: str
    name: str
    columns: List[Column]
    row_count: Optional[int] = None
    description: Optional[str] = None


@dataclass
class View:
    """Represents a database view"""
    schema: str
    name: str
    columns: List[Column]
    definition: Optional[str] = None
    description: Optional[str] = None


@dataclass
class StoredProcedure:
    """Represents a stored procedure"""
    schema: str
    name: str
    definition: str
    parameters: List[Dict[str, Any]]
    description: Optional[str] = None


@dataclass
class ForeignKey:
    """Represents a foreign key relationship"""
    name: str
    source_schema: str
    source_table: str
    source_column: str
    target_schema: str
    target_table: str
    target_column: str


@dataclass
class Index:
    """Represents a database index"""
    name: str
    schema: str
    table_name: str
    columns: List[str]
    is_unique: bool
    is_primary_key: bool
    is_clustered: bool


# =============================================================================
# MSSQL EXTRACTOR CLASS
# =============================================================================

class MSSQLExtractor:
    """
    Extracts metadata from Microsoft SQL Server databases.

    Usage:
        extractor = MSSQLExtractor(
            server="localhost",
            database="MyDB",
            username="sa",
            password="password"
        )
        metadata = extractor.extract_all()
    """

    def __init__(
        self,
        server: str,
        database: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        driver: str = "ODBC Driver 17 for SQL Server",
        trusted_connection: bool = False,
        port: int = 1433
    ):
        """
        Initialize MSSQL connection parameters.

        Args:
            server: SQL Server hostname or IP
            database: Database name
            username: SQL Server username (optional if using Windows auth)
            password: SQL Server password (optional if using Windows auth)
            driver: ODBC driver name
            trusted_connection: Use Windows authentication
            port: SQL Server port (default 1433)
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.trusted_connection = trusted_connection
        self.port = port
        self._connection = None

    def _build_connection_string(self) -> str:
        """Build ODBC connection string"""
        if self.trusted_connection:
            return (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"Trusted_Connection=yes;"
            )
        else:
            return (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )

    @contextmanager
    def connection(self):
        """Context manager for database connection"""
        conn = None
        try:
            conn_string = self._build_connection_string()
            conn = pyodbc.connect(conn_string, timeout=30)
            yield conn
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    # =========================================================================
    # TABLE EXTRACTION
    # =========================================================================

    def extract_tables(self, schema_filter: Optional[str] = None) -> List[Table]:
        """
        Extract all tables with their columns.

        Args:
            schema_filter: Optional schema name to filter (e.g., 'dbo')

        Returns:
            List of Table objects
        """
        tables = []

        # Query to get all tables
        tables_query = """
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            p.rows AS row_count,
            ep.value AS description
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
        LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id
            AND ep.minor_id = 0
            AND ep.name = 'MS_Description'
        WHERE t.is_ms_shipped = 0
        """

        if schema_filter:
            tables_query += f" AND s.name = '{schema_filter}'"

        tables_query += " ORDER BY s.name, t.name"

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(tables_query)

                for row in cursor.fetchall():
                    schema_name, table_name, row_count, description = row

                    # Get columns for this table
                    columns = self._extract_columns(conn, schema_name, table_name)

                    tables.append(Table(
                        schema=schema_name,
                        name=table_name,
                        columns=columns,
                        row_count=row_count,
                        description=description
                    ))

            logger.info(f"Extracted {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
            raise

    def _extract_columns(
        self,
        conn,
        schema_name: str,
        table_name: str
    ) -> List[Column]:
        """Extract columns for a specific table"""

        columns_query = """
        SELECT
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            CASE WHEN pk.column_id IS NOT NULL THEN 1 ELSE 0 END AS is_primary_key,
            CASE WHEN fk.parent_column_id IS NOT NULL THEN 1 ELSE 0 END AS is_foreign_key,
            dc.definition AS default_value,
            ep.value AS description
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        INNER JOIN sys.tables tbl ON c.object_id = tbl.object_id
        INNER JOIN sys.schemas s ON tbl.schema_id = s.schema_id
        LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
        LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id
            AND ep.minor_id = c.column_id
            AND ep.name = 'MS_Description'
        LEFT JOIN (
            SELECT ic.column_id, ic.object_id
            FROM sys.index_columns ic
            INNER JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
            WHERE i.is_primary_key = 1
        ) pk ON pk.object_id = c.object_id AND pk.column_id = c.column_id
        LEFT JOIN sys.foreign_key_columns fk ON fk.parent_object_id = c.object_id
            AND fk.parent_column_id = c.column_id
        WHERE s.name = ? AND tbl.name = ?
        ORDER BY c.column_id
        """

        columns = []
        cursor = conn.cursor()
        cursor.execute(columns_query, (schema_name, table_name))

        for row in cursor.fetchall():
            columns.append(Column(
                name=row.column_name,
                data_type=row.data_type,
                max_length=row.max_length,
                precision=row.precision,
                scale=row.scale,
                is_nullable=bool(row.is_nullable),
                is_primary_key=bool(row.is_primary_key),
                is_foreign_key=bool(row.is_foreign_key),
                default_value=row.default_value,
                description=row.description
            ))

        return columns

    # =========================================================================
    # VIEW EXTRACTION
    # =========================================================================

    def extract_views(self, schema_filter: Optional[str] = None) -> List[View]:
        """Extract all views with their columns and definitions"""
        views = []

        views_query = """
        SELECT
            s.name AS schema_name,
            v.name AS view_name,
            m.definition AS view_definition,
            ep.value AS description
        FROM sys.views v
        INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
        LEFT JOIN sys.sql_modules m ON v.object_id = m.object_id
        LEFT JOIN sys.extended_properties ep ON ep.major_id = v.object_id
            AND ep.minor_id = 0
            AND ep.name = 'MS_Description'
        WHERE v.is_ms_shipped = 0
        """

        if schema_filter:
            views_query += f" AND s.name = '{schema_filter}'"

        views_query += " ORDER BY s.name, v.name"

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(views_query)

                for row in cursor.fetchall():
                    schema_name, view_name, definition, description = row

                    # Get columns for this view
                    columns = self._extract_view_columns(conn, schema_name, view_name)

                    views.append(View(
                        schema=schema_name,
                        name=view_name,
                        columns=columns,
                        definition=definition,
                        description=description
                    ))

            logger.info(f"Extracted {len(views)} views")
            return views

        except Exception as e:
            logger.error(f"Failed to extract views: {e}")
            raise

    def _extract_view_columns(
        self,
        conn,
        schema_name: str,
        view_name: str
    ) -> List[Column]:
        """Extract columns for a specific view"""

        columns_query = """
        SELECT
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        INNER JOIN sys.views v ON c.object_id = v.object_id
        INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
        WHERE s.name = ? AND v.name = ?
        ORDER BY c.column_id
        """

        columns = []
        cursor = conn.cursor()
        cursor.execute(columns_query, (schema_name, view_name))

        for row in cursor.fetchall():
            columns.append(Column(
                name=row.column_name,
                data_type=row.data_type,
                max_length=row.max_length,
                precision=row.precision,
                scale=row.scale,
                is_nullable=bool(row.is_nullable),
                is_primary_key=False,
                is_foreign_key=False,
                default_value=None
            ))

        return columns

    # =========================================================================
    # STORED PROCEDURE EXTRACTION
    # =========================================================================

    def extract_stored_procedures(
        self,
        schema_filter: Optional[str] = None
    ) -> List[StoredProcedure]:
        """Extract all stored procedures with their definitions and parameters"""
        procedures = []

        proc_query = """
        SELECT
            s.name AS schema_name,
            p.name AS proc_name,
            m.definition AS proc_definition,
            ep.value AS description
        FROM sys.procedures p
        INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
        LEFT JOIN sys.sql_modules m ON p.object_id = m.object_id
        LEFT JOIN sys.extended_properties ep ON ep.major_id = p.object_id
            AND ep.minor_id = 0
            AND ep.name = 'MS_Description'
        WHERE p.is_ms_shipped = 0
        """

        if schema_filter:
            proc_query += f" AND s.name = '{schema_filter}'"

        proc_query += " ORDER BY s.name, p.name"

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(proc_query)

                for row in cursor.fetchall():
                    schema_name, proc_name, definition, description = row

                    # Get parameters for this procedure
                    parameters = self._extract_parameters(conn, schema_name, proc_name)

                    procedures.append(StoredProcedure(
                        schema=schema_name,
                        name=proc_name,
                        definition=definition or "",
                        parameters=parameters,
                        description=description
                    ))

            logger.info(f"Extracted {len(procedures)} stored procedures")
            return procedures

        except Exception as e:
            logger.error(f"Failed to extract stored procedures: {e}")
            raise

    def _extract_parameters(
        self,
        conn,
        schema_name: str,
        proc_name: str
    ) -> List[Dict[str, Any]]:
        """Extract parameters for a stored procedure"""

        params_query = """
        SELECT
            par.name AS param_name,
            t.name AS data_type,
            par.max_length,
            par.precision,
            par.scale,
            par.is_output,
            par.has_default_value,
            par.default_value
        FROM sys.parameters par
        INNER JOIN sys.procedures p ON par.object_id = p.object_id
        INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
        INNER JOIN sys.types t ON par.user_type_id = t.user_type_id
        WHERE s.name = ? AND p.name = ?
        ORDER BY par.parameter_id
        """

        parameters = []
        cursor = conn.cursor()
        cursor.execute(params_query, (schema_name, proc_name))

        for row in cursor.fetchall():
            parameters.append({
                'name': row.param_name,
                'data_type': row.data_type,
                'max_length': row.max_length,
                'precision': row.precision,
                'scale': row.scale,
                'is_output': bool(row.is_output),
                'has_default': bool(row.has_default_value),
                'default_value': row.default_value
            })

        return parameters

    # =========================================================================
    # FOREIGN KEY EXTRACTION
    # =========================================================================

    def extract_foreign_keys(self) -> List[ForeignKey]:
        """Extract all foreign key relationships"""

        fk_query = """
        SELECT
            fk.name AS fk_name,
            s1.name AS source_schema,
            t1.name AS source_table,
            c1.name AS source_column,
            s2.name AS target_schema,
            t2.name AS target_table,
            c2.name AS target_column
        FROM sys.foreign_keys fk
        INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables t1 ON fkc.parent_object_id = t1.object_id
        INNER JOIN sys.schemas s1 ON t1.schema_id = s1.schema_id
        INNER JOIN sys.columns c1 ON fkc.parent_object_id = c1.object_id
            AND fkc.parent_column_id = c1.column_id
        INNER JOIN sys.tables t2 ON fkc.referenced_object_id = t2.object_id
        INNER JOIN sys.schemas s2 ON t2.schema_id = s2.schema_id
        INNER JOIN sys.columns c2 ON fkc.referenced_object_id = c2.object_id
            AND fkc.referenced_column_id = c2.column_id
        ORDER BY fk.name
        """

        foreign_keys = []

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(fk_query)

                for row in cursor.fetchall():
                    foreign_keys.append(ForeignKey(
                        name=row.fk_name,
                        source_schema=row.source_schema,
                        source_table=row.source_table,
                        source_column=row.source_column,
                        target_schema=row.target_schema,
                        target_table=row.target_table,
                        target_column=row.target_column
                    ))

            logger.info(f"Extracted {len(foreign_keys)} foreign keys")
            return foreign_keys

        except Exception as e:
            logger.error(f"Failed to extract foreign keys: {e}")
            raise

    # =========================================================================
    # INDEX EXTRACTION
    # =========================================================================

    def extract_indexes(self) -> List[Index]:
        """Extract all indexes"""

        idx_query = """
        SELECT
            i.name AS index_name,
            s.name AS schema_name,
            t.name AS table_name,
            i.is_unique,
            i.is_primary_key,
            i.type_desc
        FROM sys.indexes i
        INNER JOIN sys.tables t ON i.object_id = t.object_id
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE i.name IS NOT NULL AND t.is_ms_shipped = 0
        ORDER BY s.name, t.name, i.name
        """

        indexes = []

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(idx_query)

                for row in cursor.fetchall():
                    # Get columns for this index
                    columns = self._extract_index_columns(
                        conn, row.schema_name, row.table_name, row.index_name
                    )

                    indexes.append(Index(
                        name=row.index_name,
                        schema=row.schema_name,
                        table_name=row.table_name,
                        columns=columns,
                        is_unique=bool(row.is_unique),
                        is_primary_key=bool(row.is_primary_key),
                        is_clustered=row.type_desc == 'CLUSTERED'
                    ))

            logger.info(f"Extracted {len(indexes)} indexes")
            return indexes

        except Exception as e:
            logger.error(f"Failed to extract indexes: {e}")
            raise

    def _extract_index_columns(
        self,
        conn,
        schema_name: str,
        table_name: str,
        index_name: str
    ) -> List[str]:
        """Extract columns for a specific index"""

        cols_query = """
        SELECT c.name
        FROM sys.index_columns ic
        INNER JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        INNER JOIN sys.tables t ON i.object_id = t.object_id
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = ? AND t.name = ? AND i.name = ?
        ORDER BY ic.key_ordinal
        """

        columns = []
        cursor = conn.cursor()
        cursor.execute(cols_query, (schema_name, table_name, index_name))

        for row in cursor.fetchall():
            columns.append(row.name)

        return columns

    # =========================================================================
    # FULL EXTRACTION
    # =========================================================================

    def extract_all(
        self,
        schema_filter: Optional[str] = None,
        include_procedures: bool = True,
        include_indexes: bool = True
    ) -> Dict[str, Any]:
        """
        Extract all metadata from the database.

        Args:
            schema_filter: Optional schema name to filter
            include_procedures: Include stored procedures (can be slow)
            include_indexes: Include indexes

        Returns:
            Dictionary with all metadata ready for the AI agents
        """
        logger.info(f"Starting full metadata extraction for database: {self.database}")

        # Extract all objects
        tables = self.extract_tables(schema_filter)
        views = self.extract_views(schema_filter)
        foreign_keys = self.extract_foreign_keys()

        stored_procedures = []
        if include_procedures:
            stored_procedures = self.extract_stored_procedures(schema_filter)

        indexes = []
        if include_indexes:
            indexes = self.extract_indexes()

        # Convert to dictionaries for JSON serialization
        metadata = {
            'database': self.database,
            'server': self.server,
            'tables': [
                {
                    'schema': t.schema,
                    'name': t.name,
                    'row_count': t.row_count,
                    'description': t.description,
                    'columns': [asdict(c) for c in t.columns]
                }
                for t in tables
            ],
            'views': [
                {
                    'schema': v.schema,
                    'name': v.name,
                    'definition': v.definition,
                    'description': v.description,
                    'columns': [asdict(c) for c in v.columns]
                }
                for v in views
            ],
            'stored_procedures': [
                {
                    'schema': sp.schema,
                    'name': sp.name,
                    'definition': sp.definition,
                    'parameters': sp.parameters,
                    'description': sp.description
                }
                for sp in stored_procedures
            ],
            'foreign_keys': [asdict(fk) for fk in foreign_keys],
            'indexes': [asdict(idx) for idx in indexes],
            'summary': {
                'total_tables': len(tables),
                'total_views': len(views),
                'total_stored_procedures': len(stored_procedures),
                'total_foreign_keys': len(foreign_keys),
                'total_indexes': len(indexes),
                'total_columns': sum(len(t.columns) for t in tables)
            }
        }

        logger.info(f"Extraction complete: {metadata['summary']}")

        return metadata


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_mssql_metadata(
    server: str,
    database: str,
    username: str,
    password: str,
    port: int = 1433,
    schema_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to extract MSSQL metadata.

    Args:
        server: SQL Server hostname
        database: Database name
        username: SQL username
        password: SQL password
        port: SQL Server port
        schema_filter: Optional schema to filter

    Returns:
        Metadata dictionary ready for AI agents
    """
    extractor = MSSQLExtractor(
        server=server,
        database=database,
        username=username,
        password=password,
        port=port
    )

    return extractor.extract_all(schema_filter=schema_filter)


def test_mssql_connection(
    server: str,
    database: str,
    username: str,
    password: str,
    port: int = 1433
) -> bool:
    """
    Test MSSQL connection.

    Returns:
        True if connection successful, False otherwise
    """
    extractor = MSSQLExtractor(
        server=server,
        database=database,
        username=username,
        password=password,
        port=port
    )

    return extractor.test_connection()


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    import json

    # Example usage
    print("MSSQL Metadata Extractor")
    print("=" * 50)

    # This would be called with real credentials
    # metadata = extract_mssql_metadata(
    #     server="localhost",
    #     database="AdventureWorks",
    #     username="sa",
    #     password="YourPassword"
    # )
    # print(json.dumps(metadata, indent=2))

    print("\nTo use, call extract_mssql_metadata() with your connection details.")

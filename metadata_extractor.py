"""
MSSQL Metadata Extractor

This file is responsible for extracting all the information from the MSSQL database that we need for migration. 
Investigates the database and writes a detailed report.

Extracts comprehensive metadata from MSSQL databases including:
- Tables, views, stored procedures
- Column definitions and data types
- Dependencies and relationships
- Table statistics
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class Column:
    """Represents a database column"""
    name: str
    data_type: str
    is_nullable: bool
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    default_value: Optional[str] = None


@dataclass
class Table:
    """Represents a database table"""
    schema: str
    name: str
    object_type: str  # 'TABLE', 'VIEW'
    columns: List[Column]
    row_count: Optional[int] = None
    dependencies: List[str] = None  # List of referenced objects
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    @property
    def full_name(self):
        return f"{self.schema}.{self.name}"


@dataclass
class StoredProcedure:
    """Represents a stored procedure"""
    schema: str
    name: str
    definition: str
    parameters: List[Dict[str, str]]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    @property
    def full_name(self):
        return f"{self.schema}.{self.name}"


@dataclass
class Dependency:
    """Represents a dependency relationship"""
    source_schema: str
    source_name: str
    target_schema: str
    target_name: str
    dependency_type: str  # 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'EXEC'
    
    @property
    def source_full_name(self):
        return f"{self.source_schema}.{self.source_name}"
    
    @property
    def target_full_name(self):
        return f"{self.target_schema}.{self.target_name}"


class MSSQLMetadataExtractor:
    """
    Extracts metadata from MSSQL database
    
    Note: For the POC, this includes both real extraction methods and
    mock methods for testing without a live MSSQL instance.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self):
        """Establish connection to MSSQL , Checks if we have a connection string
            If not → warns and stays in mock mode
            If yes → tries to connect using pyodbc
            Logs success or failure"""
        if not self.connection_string:
            logger.warning("No connection string provided, using mock mode")
            return
        
        try:
            import pyodbc
            self.connection = pyodbc.connect(self.connection_string)
            logger.info("Connected to MSSQL successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MSSQL: {e}")
            raise
    
    def extract_tables(self) -> List[Table]:
        """Extract all tables and views"""
        if not self.connection:
            return self._mock_extract_tables()
        
        query = """
        SELECT 
            s.name AS schema_name,
            t.name AS table_name,
            t.type_desc AS object_type
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
        
        UNION ALL
        
        SELECT 
            s.name AS schema_name,
            v.name AS view_name,
            'VIEW' AS object_type
        FROM sys.views v
        INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
        ORDER BY schema_name, table_name
        """
        # looping through tables and views results , for each table extract its columns, count rows if it's a table
        # create Table objects and return the all the list of Table objects.
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        tables = []
        for row in cursor.fetchall():
            schema, name, obj_type = row
            # Get the columns for this table
            columns = self._extract_columns(schema, name)
            # Get row count if it's a table (not a view)
            row_count = self._get_row_count(schema, name) if obj_type == 'USER_TABLE' else None
            
            tables.append(Table(
                schema=schema,
                name=name,
                object_type=obj_type,
                columns=columns,
                row_count=row_count
            ))
        
        cursor.close()
        return tables
    
    # extracts columns for a specific table, to know if they exitst or not, understanding data types for dbt models,
    #  identify nullable columns for data quality
    def _extract_columns(self, schema: str, table: str) -> List[Column]:
        """Extract columns for a specific table"""
        if not self.connection:
            return self._mock_extract_columns()
        
        query = """
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.is_nullable,
            c.max_length,
            c.precision,
            c.scale,
            dc.definition AS default_value
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        INNER JOIN sys.tables tb ON c.object_id = tb.object_id
        INNER JOIN sys.schemas s ON tb.schema_id = s.schema_id
        LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
        WHERE s.name = ? AND tb.name = ?
        ORDER BY c.column_id
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query, (schema, table))
        
        columns = []
        for row in cursor.fetchall():
            columns.append(Column(
                name=row.column_name,
                data_type=row.data_type,
                is_nullable=row.is_nullable,
                max_length=row.max_length,
                precision=row.precision,
                scale=row.scale,
                default_value=row.default_value
            ))
        
        cursor.close()
        return columns
    
    def _get_row_count(self, schema: str, table: str) -> int:
        """Get approximate row count for a table"""
        if not self.connection:
            return 1000
        
        query = f"SELECT COUNT(*) FROM [{schema}].[{table}]"
        cursor = self.connection.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    

    # extracts stored procedures, their definitions, parameters, to understand business logic encapsulated in the db so agents can analyze and migrate them
    def extract_stored_procedures(self) -> List[StoredProcedure]:
        """Extract stored procedures"""
        if not self.connection:
            return self._mock_extract_stored_procedures()
        
        query = """
        SELECT 
            s.name AS schema_name,
            p.name AS procedure_name,
            m.definition
        FROM sys.procedures p
        INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
        INNER JOIN sys.sql_modules m ON p.object_id = m.object_id
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
        ORDER BY s.name, p.name
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        procedures = []
        for row in cursor.fetchall():
            schema, name, definition = row
            parameters = self._extract_procedure_parameters(schema, name)
            
            procedures.append(StoredProcedure(
                schema=schema,
                name=name,
                definition=definition,
                parameters=parameters
            ))
        
        cursor.close()
        return procedures
    
    def _extract_procedure_parameters(self, schema: str, proc_name: str) -> List[Dict[str, str]]:
        """Extract parameters for a stored procedure"""
        if not self.connection:
            return []
        
        query = """
        SELECT 
            p.name AS parameter_name,
            t.name AS data_type,
            p.is_output
        FROM sys.parameters p
        INNER JOIN sys.types t ON p.user_type_id = t.user_type_id
        INNER JOIN sys.procedures pr ON p.object_id = pr.object_id
        INNER JOIN sys.schemas s ON pr.schema_id = s.schema_id
        WHERE s.name = ? AND pr.name = ?
        ORDER BY p.parameter_id
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query, (schema, proc_name))
        
        parameters = []
        for row in cursor.fetchall():
            parameters.append({
                'name': row.parameter_name,
                'data_type': row.data_type,
                'is_output': row.is_output
            })
        
        cursor.close()
        return parameters
    
    # orders table depends on customers table, so we need to know that to migrate in correct order
    # need to migrate custeomers first, then orders
    def extract_dependencies(self, tables: List[Table], procedures: List[StoredProcedure]) -> List[Dependency]:
        """Extract dependencies between objects"""
        if not self.connection:
            return self._mock_extract_dependencies()
        
        query = """
        SELECT 
            OBJECT_SCHEMA_NAME(referencing_id) AS source_schema,
            OBJECT_NAME(referencing_id) AS source_name,
            OBJECT_SCHEMA_NAME(referenced_id) AS target_schema,
            OBJECT_NAME(referenced_id) AS target_name,
            'SELECT' AS dependency_type
        FROM sys.sql_expression_dependencies
        WHERE referenced_id IS NOT NULL
        ORDER BY source_schema, source_name
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query)
        

         # this query finds all the relations between objects
        dependencies = []
        for row in cursor.fetchall():
            dependencies.append(Dependency(
                source_schema=row.source_schema,
                source_name=row.source_name,
                target_schema=row.target_schema,
                target_name=row.target_name,
                dependency_type=row.dependency_type
            ))
        
        cursor.close()
        return dependencies
    # main method to extract all metadata , connects to mssql , extracts tables, procedures, dependencies, maps dependencies ,
    # package everything into json serializable format, returns the complete metadata dictionary.
    def extract_all_metadata(self) -> Dict:
        """Extract all metadata and return as dictionary"""
        logger.info("Starting metadata extraction...")
        
        if self.connection_string:
            self.connect()
        
        tables = self.extract_tables()
        logger.info(f"Extracted {len(tables)} tables/views")
        
        procedures = self.extract_stored_procedures()
        logger.info(f"Extracted {len(procedures)} stored procedures")
        
        dependencies = self.extract_dependencies(tables, procedures)
        logger.info(f"Extracted {len(dependencies)} dependencies")
        
        # Enrich tables with dependencies
        dep_map = {}
        for dep in dependencies:
            if dep.source_full_name not in dep_map:
                dep_map[dep.source_full_name] = []
            dep_map[dep.source_full_name].append(dep.target_full_name)
        
        for table in tables:
            table.dependencies = dep_map.get(table.full_name, [])
        
        for proc in procedures:
            proc.dependencies = dep_map.get(proc.full_name, [])
        
        metadata = {
            'tables': [asdict(t) for t in tables],
            'stored_procedures': [asdict(p) for p in procedures],
            'dependencies': [asdict(d) for d in dependencies],
            'summary': {
                'total_tables': len([t for t in tables if t.object_type == 'USER_TABLE']),
                'total_views': len([t for t in tables if t.object_type == 'VIEW']),
                'total_procedures': len(procedures),
                'total_dependencies': len(dependencies)
            }
        }
        
        logger.info("Metadata extraction complete")
        return metadata
    
    # Mock methods for testing without MSSQL connection
    # fake data to simulate real extraction , test the system without mssql , demo the tool , develope with no infrastructure.
    def _mock_extract_tables(self) -> List[Table]:
        """Mock table extraction for POC testing"""
        return [
            Table(
                schema='dbo',
                name='customers',
                object_type='USER_TABLE',
                columns=[
                    Column('customer_id', 'int', False),
                    Column('customer_name', 'varchar', False, max_length=100),
                    Column('email', 'varchar', True, max_length=255),
                    Column('created_at', 'datetime', False),
                    Column('updated_at', 'datetime', True),
                ],
                row_count=50000,
                dependencies=[]
            ),
            Table(
                schema='dbo',
                name='orders',
                object_type='USER_TABLE',
                columns=[
                    Column('order_id', 'int', False),
                    Column('customer_id', 'int', False),
                    Column('order_date', 'datetime', False),
                    Column('total_amount', 'decimal', False, precision=10, scale=2),
                    Column('status', 'varchar', False, max_length=50),
                ],
                row_count=150000,
                dependencies=['dbo.customers']
            ),
            Table(
                schema='dbo',
                name='order_items',
                object_type='USER_TABLE',
                columns=[
                    Column('order_item_id', 'int', False),
                    Column('order_id', 'int', False),
                    Column('product_id', 'int', False),
                    Column('quantity', 'int', False),
                    Column('unit_price', 'decimal', False, precision=10, scale=2),
                ],
                row_count=400000,
                dependencies=['dbo.orders', 'dbo.products']
            ),
            Table(
                schema='dbo',
                name='products',
                object_type='USER_TABLE',
                columns=[
                    Column('product_id', 'int', False),
                    Column('product_name', 'varchar', False, max_length=200),
                    Column('category', 'varchar', True, max_length=100),
                    Column('price', 'decimal', False, precision=10, scale=2),
                ],
                row_count=5000,
                dependencies=[]
            ),
            Table(
                schema='dbo',
                name='vw_customer_orders',
                object_type='VIEW',
                columns=[
                    Column('customer_id', 'int', False),
                    Column('customer_name', 'varchar', False),
                    Column('order_count', 'int', False),
                    Column('total_spent', 'decimal', False, precision=10, scale=2),
                ],
                dependencies=['dbo.customers', 'dbo.orders']
            ),
        ]
    
    def _mock_extract_columns(self) -> List[Column]:
        """Mock columns for testing"""
        return []
    
    def _mock_extract_stored_procedures(self) -> List[StoredProcedure]:
        """Mock stored procedures for POC testing"""
        return [
            StoredProcedure(
                schema='dbo',
                name='usp_GetCustomerOrders',
                definition="""
CREATE PROCEDURE dbo.usp_GetCustomerOrders
    @customer_id INT
AS
BEGIN
    SELECT 
        o.order_id,
        o.order_date,
        o.total_amount,
        o.status
    FROM dbo.orders o
    WHERE o.customer_id = @customer_id
    ORDER BY o.order_date DESC
END
                """,
                parameters=[
                    {'name': '@customer_id', 'data_type': 'int', 'is_output': False}
                ],
                dependencies=['dbo.orders']
            ),
            StoredProcedure(
                schema='dbo',
                name='usp_CalculateRevenue',
                definition="""
CREATE PROCEDURE dbo.usp_CalculateRevenue
    @start_date DATETIME,
    @end_date DATETIME
AS
BEGIN
    SELECT 
        p.category,
        SUM(oi.quantity * oi.unit_price) as total_revenue
    FROM dbo.order_items oi
    INNER JOIN dbo.orders o ON oi.order_id = o.order_id
    INNER JOIN dbo.products p ON oi.product_id = p.product_id
    WHERE o.order_date BETWEEN @start_date AND @end_date
    GROUP BY p.category
END
                """,
                parameters=[
                    {'name': '@start_date', 'data_type': 'datetime', 'is_output': False},
                    {'name': '@end_date', 'data_type': 'datetime', 'is_output': False}
                ],
                dependencies=['dbo.order_items', 'dbo.orders', 'dbo.products']
            )
        ]
    
    def _mock_extract_dependencies(self) -> List[Dependency]:
        """Mock dependencies for POC testing"""
        return [
            Dependency('dbo', 'orders', 'dbo', 'customers', 'SELECT'),
            Dependency('dbo', 'order_items', 'dbo', 'orders', 'SELECT'),
            Dependency('dbo', 'order_items', 'dbo', 'products', 'SELECT'),
            Dependency('dbo', 'vw_customer_orders', 'dbo', 'customers', 'SELECT'),
            Dependency('dbo', 'vw_customer_orders', 'dbo', 'orders', 'SELECT'),
            Dependency('dbo', 'usp_GetCustomerOrders', 'dbo', 'orders', 'SELECT'),
            Dependency('dbo', 'usp_CalculateRevenue', 'dbo', 'order_items', 'SELECT'),
            Dependency('dbo', 'usp_CalculateRevenue', 'dbo', 'orders', 'SELECT'),
            Dependency('dbo', 'usp_CalculateRevenue', 'dbo', 'products', 'SELECT'),
        ]
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Connection closed")
    
    def save_metadata(self, metadata: Dict, output_path: str):
        """Save metadata to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # For POC, use mock mode
    extractor = MSSQLMetadataExtractor()
    metadata = extractor.extract_all_metadata()
    extractor.save_metadata(metadata, 'mssql_metadata.json')
    
    print(f"\nExtracted metadata:")
    print(f"- Tables: {metadata['summary']['total_tables']}")
    print(f"- Views: {metadata['summary']['total_views']}")
    print(f"- Stored Procedures: {metadata['summary']['total_procedures']}")
    print(f"- Dependencies: {metadata['summary']['total_dependencies']}")
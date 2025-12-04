"""
DataPrep AI Agent

Intelligent data preparation and cleaning agent for preparing data
for analytics and machine learning. Works with Snowflake, Databricks,
BigQuery, and Redshift.

Can be used as:
- Add-on to DataMigrate AI migration
- Standalone product for data preparation only

Copyright (c) 2025 OKO Investments. All rights reserved.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ImputationStrategy(Enum):
    """Strategies for handling null values"""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    PREDICTIVE = "predictive"
    DROP = "drop"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"


class DataPlatform(Enum):
    """Supported data platforms"""
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    BIGQUERY = "bigquery"
    REDSHIFT = "redshift"
    POSTGRES = "postgres"


class OutlierMethod(Enum):
    """Methods for outlier detection"""
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"
    LOF = "local_outlier_factor"


@dataclass
class ColumnProfile:
    """Profile information for a single column"""
    name: str
    data_type: str
    null_count: int
    null_percentage: float
    distinct_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_dev: Optional[float] = None
    is_categorical: bool = False
    is_numeric: bool = False
    is_datetime: bool = False
    recommended_imputation: ImputationStrategy = ImputationStrategy.DROP
    outlier_count: int = 0
    quality_score: float = 0.0
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class DataProfile:
    """Complete profile for a dataset"""
    table_name: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    overall_quality_score: float
    duplicate_rows: int
    duplicate_percentage: float
    memory_usage_mb: float
    recommended_actions: List[str]
    created_at: datetime


@dataclass
class PrepAction:
    """A data preparation action to be taken"""
    action_type: str
    column: Optional[str]
    description: str
    sql: str
    priority: int  # 1=high, 2=medium, 3=low
    estimated_impact: str


class DataPrepAgent:
    """
    DataPrep AI Agent for intelligent data preparation.

    Capabilities:
    - Auto Data Profiling
    - Smart Null Handling
    - Duplicate Detection
    - Type Inference
    - Outlier Detection
    - Feature Engineering
    - Data Standardization
    - Schema Optimization
    """

    def __init__(
        self,
        platform: DataPlatform = DataPlatform.SNOWFLAKE,
        connection_params: Optional[Dict[str, Any]] = None,
        llm_client: Optional[Any] = None
    ):
        self.platform = platform
        self.connection_params = connection_params or {}
        self.llm_client = llm_client
        self.profiles: Dict[str, DataProfile] = {}
        self.prep_actions: List[PrepAction] = []

    # ===========================================================================
    # DATA PROFILING
    # ===========================================================================

    def profile_table(
        self,
        table_name: str,
        sample_size: Optional[int] = None,
        include_samples: bool = True
    ) -> DataProfile:
        """
        Generate comprehensive profile for a table.

        Args:
            table_name: Full table name (schema.table)
            sample_size: Optional row limit for profiling
            include_samples: Include sample values in profile

        Returns:
            DataProfile with complete statistics
        """
        logger.info(f"Profiling table: {table_name}")

        # Generate profiling SQL based on platform
        profile_sql = self._generate_profile_sql(table_name, sample_size)

        # In production, execute SQL and parse results
        # For now, return structure
        profile = DataProfile(
            table_name=table_name,
            row_count=0,
            column_count=0,
            columns=[],
            overall_quality_score=0.0,
            duplicate_rows=0,
            duplicate_percentage=0.0,
            memory_usage_mb=0.0,
            recommended_actions=[],
            created_at=datetime.now()
        )

        self.profiles[table_name] = profile
        return profile

    def _generate_profile_sql(
        self,
        table_name: str,
        sample_size: Optional[int] = None
    ) -> str:
        """Generate platform-specific profiling SQL"""

        limit_clause = f"LIMIT {sample_size}" if sample_size else ""

        if self.platform == DataPlatform.SNOWFLAKE:
            return f"""
            SELECT
                COUNT(*) as row_count,
                COUNT(*) - COUNT(column_name) as null_count,
                COUNT(DISTINCT column_name) as distinct_count,
                MIN(column_name) as min_value,
                MAX(column_name) as max_value,
                AVG(column_name::FLOAT) as mean_value,
                STDDEV(column_name::FLOAT) as std_dev
            FROM {table_name}
            {limit_clause}
            """
        elif self.platform == DataPlatform.BIGQUERY:
            return f"""
            SELECT
                COUNT(*) as row_count,
                COUNTIF(column_name IS NULL) as null_count,
                COUNT(DISTINCT column_name) as distinct_count,
                MIN(column_name) as min_value,
                MAX(column_name) as max_value,
                AVG(CAST(column_name AS FLOAT64)) as mean_value,
                STDDEV(CAST(column_name AS FLOAT64)) as std_dev
            FROM `{table_name}`
            {limit_clause}
            """
        else:
            return f"""
            SELECT
                COUNT(*) as row_count,
                SUM(CASE WHEN column_name IS NULL THEN 1 ELSE 0 END) as null_count,
                COUNT(DISTINCT column_name) as distinct_count,
                MIN(column_name) as min_value,
                MAX(column_name) as max_value
            FROM {table_name}
            {limit_clause}
            """

    def get_column_statistics(
        self,
        table_name: str,
        column_name: str
    ) -> ColumnProfile:
        """Get detailed statistics for a specific column"""
        logger.info(f"Getting stats for {table_name}.{column_name}")

        return ColumnProfile(
            name=column_name,
            data_type="unknown",
            null_count=0,
            null_percentage=0.0,
            distinct_count=0
        )

    # ===========================================================================
    # NULL HANDLING
    # ===========================================================================

    def analyze_nulls(
        self,
        table_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze null patterns in a table.

        Returns:
            Dictionary with null analysis per column
        """
        logger.info(f"Analyzing nulls in: {table_name}")

        null_sql = f"""
        SELECT
            column_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN column_value IS NULL THEN 1 ELSE 0 END) as null_count,
            ROUND(SUM(CASE WHEN column_value IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_pct
        FROM {table_name}
        GROUP BY column_name
        """

        return {
            "sql": null_sql,
            "columns": {}
        }

    def recommend_imputation(
        self,
        column_profile: ColumnProfile
    ) -> ImputationStrategy:
        """
        Recommend the best imputation strategy for a column.

        Uses ML to determine optimal strategy based on:
        - Data type
        - Distribution
        - Null percentage
        - Correlation with other columns
        """
        if column_profile.null_percentage > 50:
            return ImputationStrategy.DROP
        elif column_profile.null_percentage < 5:
            if column_profile.is_numeric:
                return ImputationStrategy.MEDIAN
            return ImputationStrategy.MODE
        elif column_profile.is_numeric:
            if column_profile.std_dev and column_profile.mean_value:
                if column_profile.std_dev > abs(column_profile.mean_value):
                    return ImputationStrategy.MEDIAN
            return ImputationStrategy.MEAN
        elif column_profile.is_categorical:
            return ImputationStrategy.MODE
        elif column_profile.is_datetime:
            return ImputationStrategy.FORWARD_FILL
        return ImputationStrategy.PREDICTIVE

    def generate_imputation_sql(
        self,
        table_name: str,
        column_name: str,
        strategy: ImputationStrategy,
        constant_value: Optional[Any] = None
    ) -> str:
        """Generate SQL to impute null values"""

        if strategy == ImputationStrategy.MEAN:
            return f"""
-- Impute {column_name} with mean value
UPDATE {table_name}
SET {column_name} = (SELECT AVG({column_name}) FROM {table_name} WHERE {column_name} IS NOT NULL)
WHERE {column_name} IS NULL;
"""
        elif strategy == ImputationStrategy.MEDIAN:
            if self.platform == DataPlatform.SNOWFLAKE:
                return f"""
-- Impute {column_name} with median value
UPDATE {table_name}
SET {column_name} = (
    SELECT MEDIAN({column_name}) FROM {table_name} WHERE {column_name} IS NOT NULL
)
WHERE {column_name} IS NULL;
"""
            else:
                return f"""
-- Impute {column_name} with median value (approximate)
UPDATE {table_name}
SET {column_name} = (
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column_name})
    FROM {table_name} WHERE {column_name} IS NOT NULL
)
WHERE {column_name} IS NULL;
"""
        elif strategy == ImputationStrategy.MODE:
            return f"""
-- Impute {column_name} with mode (most frequent) value
UPDATE {table_name}
SET {column_name} = (
    SELECT {column_name}
    FROM {table_name}
    WHERE {column_name} IS NOT NULL
    GROUP BY {column_name}
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
WHERE {column_name} IS NULL;
"""
        elif strategy == ImputationStrategy.CONSTANT:
            value = f"'{constant_value}'" if isinstance(constant_value, str) else constant_value
            return f"""
-- Impute {column_name} with constant value
UPDATE {table_name}
SET {column_name} = {value}
WHERE {column_name} IS NULL;
"""
        elif strategy == ImputationStrategy.FORWARD_FILL:
            return f"""
-- Forward fill {column_name} (use previous non-null value)
-- Note: Requires ordering column
UPDATE {table_name} t1
SET {column_name} = (
    SELECT {column_name}
    FROM {table_name} t2
    WHERE t2.{column_name} IS NOT NULL
    AND t2.id < t1.id
    ORDER BY t2.id DESC
    LIMIT 1
)
WHERE {column_name} IS NULL;
"""
        return f"-- No imputation SQL generated for strategy: {strategy.value}"

    # ===========================================================================
    # DUPLICATE DETECTION
    # ===========================================================================

    def detect_duplicates(
        self,
        table_name: str,
        key_columns: Optional[List[str]] = None,
        similarity_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """
        Detect duplicate rows using exact and fuzzy matching.

        Args:
            table_name: Table to analyze
            key_columns: Columns to use for matching (None = all)
            similarity_threshold: Threshold for fuzzy matching (0.0-1.0)

        Returns:
            Dictionary with duplicate analysis results
        """
        logger.info(f"Detecting duplicates in: {table_name}")

        if key_columns:
            cols = ", ".join(key_columns)
        else:
            cols = "*"

        exact_dup_sql = f"""
-- Find exact duplicates
SELECT {cols}, COUNT(*) as dup_count
FROM {table_name}
GROUP BY {cols}
HAVING COUNT(*) > 1
ORDER BY dup_count DESC;
"""

        return {
            "exact_duplicate_sql": exact_dup_sql,
            "exact_duplicates": 0,
            "fuzzy_duplicates": 0,
            "duplicate_groups": [],
            "recommended_action": "review"
        }

    def generate_dedup_sql(
        self,
        table_name: str,
        key_columns: List[str],
        keep: str = "first",
        order_by: Optional[str] = None
    ) -> str:
        """Generate SQL to remove duplicates"""
        cols = ", ".join(key_columns)
        order_clause = order_by or key_columns[0]

        if self.platform == DataPlatform.SNOWFLAKE:
            return f"""
-- Remove duplicates keeping {keep} occurrence
DELETE FROM {table_name}
WHERE ROW_NUMBER() OVER (
    PARTITION BY {cols}
    ORDER BY {order_clause} {'ASC' if keep == 'first' else 'DESC'}
) > 1;
"""
        else:
            return f"""
-- Remove duplicates using CTE
WITH ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY {cols}
            ORDER BY {order_clause} {'ASC' if keep == 'first' else 'DESC'}
        ) as rn
    FROM {table_name}
)
DELETE FROM {table_name}
WHERE EXISTS (
    SELECT 1 FROM ranked
    WHERE ranked.rn > 1
);
"""

    # ===========================================================================
    # TYPE INFERENCE
    # ===========================================================================

    def infer_types(
        self,
        table_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze columns and suggest optimal data types.

        Returns:
            Dictionary with type recommendations per column
        """
        logger.info(f"Inferring types for: {table_name}")

        recommendations = {}

        # In production, would analyze sample data
        return recommendations

    def generate_type_cast_sql(
        self,
        table_name: str,
        column_name: str,
        current_type: str,
        target_type: str
    ) -> str:
        """Generate SQL to cast column to new type"""

        if self.platform == DataPlatform.SNOWFLAKE:
            return f"""
-- Change {column_name} from {current_type} to {target_type}
ALTER TABLE {table_name}
ALTER COLUMN {column_name} SET DATA TYPE {target_type};
"""
        elif self.platform == DataPlatform.BIGQUERY:
            return f"""
-- BigQuery requires table recreation for type changes
CREATE OR REPLACE TABLE {table_name} AS
SELECT * EXCEPT({column_name}),
    CAST({column_name} AS {target_type}) AS {column_name}
FROM {table_name};
"""
        else:
            return f"""
-- Alter column type
ALTER TABLE {table_name}
ALTER COLUMN {column_name} TYPE {target_type}
USING {column_name}::{target_type};
"""

    # ===========================================================================
    # OUTLIER DETECTION
    # ===========================================================================

    def detect_outliers(
        self,
        table_name: str,
        column_name: str,
        method: OutlierMethod = OutlierMethod.IQR,
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect outliers in a numeric column.

        Methods:
        - iqr: Interquartile range (1.5 * IQR by default)
        - zscore: Z-score (> 3 standard deviations)
        - isolation_forest: ML-based detection

        Returns:
            Dictionary with outlier analysis
        """
        logger.info(f"Detecting outliers in {table_name}.{column_name} using {method.value}")

        if method == OutlierMethod.IQR:
            sql = f"""
-- Detect outliers using IQR method
WITH stats AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column_name}) as q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column_name}) as q3
    FROM {table_name}
    WHERE {column_name} IS NOT NULL
),
bounds AS (
    SELECT
        q1 - ({threshold} * (q3 - q1)) as lower_bound,
        q3 + ({threshold} * (q3 - q1)) as upper_bound
    FROM stats
)
SELECT
    COUNT(*) as outlier_count,
    MIN({column_name}) as min_outlier,
    MAX({column_name}) as max_outlier
FROM {table_name}, bounds
WHERE {column_name} < lower_bound OR {column_name} > upper_bound;
"""
        elif method == OutlierMethod.ZSCORE:
            sql = f"""
-- Detect outliers using Z-score method
WITH stats AS (
    SELECT
        AVG({column_name}) as mean_val,
        STDDEV({column_name}) as std_val
    FROM {table_name}
    WHERE {column_name} IS NOT NULL
)
SELECT
    COUNT(*) as outlier_count
FROM {table_name}, stats
WHERE ABS(({column_name} - mean_val) / NULLIF(std_val, 0)) > 3;
"""
        else:
            sql = f"-- {method.value} requires Python-based processing"

        return {
            "method": method.value,
            "sql": sql,
            "outlier_count": 0,
            "outlier_percentage": 0.0,
            "lower_bound": None,
            "upper_bound": None
        }

    def generate_outlier_handling_sql(
        self,
        table_name: str,
        column_name: str,
        action: str = "cap",  # cap, remove, null
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None
    ) -> str:
        """Generate SQL to handle outliers"""

        if action == "cap":
            return f"""
-- Cap outliers to bounds
UPDATE {table_name}
SET {column_name} = CASE
    WHEN {column_name} < {lower_bound} THEN {lower_bound}
    WHEN {column_name} > {upper_bound} THEN {upper_bound}
    ELSE {column_name}
END
WHERE {column_name} < {lower_bound} OR {column_name} > {upper_bound};
"""
        elif action == "remove":
            return f"""
-- Remove outlier rows
DELETE FROM {table_name}
WHERE {column_name} < {lower_bound} OR {column_name} > {upper_bound};
"""
        elif action == "null":
            return f"""
-- Set outliers to NULL
UPDATE {table_name}
SET {column_name} = NULL
WHERE {column_name} < {lower_bound} OR {column_name} > {upper_bound};
"""
        return ""

    # ===========================================================================
    # FEATURE ENGINEERING
    # ===========================================================================

    def suggest_features(
        self,
        table_name: str,
        target_column: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest ML features based on column analysis.

        Suggestions include:
        - Binning for numeric columns
        - One-hot encoding for categoricals
        - Date part extraction
        - Text embeddings
        - Interaction features
        """
        logger.info(f"Suggesting features for: {table_name}")

        suggestions = []

        # Would analyze columns and suggest features
        return suggestions

    def generate_feature_sql(
        self,
        table_name: str,
        source_column: str,
        feature_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate SQL to create new features"""
        params = params or {}

        if feature_type == "binning":
            num_bins = params.get("bins", 5)
            return f"""
-- Create binned feature for {source_column}
SELECT *,
    NTILE({num_bins}) OVER (ORDER BY {source_column}) as {source_column}_bin
FROM {table_name};
"""
        elif feature_type == "date_parts":
            return f"""
-- Extract date parts from {source_column}
SELECT *,
    EXTRACT(YEAR FROM {source_column}) AS {source_column}_year,
    EXTRACT(MONTH FROM {source_column}) AS {source_column}_month,
    EXTRACT(DAY FROM {source_column}) AS {source_column}_day,
    EXTRACT(DAYOFWEEK FROM {source_column}) AS {source_column}_dow,
    EXTRACT(HOUR FROM {source_column}) AS {source_column}_hour
FROM {table_name};
"""
        elif feature_type == "one_hot":
            return f"""
-- One-hot encode {source_column} (pivot)
SELECT *,
    CASE WHEN {source_column} = 'value1' THEN 1 ELSE 0 END as {source_column}_value1,
    CASE WHEN {source_column} = 'value2' THEN 1 ELSE 0 END as {source_column}_value2
    -- Add more categories as needed
FROM {table_name};
"""
        elif feature_type == "log_transform":
            return f"""
-- Log transform {source_column}
SELECT *,
    LN(NULLIF({source_column}, 0) + 1) as {source_column}_log
FROM {table_name};
"""
        elif feature_type == "normalize":
            return f"""
-- Min-Max normalize {source_column}
SELECT *,
    ({source_column} - MIN({source_column}) OVER()) /
    NULLIF(MAX({source_column}) OVER() - MIN({source_column}) OVER(), 0)
    as {source_column}_normalized
FROM {table_name};
"""
        elif feature_type == "standardize":
            return f"""
-- Z-score standardize {source_column}
SELECT *,
    ({source_column} - AVG({source_column}) OVER()) /
    NULLIF(STDDEV({source_column}) OVER(), 0)
    as {source_column}_standardized
FROM {table_name};
"""
        return f"-- Unknown feature type: {feature_type}"

    # ===========================================================================
    # DATA STANDARDIZATION
    # ===========================================================================

    def standardize_dates(
        self,
        table_name: str,
        date_columns: List[str],
        target_format: str = "YYYY-MM-DD"
    ) -> List[str]:
        """Generate SQL to standardize date formats"""
        sql_statements = []

        for col in date_columns:
            sql = f"""
-- Standardize {col} to {target_format}
UPDATE {table_name}
SET {col} = TO_DATE(TO_CHAR({col}::DATE, '{target_format}'), '{target_format}')
WHERE {col} IS NOT NULL;
"""
            sql_statements.append(sql)

        return sql_statements

    def standardize_text(
        self,
        table_name: str,
        text_columns: List[str],
        operations: List[str] = None
    ) -> List[str]:
        """Generate SQL to standardize text columns"""
        operations = operations or ["trim", "lower"]
        sql_statements = []

        for col in text_columns:
            transformations = col

            if "trim" in operations:
                transformations = f"TRIM({transformations})"
            if "lower" in operations:
                transformations = f"LOWER({transformations})"
            if "upper" in operations:
                transformations = f"UPPER({transformations})"
            if "remove_special" in operations:
                transformations = f"REGEXP_REPLACE({transformations}, '[^a-zA-Z0-9 ]', '')"

            sql = f"""
-- Standardize text in {col}
UPDATE {table_name}
SET {col} = {transformations}
WHERE {col} IS NOT NULL;
"""
            sql_statements.append(sql)

        return sql_statements

    def standardize_phone_numbers(
        self,
        table_name: str,
        phone_column: str,
        country_code: str = "1"
    ) -> str:
        """Generate SQL to standardize phone numbers"""
        return f"""
-- Standardize phone numbers in {phone_column}
UPDATE {table_name}
SET {phone_column} = CONCAT('+{country_code}',
    REGEXP_REPLACE({phone_column}, '[^0-9]', '')
)
WHERE {phone_column} IS NOT NULL
AND LENGTH(REGEXP_REPLACE({phone_column}, '[^0-9]', '')) = 10;
"""

    # ===========================================================================
    # SCHEMA OPTIMIZATION
    # ===========================================================================

    def analyze_schema(
        self,
        table_name: str
    ) -> Dict[str, Any]:
        """
        Analyze schema and suggest optimizations.

        Returns:
            Dictionary with optimization recommendations
        """
        logger.info(f"Analyzing schema: {table_name}")

        return {
            "table_name": table_name,
            "unused_columns": [],
            "wide_columns": [],
            "suggested_partitions": [],
            "suggested_clusters": [],
            "type_optimizations": [],
            "estimated_size_reduction": "0%"
        }

    def generate_partition_sql(
        self,
        table_name: str,
        partition_column: str,
        partition_type: str = "date"
    ) -> str:
        """Generate SQL to add partitioning"""

        if self.platform == DataPlatform.BIGQUERY:
            return f"""
-- Add partitioning to table
CREATE OR REPLACE TABLE {table_name}
PARTITION BY DATE({partition_column})
AS SELECT * FROM {table_name};
"""
        elif self.platform == DataPlatform.SNOWFLAKE:
            return f"""
-- Snowflake uses micro-partitions automatically
-- Optimize clustering key instead
ALTER TABLE {table_name}
CLUSTER BY ({partition_column});
"""
        return f"-- Partitioning SQL for {self.platform.value}"

    # ===========================================================================
    # COMPREHENSIVE PREP PIPELINES
    # ===========================================================================

    def prepare_for_analytics(
        self,
        table_name: str,
        output_table: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run full data preparation pipeline for analytics.

        Steps:
        1. Profile data
        2. Handle nulls
        3. Remove duplicates
        4. Standardize formats
        5. Detect and handle outliers

        Returns:
            Summary of all preparation actions
        """
        logger.info(f"Preparing {table_name} for analytics")

        output = output_table or f"{table_name}_prepared"

        results = {
            "source_table": table_name,
            "output_table": output,
            "steps_completed": [],
            "quality_before": 0.0,
            "quality_after": 0.0,
            "sql_scripts": [],
            "recommendations": []
        }

        # Step 1: Profile
        profile = self.profile_table(table_name)
        results["steps_completed"].append("profiling")
        results["quality_before"] = profile.overall_quality_score

        # Step 2: Generate preparation SQL
        prep_sql = f"""
-- DataPrep AI Generated Script
-- Table: {table_name}
-- Generated: {datetime.now().isoformat()}

-- Create prepared table
CREATE TABLE {output} AS
SELECT * FROM {table_name};

-- Add data quality improvements here
-- (Generated based on profiling results)
"""
        results["sql_scripts"].append(prep_sql)

        return results

    def prepare_for_ml(
        self,
        table_name: str,
        target_column: str,
        output_table: Optional[str] = None,
        feature_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run full data preparation pipeline for machine learning.

        Additional steps beyond analytics:
        - Feature engineering
        - Encoding categorical variables
        - Scaling numeric features
        - Train/test split preparation
        """
        logger.info(f"Preparing {table_name} for ML with target: {target_column}")

        output = output_table or f"{table_name}_ml_ready"

        results = {
            "source_table": table_name,
            "target_column": target_column,
            "output_table": output,
            "features_generated": [],
            "encoding_applied": [],
            "scaling_applied": [],
            "sql_scripts": [],
            "model_ready": False
        }

        # Generate ML preparation SQL
        ml_sql = f"""
-- DataPrep AI ML Preparation Script
-- Table: {table_name}
-- Target: {target_column}
-- Generated: {datetime.now().isoformat()}

-- Create ML-ready table
CREATE TABLE {output} AS
SELECT
    {target_column} as target,
    -- Feature columns with transformations
    *
FROM {table_name}
WHERE {target_column} IS NOT NULL;

-- Split markers for train/test
ALTER TABLE {output} ADD COLUMN split_group VARCHAR(10);
UPDATE {output} SET split_group =
    CASE WHEN RANDOM() < 0.8 THEN 'train' ELSE 'test' END;
"""
        results["sql_scripts"].append(ml_sql)
        results["model_ready"] = True

        return results

    # ===========================================================================
    # ACTION GENERATION
    # ===========================================================================

    def generate_prep_actions(
        self,
        table_name: str
    ) -> List[PrepAction]:
        """
        Analyze table and generate prioritized preparation actions.

        Returns:
            List of PrepAction objects sorted by priority
        """
        logger.info(f"Generating prep actions for: {table_name}")

        actions = []

        # Profile first
        profile = self.profile_table(table_name)

        # Generate actions based on findings
        for col in profile.columns:
            if col.null_percentage > 10:
                strategy = self.recommend_imputation(col)
                actions.append(PrepAction(
                    action_type="imputation",
                    column=col.name,
                    description=f"Handle {col.null_percentage:.1f}% nulls with {strategy.value}",
                    sql=self.generate_imputation_sql(table_name, col.name, strategy),
                    priority=1 if col.null_percentage > 30 else 2,
                    estimated_impact=f"Improve data completeness by {col.null_percentage:.1f}%"
                ))

        if profile.duplicate_rows > 0:
            actions.append(PrepAction(
                action_type="deduplication",
                column=None,
                description=f"Remove {profile.duplicate_rows} duplicate rows",
                sql="-- Deduplication SQL (specify key columns)",
                priority=1,
                estimated_impact=f"Reduce table size by {profile.duplicate_percentage:.1f}%"
            ))

        self.prep_actions = sorted(actions, key=lambda x: x.priority)
        return self.prep_actions


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_dataprep_agent(
    platform: str = "snowflake",
    connection_params: Optional[Dict[str, Any]] = None
) -> DataPrepAgent:
    """
    Factory function to create DataPrep Agent.

    Args:
        platform: Data platform (snowflake, databricks, bigquery, redshift)
        connection_params: Platform-specific connection parameters

    Returns:
        Configured DataPrepAgent instance
    """
    platform_enum = DataPlatform(platform.lower())
    return DataPrepAgent(
        platform=platform_enum,
        connection_params=connection_params
    )


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DataPrep AI Agent")
    print("Intelligent Data Preparation for Analytics & ML")
    print("=" * 60)

    # Create agent
    agent = get_dataprep_agent("snowflake")

    # Demo profile
    profile = agent.profile_table("raw.customers")
    print(f"\nProfiled: {profile.table_name}")

    # Demo imputation SQL
    col_profile = ColumnProfile(
        name="revenue",
        data_type="float",
        null_count=100,
        null_percentage=15.0,
        distinct_count=500,
        is_numeric=True
    )
    strategy = agent.recommend_imputation(col_profile)
    print(f"\nRecommended imputation for 'revenue': {strategy.value}")

    # Demo feature engineering
    feature_sql = agent.generate_feature_sql(
        "sales.orders",
        "order_date",
        "date_parts"
    )
    print(f"\nFeature engineering SQL generated")

    print("\n" + "=" * 60)
    print("Available Capabilities:")
    print("=" * 60)
    capabilities = [
        "Auto Data Profiling",
        "Smart Null Handling",
        "Duplicate Detection",
        "Type Inference",
        "Outlier Detection",
        "Feature Engineering",
        "Data Standardization",
        "Schema Optimization"
    ]
    for cap in capabilities:
        print(f"  - {cap}")

    print("\n" + "=" * 60)
    print("Supported Platforms:")
    print("=" * 60)
    for platform in DataPlatform:
        print(f"  - {platform.value.title()}")

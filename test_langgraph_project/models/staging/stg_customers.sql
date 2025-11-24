-- dbt model: stg_customers
-- Source: dbo.customers

{{ config(materialized='view') }}

SELECT
    *
FROM {{ source('mssql', 'customers') }}

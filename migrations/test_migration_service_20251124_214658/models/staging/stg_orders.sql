-- dbt model: stg_orders
-- Source: dbo.orders

{{ config(materialized='view') }}

SELECT
    *
FROM {{ source('mssql', 'orders') }}

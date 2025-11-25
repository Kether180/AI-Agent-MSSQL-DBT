-- dbt model: stg_vw_customer_orders
-- Source: dbo.vw_customer_orders

{{ config(materialized='view') }}

SELECT
    *
FROM {{ source('mssql', 'vw_customer_orders') }}

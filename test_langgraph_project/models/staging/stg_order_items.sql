-- dbt model: stg_order_items
-- Source: dbo.order_items

{{ config(materialized='view') }}

SELECT
    *
FROM {{ source('mssql', 'order_items') }}

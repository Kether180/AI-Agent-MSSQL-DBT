-- dbt model: stg_products
-- Source: dbo.products

{{ config(materialized='view') }}

SELECT
    *
FROM {{ source('mssql', 'products') }}

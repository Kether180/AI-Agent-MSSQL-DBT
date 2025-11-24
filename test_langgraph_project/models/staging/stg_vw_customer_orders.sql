{{
    config(
        materialized='view'
    )
}}

-- This model replicates the logic from MSSQL view: dbo.vw_customer_orders
-- TODO: Replace with actual view logic

select * from {{ source('mssql', 'vw_customer_orders') }}

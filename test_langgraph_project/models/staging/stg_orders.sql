{{
    config(
        materialized='table'
    )
}}

with source as (
    select * from {{ source('mssql', 'orders') }}
),

renamed as (
    select
        order_id,
    customer_id,
    order_date,
    total_amount,
    status
    from source
)

select * from renamed

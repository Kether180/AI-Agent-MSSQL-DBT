{{
    config(
        materialized='table'
    )
}}

with source as (
    select * from {{ source('mssql', 'order_items') }}
),

renamed as (
    select
        order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price
    from source
)

select * from renamed

{{
    config(
        materialized='table'
    )
}}

with source as (
    select * from {{ source('mssql', 'products') }}
),

renamed as (
    select
        product_id,
    product_name,
    category,
    price
    from source
)

select * from renamed

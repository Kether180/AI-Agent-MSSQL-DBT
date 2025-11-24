{{
    config(
        materialized='table'
    )
}}

with source as (
    select * from {{ source('mssql', 'customers') }}
),

renamed as (
    select
        customer_id,
    customer_name,
    email,
    created_at,
    updated_at
    from source
)

select * from renamed

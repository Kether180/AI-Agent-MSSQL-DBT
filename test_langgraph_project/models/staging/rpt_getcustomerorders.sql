{{
    config(
        materialized='table'
    )
}}

-- This model replicates the logic from stored procedure: dbo.usp_GetCustomerOrders
-- Original procedure definition:
-- 
-- CREATE PROCEDURE dbo.usp_GetCustomerOrders
--     @customer_id INT
-- AS
-- BEGIN
--     SELECT 
--         o.order_id,
--         o.order_date,
--         o.total_amount,
--         o.status
--     FROM dbo.orders o
--     WHERE o.customer_id = @customer_id
--     ORDER BY o.order_date DESC
-- END
--                 

-- TODO: Extract and convert SELECT logic
select 1 as placeholder

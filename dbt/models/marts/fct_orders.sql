with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

item_agg as (
    select
        order_id,
        count(*) as item_count,
        sum(sale_price) as revenue
    from order_items
    group by 1
)

select
    o.order_id,
    o.user_id,
    o.order_status,
    o.gender,
    o.created_at,
    o.shipped_at,
    o.delivered_at,
    o.returned_at,
    o.num_of_item,
    coalesce(ia.item_count, 0) as item_count,
    coalesce(ia.revenue, 0) as revenue
from orders o
left join item_agg ia on o.order_id = ia.order_id

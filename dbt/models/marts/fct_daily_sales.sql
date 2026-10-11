with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
)

select
    date(o.created_at) as order_date,
    p.category,
    count(distinct oi.order_id) as order_count,
    sum(oi.sale_price) as revenue
from order_items oi
inner join orders o on oi.order_id = o.order_id
inner join products p on oi.product_id = p.product_id
group by 1, 2

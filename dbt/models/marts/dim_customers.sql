with users as (
    select * from {{ ref('stg_users') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
),

order_agg as (
    select
        user_id,
        min(created_at) as first_order_date,
        max(created_at) as last_order_date,
        count(*) as lifetime_orders,
        sum(revenue) as lifetime_revenue
    from orders
    group by 1
)

select
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    u.age,
    u.gender,
    u.state,
    u.country,
    u.traffic_source,
    u.created_at as signup_at,
    oa.first_order_date,
    oa.last_order_date,
    coalesce(oa.lifetime_orders, 0) as lifetime_orders,
    coalesce(oa.lifetime_revenue, 0) as lifetime_revenue
from users u
left join order_agg oa on u.user_id = oa.user_id

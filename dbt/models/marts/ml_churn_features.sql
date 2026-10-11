-- Churn is defined as: no order in the last 90 days (as of this run's
-- CURRENT_DATE()). All features below are computed against that same
-- snapshot date, so nothing here is computed from "future" data relative
-- to the label — every row in a given dbt run shares one reference point.
with customers as (
    select * from {{ ref('dim_customers') }}
),

category_purchases as (
    select
        o.user_id,
        p.category,
        count(*) as purchase_count
    from {{ ref('stg_order_items') }} oi
    inner join {{ ref('stg_orders') }} o on oi.order_id = o.order_id
    inner join {{ ref('stg_products') }} p on oi.product_id = p.product_id
    group by 1, 2
),

category_agg as (
    select
        user_id,
        count(distinct category) as distinct_categories,
        array_agg(category order by purchase_count desc limit 1)[offset(0)] as top_category
    from category_purchases
    group by 1
)

select
    c.user_id,
    c.lifetime_orders as frequency,
    c.lifetime_revenue as monetary,
    date_diff(current_date(), date(c.last_order_date), day) as recency_days,
    coalesce(ca.distinct_categories, 0) as distinct_categories,
    ca.top_category,
    (c.lifetime_orders = 0) as never_ordered,
    (
        c.lifetime_orders = 0
        or date_diff(current_date(), date(c.last_order_date), day) > 90
    ) as is_churned
from customers c
left join category_agg ca on c.user_id = ca.user_id

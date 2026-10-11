with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

holidays as (
    -- Some dates have multiple state-specific holidays (e.g. a different
    -- "Labour Day" per state on the same date) — dedupe to one row per
    -- date so the join below can't fan out fct_daily_sales.
    select
        holiday_date,
        string_agg(distinct holiday_name, ', ') as holiday_name
    from {{ ref('stg_holidays') }}
    group by 1
),

daily as (
    select
        date(o.created_at) as order_date,
        p.category,
        count(distinct oi.order_id) as order_count,
        sum(oi.sale_price) as revenue
    from order_items oi
    inner join orders o on oi.order_id = o.order_id
    inner join products p on oi.product_id = p.product_id
    group by 1, 2
)

select
    d.order_date,
    d.category,
    d.order_count,
    d.revenue,
    h.holiday_date is not null as is_holiday,
    h.holiday_name
from daily d
left join holidays h on d.order_date = h.holiday_date

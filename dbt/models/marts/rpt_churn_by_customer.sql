-- Convenience view for the dashboard: joins the ML-written churn_scores
-- table to customer attributes so Looker Studio can chart "churn risk by
-- segment" (state, traffic_source, age) without a manual blend.
with customers as (
    select * from {{ ref('dim_customers') }}
),

scores as (
    select * from {{ source('ml', 'churn_scores') }}
)

select
    c.user_id,
    c.state,
    c.country,
    c.traffic_source,
    c.age,
    c.lifetime_orders,
    c.lifetime_revenue,
    s.churn_score,
    s.is_churned_label,
    s.scored_at
from customers c
inner join scores s on c.user_id = s.user_id

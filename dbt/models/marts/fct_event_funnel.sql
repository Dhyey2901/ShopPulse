-- Distinct users reaching each stage of the shopping funnel. stage_order
-- lets the dashboard sort the funnel correctly (home -> product -> cart
-- -> purchase) instead of alphabetically.
with events as (
    select * from {{ ref('stg_events') }}
),

funnel_stages as (
    select 'home' as event_type, 1 as stage_order
    union all select 'product', 2
    union all select 'cart', 3
    union all select 'purchase', 4
)

select
    f.event_type,
    f.stage_order,
    count(distinct e.user_id) as distinct_users,
    count(*) as event_count
from funnel_stages f
left join events e on e.event_type = f.event_type
group by 1, 2

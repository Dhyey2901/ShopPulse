with source as (
    select * from {{ source('raw', 'holidays') }}
)

select
    date as holiday_date,
    local_name,
    name as holiday_name,
    country_code
from source
where country_code = 'AU'

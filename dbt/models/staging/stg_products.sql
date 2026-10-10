with source as (
    select * from {{ source('thelook_ecommerce', 'products') }}
)

select
    id as product_id,
    name as product_name,
    brand,
    category,
    department,
    sku,
    cost,
    retail_price,
    distribution_center_id
from source

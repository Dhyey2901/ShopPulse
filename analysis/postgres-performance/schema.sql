-- Schema for the local Postgres performance exercise.
-- Mirrors orders/order_items from bigquery-public-data.thelook_ecommerce,
-- loaded via \copy from a BigQuery export (see README.md in this folder).

drop table if exists order_items;
drop table if exists orders;

create table orders (
    order_id integer primary key,
    user_id integer not null,
    status text,
    gender text,
    created_at timestamp,
    shipped_at timestamp,
    delivered_at timestamp,
    returned_at timestamp,
    num_of_item integer
);

create table order_items (
    id integer primary key,
    order_id integer not null,
    user_id integer not null,
    product_id integer not null,
    inventory_item_id integer,
    status text,
    created_at timestamp,
    shipped_at timestamp,
    delivered_at timestamp,
    returned_at timestamp,
    sale_price numeric
);

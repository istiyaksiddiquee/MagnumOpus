{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'append'
    )
}}

{% set tables = get_source_tables('datalake') %}

{% for t in tables %}
select
  cast (vendor_id as BIGINT) as vendor_id,
  cast (lpep_pickup_datetime AS TIMESTAMP(6)) as pickup_datetime,
  cast (lpep_dropoff_datetime AS TIMESTAMP(6)) as dropoff_datetime,
  cast (rate_code_id as BIGINT) as rate_code_id,
  cast (pu_location_id as BIGINT) as pickup_locationid,
  cast (do_location_id as BIGINT) as dropoff_locationid,
  cast (passenger_count as BIGINT) as passenger_count,
  cast (trip_distance as DOUBLE) as trip_distance,
  cast (trip_type as BIGINT) as trip_type,
  cast (fare_amount as DOUBLE) as fare_amount,
  cast (extra as DOUBLE) as extra,
  cast (mta_tax as DOUBLE) as mta_tax,
  cast (tip_amount as DOUBLE) as tip_amount,
  cast (tolls_amount as DOUBLE) as tolls_amount,
  cast (ehail_fee as BIGINT) as ehail_fee,
  cast (improvement_surcharge as DOUBLE) as improvement_surcharge,
  cast (total_amount as DOUBLE) as total_amount,
  cast (payment_type as BIGINT) as payment_type,
  cast (congestion_surcharge as DOUBLE) as congestion_surcharge,
  cast (cbd_congestion_fee as DOUBLE) as cbd_congestion_fee
from {{ source('datalake', t) }}
{% if not loop.last %}
union all
{% endif %}
{% endfor %}
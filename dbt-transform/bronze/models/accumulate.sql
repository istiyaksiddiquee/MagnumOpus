{{
    config(
        materialized = 'incremental',
        incremental_strategy='append'
    )
}}

select
  cast (vendorid as BIGINT) as vendorid, 
  cast (ratecodeid as BIGINT) as ratecodeid,
  cast (pulocationid as BIGINT) as pickup_locationid,
  cast (dolocationid as BIGINT) as dropoff_locationid,
  cast (lpep_pickup_datetime AS TIMESTAMP(6)) as pickup_datetime,
  cast (lpep_dropoff_datetime AS TIMESTAMP(6)) as dropoff_datetime,
  store_and_fwd_flag,
  cast (passenger_count as BIGINT) as passenger_count,
  cast (trip_distance as DOUBLE) as trip_distance,
  cast (trip_type as BIGINT) as trip_type,
  cast (fare_amount as DOUBLE) as fare_amount,
  cast (extra as DOUBLE) as extra,
  cast(mta_tax as DOUBLE) as mta_tax,
  cast (tip_amount as DOUBLE) as tip_amount,
  cast (tolls_amount as DOUBLE) as tolls_amount,
  cast (ehail_fee as BIGINT) as ehail_fee,
  cast (improvement_surcharge as DOUBLE) as improvement_surcharge,
  cast (total_amount as DOUBLE) as total_amount,
  cast (payment_type as BIGINT) as payment_type,
  cast (congestion_surcharge as DOUBLE) as congestion_surcharge
from {{ source('postgres', var('db_name')) }}
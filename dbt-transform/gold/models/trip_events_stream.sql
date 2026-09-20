{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'append'
    )
}}

-- This table is meant to be tailed downstream into a Fluss log table, so it
-- must stay append-only: every dbt run should emit ONLY trips that haven't
-- been emitted yet, never the full history again. That's why this uses a
-- pickup_datetime high-water-mark filter instead of the "just reprocess
-- everything" approach used in bronze/silver — replaying the full table
-- into a log stream on every run would re-emit every historical trip as a
-- "new" event each time.

select
    trip_id,
    pickup_datetime,
    dropoff_datetime,
    trip_duration_minutes,

    pickup_locationid,
    pickup_borough,
    pickup_zone,
    dropoff_locationid,
    dropoff_borough,
    dropoff_zone,

    passenger_count,
    fare_amount,
    tip_amount,
    total_amount

from {{ source('silver_layer', 'cleaned_tlc') }}

{% if is_incremental() %}
where pickup_datetime > (select max(pickup_datetime) from {{ this }})
{% endif %}

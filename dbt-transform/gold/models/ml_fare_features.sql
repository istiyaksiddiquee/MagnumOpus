{{
    config(
        unique_key = 'trip_id'
    )
}}

-- Grain: one row per trip.
-- Target: fare_amount (the metered price) — NOT total_amount, which already
-- bakes in tip/tolls/surcharges and would make the target circular with
-- several of the columns below if those were kept as features.
--
-- Columns after fare_amount are candidates only. Anything derived from or
-- added after the ride is over (tip_amount, tolls_amount, extra, mta_tax,
-- improvement_surcharge, congestion_surcharge, total_amount, avg_speed_mph)
-- is intentionally left out here rather than included-then-flagged, since a
-- leaky column sitting in the table invites accidental use downstream.
-- payment_type is included as a debatable case: known before the ride ends,
-- but not causally related to price — keep it in your correlation pass and
-- decide.

select
    trip_id,
    pickup_datetime,          -- metadata for temporal train/test split, not a feature
    fare_amount,               -- target

    vendor_id,
    rate_code_id,
    trip_type,
    passenger_count,
    trip_distance,
    trip_duration_minutes,
    pickup_hour,
    pickup_day_of_week,
    is_weekend,

    pickup_locationid,
    pickup_borough,
    pickup_zone,
    dropoff_locationid,
    dropoff_borough,
    dropoff_zone,

    payment_type

from {{ source('silver_layer', 'cleaned_tlc') }}

{% if is_incremental() %}
where pickup_datetime > (select max(pickup_datetime) from {{ this }})
{% endif %}

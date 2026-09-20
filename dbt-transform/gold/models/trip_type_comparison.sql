-- trip_type is the reliable signal for street-hail vs. dispatch/e-hail —
-- ehail_fee itself is almost always 0/null in real TLC data, so it's not
-- useful as a grouping column on its own.

select
    trip_type_desc,
    count(*) as trip_count,
    avg(fare_amount) as avg_fare_amount,
    avg(trip_distance) as avg_trip_distance,
    avg(trip_duration_minutes) as avg_trip_duration_minutes,
    avg(tip_amount / nullif(fare_amount, 0)) as avg_tip_pct

from {{ source('silver_layer', 'cleaned_tlc') }}
group by trip_type_desc

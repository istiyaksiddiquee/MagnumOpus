-- Cumulative running totals per pickup borough/zone, ordered by pickup time.
-- Recomputed fully on each run (this is table-materialized, not incremental)
-- because a correct running total needs the full ordered history each time —
-- carrying forward a partial cumulative sum incrementally is easy to get
-- subtly wrong, and this table is small enough that a full rebuild is cheap.

select
    pickup_borough,
    pickup_zone,
    pickup_datetime,
    trip_id,

    count(*) over (
        partition by pickup_borough, pickup_zone
        order by pickup_datetime, trip_id
        rows between unbounded preceding and current row
    ) as running_trip_count,

    sum(fare_amount) over (
        partition by pickup_borough, pickup_zone
        order by pickup_datetime, trip_id
        rows between unbounded preceding and current row
    ) as running_total_fare,

    sum(total_amount) over (
        partition by pickup_borough, pickup_zone
        order by pickup_datetime, trip_id
        rows between unbounded preceding and current row
    ) as running_total_amount

from {{ source('silver_layer', 'cleaned_tlc') }}

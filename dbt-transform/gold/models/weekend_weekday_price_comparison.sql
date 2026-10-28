select
    is_weekend,
    count(*) as trip_count,
    avg(fare_amount) as avg_fare_amount,
    avg(total_amount) as avg_total_amount,
    avg(tip_amount) as avg_tip_amount,
    avg(trip_distance) as avg_trip_distance

from {{ source('silver_layer', 'cleaned_tlc') }}
group by is_weekend

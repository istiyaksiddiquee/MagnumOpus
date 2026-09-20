select
    pickup_borough,
    pickup_zone,
    count(*) as trip_count,
    avg(fare_amount / nullif(trip_distance, 0)) as avg_fare_per_mile

from {{ source('silver_layer', 'cleaned_tlc') }}
group by pickup_borough, pickup_zone

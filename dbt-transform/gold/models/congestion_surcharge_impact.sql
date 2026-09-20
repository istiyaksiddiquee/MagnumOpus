select
    case when congestion_surcharge > 0 then true else false end as has_congestion_surcharge,
    count(*) as trip_count,
    avg(fare_amount) as avg_fare_amount,
    avg(trip_duration_minutes) as avg_trip_duration_minutes,
    avg(trip_distance) as avg_trip_distance

from {{ source('silver_layer', 'cleaned_tlc') }}
group by case when congestion_surcharge > 0 then true else false end

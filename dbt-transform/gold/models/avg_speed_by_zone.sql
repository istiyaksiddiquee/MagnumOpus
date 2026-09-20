select
    pickup_borough,
    pickup_zone,
    count(*) as trip_count,
    avg(avg_speed_mph) as avg_speed_mph,
    avg(trip_distance) as avg_trip_distance

from {{ source('silver_layer', 'cleaned_tlc') }}
where avg_speed_mph is not null
group by pickup_borough, pickup_zone

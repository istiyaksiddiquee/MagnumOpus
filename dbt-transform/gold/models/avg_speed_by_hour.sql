select
    pickup_hour,
    count(*) as trip_count,
    avg(avg_speed_mph) as avg_speed_mph

from {{ source('silver_layer', 'cleaned_tlc') }}
where avg_speed_mph is not null
group by pickup_hour

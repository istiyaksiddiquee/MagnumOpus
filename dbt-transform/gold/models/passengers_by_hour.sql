select
    pickup_hour,
    count(*) as trip_count,
    avg(passenger_count) as avg_passenger_count,
    sum(passenger_count) as total_passengers

from {{ source('silver_layer', 'cleaned_tlc') }}
group by pickup_hour

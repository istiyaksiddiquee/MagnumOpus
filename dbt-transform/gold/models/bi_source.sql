{{
    config(
        materialized = 'incremental',
        incremental_strategy='append'
    )
}}

SELECT 
    *,
    extract(YEAR FROM dropoff_datetime) as dropoff_year,
    extract(MONTH FROM dropoff_datetime) as dropoff_month,
    extract(DAY FROM dropoff_datetime) as dropoff_day,
    extract(YEAR FROM pickup_datetime) as pickup_year,
    extract(MONTH FROM pickup_datetime) as pickup_month,
    extract(DAY FROM pickup_datetime) as pickup_day,
    date_diff('second', dropoff_datetime, pickup_datetime) as trip_duration,
    trip_distance*3600/date_diff('second', dropoff_datetime, pickup_datetime) as avg_speed,
    (CASE 
        WHEN total_amount=0 THEN 0 
        ELSE ROUND(tip_amount*100/total_amount, 2) END
    ) as tip_rate
from 
    {{ source('silver', 'cleaned_tlc') }}
select
    pickup_borough,
    pickup_zone,
    ratecode_desc,
    count(*) as trip_count,
    100.0 * count(*) / sum(count(*)) over (
        partition by pickup_borough, pickup_zone
    ) as pct_of_zone_trips

from {{ source('silver_layer', 'cleaned_tlc') }}
group by pickup_borough, pickup_zone, ratecode_desc

{{
    config(
        materialized = 'incremental',
        incremental_strategy = 'merge',
        unique_key = 'trip_id'
    )
}}

with source as (

    select *
    from {{ source('bronze_layer', 'accumulate') }}

),

quality_filtered as (

    select *
    from source
    where
        dropoff_datetime > pickup_datetime
        and trip_distance > 0
        and fare_amount >= 0
        and total_amount >= 0
        and passenger_count between 0 and 8

),

deduped as (

    select
        *,
        row_number() over (
            partition by
                vendorid,
                pickup_datetime,
                dropoff_datetime,
                pickup_locationid,
                dropoff_locationid
            order by pickup_datetime
        ) as rn
    from quality_filtered

),

final as (

    select
        to_hex(md5(to_utf8(concat(
            cast(vendorid as varchar), '|',
            cast(pickup_datetime as varchar), '|',
            cast(dropoff_datetime as varchar), '|',
            cast(pickup_locationid as varchar), '|',
            cast(dropoff_locationid as varchar)
        )))) as trip_id,

        vendorid,
        ratecodeid,
        case ratecodeid
            when 1 then 'Standard rate'
            when 2 then 'JFK'
            when 3 then 'Newark'
            when 4 then 'Nassau or Westchester'
            when 5 then 'Negotiated fare'
            when 6 then 'Group ride'
            else 'Unknown'
        end as ratecode_desc,

        pickup_locationid,
        pickup_zone.borough as pickup_borough,
        pickup_zone.zone as pickup_zone,
        pickup_zone.service_zone as pickup_service_zone,

        dropoff_locationid,
        dropoff_zone.borough as dropoff_borough,
        dropoff_zone.zone as dropoff_zone,
        dropoff_zone.service_zone as dropoff_service_zone,

        pickup_datetime,
        dropoff_datetime,
        date_diff('minute', pickup_datetime, dropoff_datetime) as trip_duration_minutes,
        hour(pickup_datetime) as pickup_hour,
        day_of_week(pickup_datetime) as pickup_day_of_week,
        case when day_of_week(pickup_datetime) in (6, 7) then true else false end as is_weekend,

        store_and_fwd_flag,
        passenger_count,
        trip_distance,
        case
            when date_diff('minute', pickup_datetime, dropoff_datetime) > 0
                then trip_distance / (date_diff('minute', pickup_datetime, dropoff_datetime) / 60.0)
            else null
        end as avg_speed_mph,

        trip_type,
        case trip_type
            when 1 then 'Street-hail'
            when 2 then 'Dispatch'
            else 'Unknown'
        end as trip_type_desc,

        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        ehail_fee,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,

        payment_type,
        case payment_type
            when 1 then 'Credit card'
            when 2 then 'Cash'
            when 3 then 'No charge'
            when 4 then 'Dispute'
            when 5 then 'Unknown'
            when 6 then 'Voided trip'
            else 'Unknown'
        end as payment_type_desc

    from deduped
    left join {{ ref('taxi_zone_lookup') }} as pickup_zone
        on deduped.pickup_locationid = pickup_zone.locationid
    left join {{ ref('taxi_zone_lookup') }} as dropoff_zone
        on deduped.dropoff_locationid = dropoff_zone.locationid
    where rn = 1

)

select * from final
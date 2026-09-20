-- Caveat to carry into any dashboard built on this: cash tips aren't
-- captured in TLC trip data, so cash trips will show near-zero tips here.
-- That's a data-capture gap, not evidence that cash customers tip less.

select
    payment_type_desc,
    count(*) as trip_count,
    avg(tip_amount / nullif(fare_amount, 0)) as avg_tip_pct,
    avg(tip_amount) as avg_tip_amount

from {{ source('silver_layer', 'cleaned_tlc') }}
group by payment_type_desc

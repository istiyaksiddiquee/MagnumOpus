{{
    config(
        materialized = 'incremental',
        incremental_strategy='append'
    )
}}

select 
    *
from {{ source('bronze', 'accumulate') }}
where 
		ratecodeid != -999 
	and  store_and_fwd_flag  != '-999'
	and  passenger_count  != -999
	and  payment_type != -999
	and  trip_type != -999
	and  congestion_surcharge  != -999
	and  ratecodeid != -999
	and  (dropoff_locationid between 1 and 263)
	and  (pickup_locationid  between 1 and 263)
	and  passenger_count > 0
	and  trip_distance >= 0
	and  fare_amount >= 0
	and  total_amount >= 0
	and  mta_tax >= 0
	and  tip_amount >= 0
	and  tolls_amount >= 0
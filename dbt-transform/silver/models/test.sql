{{
    config(
    materialized = 'view',
    )
}}

select 
    *
from {{ source('bronze', 'accumulate') }}
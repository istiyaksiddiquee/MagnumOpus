{{
    config(
        materialized = 'incremental',
        incremental_strategy='append'
    )
}}

SELECT 
    *
from 
    {{ source('silver', 'cleaned_tlc') }}
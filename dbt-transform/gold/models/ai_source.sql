{{
    config(
        materialized = 'table',
        on_table_exists = 'drop'
    )
}}

SELECT 
    *
from 
    {{ source('silver', 'cleaned_tlc') }}
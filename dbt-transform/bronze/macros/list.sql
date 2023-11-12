{% macro get_table_names() %}

{{ print("Running some_macro ") }}

{% set schema_list_query %}
    select 
      table_name 
    from 
      psql.information_schema.tables 
    where 
      table_schema = 'public'
{% endset %}

{% set results = run_query(schema_list_query) %}
{% if execute %}
{# Return the first column #}
{% set results_list = results.columns[0].values() %}
{{ print("macro output: " ~ results_list) }}
{{ return (results_list) }}
{% else %}
{% set results_list = 'nothing' %}
{% endif %}

{% endmacro %}
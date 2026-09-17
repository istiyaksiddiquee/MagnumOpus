{% macro get_table_names() %}

{{ print("Running some_macro ") }}

{% macro get_source_tables(source_name) %}
  {% set tables = [] %}
  {% for node in graph.sources.values() %}
    {% if node.source_name == source_name %}
      {% do tables.append(node.name) %}
    {% endif %}
  {% endfor %}
  {{ return(tables) }}
{% endmacro %}

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
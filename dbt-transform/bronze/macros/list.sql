{% macro get_source_tables(source_name) %}
  {% set tables = [] %}
  {% if execute %}
    {% for node in graph.sources.values() %}
      {% if node.source_name == source_name %}
        {% do tables.append(node.name) %}
      {% endif %}
    {% endfor %}
  {% endif %}
  {{ return(tables) }}
{% endmacro %}
 
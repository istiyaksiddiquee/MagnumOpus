FROM apache/airflow:3.1.5-python3.13

ENV AIRFLOW_HOME=/opt/airflow
WORKDIR $AIRFLOW_HOME

USER root
RUN apt-get update -qq && apt-get install libpq-dev python3-dev vim -qqq
# RUN python3 -m pip install airflow

# COPY ./scripts/entrypoint.sh scripts/entrypoint.sh
# RUN chmod +x scripts/entrypoint.sh
# RUN airflow db upgrade && airflow users create -r Admin -u admin -p admin -e admin@example.com -f admin -l airflow

USER $AIRFLOW_UID

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /opt/airflow/shared_data
# RUN chown airflow:airflow /opt/airflow/shared_data
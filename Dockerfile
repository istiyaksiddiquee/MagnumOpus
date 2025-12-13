FROM apache/airflow:2.7.3-python3.11

ENV AIRFLOW_HOME=/opt/airflow
WORKDIR $AIRFLOW_HOME

USER root
RUN apt-get update -qq && apt-get install libpq-dev python3-dev vim -qqq

COPY ./scripts/entrypoint.sh scripts/entrypoint.sh
RUN chmod +x scripts/entrypoint.sh
RUN airflow db upgrade && airflow users create -r Admin -u admin -p admin -e admin@example.com -f admin -l airflow

USER $AIRFLOW_UID

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
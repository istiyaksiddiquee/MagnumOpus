FROM apache/airflow:2.7.2

ENV AIRFLOW_HOME=/opt/airflow
WORKDIR $AIRFLOW_HOME

USER root
RUN apt-get update -qq && apt-get install vim -qqq

COPY scripts scripts
RUN chmod +x scripts

USER $AIRFLOW_UID

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
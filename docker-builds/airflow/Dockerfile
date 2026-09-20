FROM apache/airflow:3.3.1-python3.13

ENV AIRFLOW_HOME=/opt/airflow
WORKDIR $AIRFLOW_HOME

USER root
RUN apt-get update -qq && apt-get install -y -qq \
    libpq-dev python3-dev vim \
    build-essential pkg-config curl git \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rust \
    CARGO_HOME=/opt/rust/cargo \
    PATH=/opt/rust/cargo/bin:$PATH

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --default-toolchain stable --profile minimal \
    && chmod -R a+rX /opt/rust

COPY --chown=$AIRFLOW_UID:0 requirements.txt .

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir maturin
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /opt/airflow/shared_data && chown $AIRFLOW_UID:$AIRFLOW_UID /opt/airflow/shared_data

USER $AIRFLOW_UID
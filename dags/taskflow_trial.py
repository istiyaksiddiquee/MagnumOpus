import json
import pandas as pd
from airflow import DAG
from datetime import datetime
from airflow.decorators import task
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from pendulum import duration

@task
def scrape_data_from_source(year_month_duo: str):
    import pandas as pd
    from urllib.error import HTTPError

    URL_PREFIX = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    URL_TEMPLATE = URL_PREFIX + "/green_tripdata_" + year_month_duo + ".parquet"

    df = None
    try:
        df = pd.read_parquet(URL_TEMPLATE)
    except HTTPError:
        print("the requested file is not available")
        return None

    return df


@task
def data_validation(df: pd.DataFrame):

    import pandas as pd
    from numpy import datetime64
    import great_expectations as gx
    from pandera.errors import SchemaError
    from pandera import Column, DataFrameSchema, Float64, Index
    from expect_column_values_to_be_non_negative import ExpectColumnValuesToBeNonNegative

    schema = DataFrameSchema(
        {
            "VendorID": Column(Float64, coerce=True),
            "lpep_pickup_datetime": Column(datetime64),
            "lpep_dropoff_datetime": Column(datetime64),
            "store_and_fwd_flag": Column(object, nullable=True),
            "RatecodeID": Column(Float64, nullable=True, coerce=True),
            "PULocationID": Column(Float64, coerce=True),
            "DOLocationID": Column(Float64, coerce=True),
            "passenger_count": Column(Float64, coerce=True, nullable=True),
            "trip_distance": Column(Float64, coerce=True),
            "fare_amount": Column(Float64, coerce=True),
            "extra": Column(Float64, coerce=True),
            "mta_tax": Column(Float64, coerce=True),
            "tip_amount": Column(Float64, coerce=True),
            "tolls_amount": Column(Float64, coerce=True),
            "ehail_fee": Column(Float64, coerce=True, nullable=True),
            "improvement_surcharge": Column(Float64, coerce=True),
            "total_amount": Column(Float64, coerce=True),
            "payment_type": Column(Float64, coerce=True, nullable=True),
            "trip_type": Column(Float64, coerce=True, nullable=True),
            "congestion_surcharge": Column(Float64, coerce=True, nullable=True),
        },
        index=Index(int),
        strict=True,
    )
    
    try:
        schema.validate(df)
    except SchemaError:
        print("schema error")
        return None

    df['lpep_pickup_datetime'] = df['lpep_pickup_datetime'].astype('str')
    df['lpep_dropoff_datetime'] = df['lpep_dropoff_datetime'].astype('str')

    context = gx.data_context.DataContext('./gx/initial_gx')
    taxi_asset = context.get_datasource("green_taxi_validator_checkpoint").get_asset("taxi_df")
    batch_request = taxi_asset.build_batch_request(dataframe=df)
    checkpoint = context.get_checkpoint(name="green_taxi_checkpoint")
    checkpoint_results = checkpoint.run_with_runtime_args(
        batch_request=batch_request,
        expectation_suite_name="green_taxi_expectation_suite"
    )
    print(checkpoint_results.success)
    if checkpoint_results.success != True:
        return None

    return df

@task
def db_injection(table_name: str, df: pd.DataFrame):
    
    # we have a df that we want to inject in our pg database
    # return successful if successful
    import os
    from ingestion_script import ingest_callable
        
    PG_HOST = os.getenv('PG_HOST')
    PG_USER = os.getenv('PG_USER')
    PG_PASSWORD = os.getenv('PG_PASSWORD')
    PG_PORT = os.getenv('PG_PORT')
    PG_DATABASE = os.getenv('PG_DATABASE')    
    
    if df.shape != 0:
        ingest_callable(PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DATABASE, table_name, df)


@task
def load(year_month_duo):
    """
    Prints the name of the largest city in
    the set as determined by the transform.
    """

    print(year_month_duo)


with DAG(
    dag_id="green_taxi",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2023, 2, 1),
    end_date=datetime(2023, 3, 15),
    default_args={"retries": 1, "retry_delay": duration(minutes=1)},
    max_active_runs=1,
    concurrency=5,
) as dag:
    
    year_month_duo_for_scraping = "{{ execution_date.strftime('%Y-%m') }}"
    year_month_duo_for_db = "{{ execution_date.strftime('%Y_%m') }}"
    TABLE_NAME_TEMPLATE = 'green_taxi_' + year_month_duo_for_db
    
    extracted_data = scrape_data_from_source(year_month_duo_for_scraping)
    validated_data = data_validation(extracted_data)
    inject_db = db_injection(TABLE_NAME_TEMPLATE, validated_data)
        
    bronze_transform = BashOperator(
        task_id="bronze_transform",
        bash_command=f"dbt run --vars 'db_name: {TABLE_NAME_TEMPLATE}' --project-dir /opt/airflow/dbt-transform/bronze --profiles-dir /opt/airflow/dbt-transform"
    )
    
    silver_transform = BashOperator(
        task_id="silver_transform",
        bash_command=f'dbt run --project-dir /opt/airflow/dbt-transform/silver --profiles-dir /opt/airflow/dbt-transform'
    )
    
    gold_transform = BashOperator(
        task_id="gold_transform",
        bash_command=f'dbt run --project-dir /opt/airflow/dbt-transform/gold --profiles-dir /opt/airflow/dbt-transform'
    )
    
    chain(
        extracted_data,
        validated_data,
        inject_db,
        bronze_transform, 
        silver_transform,
        gold_transform
    )
import json
import pandas as pd
from airflow import DAG
from numpy import datetime64
from datetime import datetime
import great_expectations as gx
from urllib.error import HTTPError
from airflow.decorators import task
from pandera.errors import SchemaError
from pandera import Column, DataFrameSchema, Float64, Index
# from gx.initial_gx.plugins.expectations.expect_column_values_to_be_non_negative import ExpectColumnValuesToBeNonNegative


@task
def scrape_data_from_source(year_month_duo: str):
    
    URL_PREFIX = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    URL_TEMPLATE = URL_PREFIX + "/green_tripdata_" + year_month_duo + ".parquet"

    df = None
    try:
        df = pd.read_parquet(URL_TEMPLATE)
    except HTTPError:
        print("the requested file is not available")

    return df


# def data_validation(df: pd.DataFrame) -> pd.DataFrame:

#     if df == None:
#         return None

#     schema = DataFrameSchema(
#         {
#             "VendorID": Column(Float64),
#             "lpep_pickup_datetime": Column(datetime64),
#             "lpep_dropoff_datetime": Column(datetime64),
#             "store_and_fwd_flag": Column(object, nullable=True),
#             "RatecodeID": Column(Float64, nullable=True),
#             "PULocationID": Column(Float64),
#             "DOLocationID": Column(Float64),
#             "passenger_count": Column(Float64, nullable=True),
#             "trip_distance": Column(Float64),
#             "fare_amount": Column(Float64),
#             "extra": Column(Float64),
#             "mta_tax": Column(Float64),
#             "tip_amount": Column(Float64),
#             "tolls_amount": Column(Float64),
#             "ehail_fee": Column(Float64, nullable=True),
#             "improvement_surcharge": Column(Float64),
#             "total_amount": Column(Float64),
#             "payment_type": Column(Float64, nullable=True),
#             "trip_type": Column(Float64, nullable=True),
#             "congestion_surcharge": Column(Float64, nullable=True),
#         },
#         index=Index(int),
#         strict=True,
#     )

#     try:
#         schema.validate(df)
#     except SchemaError:
#         print("schema error")
#         return None

#     df['lpep_pickup_datetime'] = df['lpep_pickup_datetime'].astype('str')
#     df['lpep_dropoff_datetime'] = df['lpep_dropoff_datetime'].astype('str')
    
#     context = gx.data_context.DataContext('./gx/initial_gx')
#     my_asset = context.get_datasource("my_taxi_validator_checkpoint").get_asset("taxi_frame")
#     batch_request = my_asset.build_batch_request(dataframe=df)
#     checkpoint = context.get_checkpoint(name="my_checkpoint")
#     checkpoint_results = checkpoint.run_with_runtime_args(
#         batch_request=batch_request,
#         expectation_suite_name="my_expectation_suite"
#     )
#     if checkpoint_results.success != True:
#         return None
    
#     return df


# def db_injection(df: pd.DataFrame):
#     # we have a df that we want to inject in our pg database
#     # return successful if successful
#     pass


# def process_bronze_layer():
#     # process ETL with dbt
#     # get all the data from pg and unify them
#     # use macro in dbt
#     pass


# def process_silver_layer():
#     # we have all of our data
#     # we clean and format the data in this step with dbt
#     pass


# def process_gold_layer():
#     # we divide our data into two separate schemas
#     # AI will have data for machine learning models
#     # BI will have data for BI
#     # in BI, we give some additional computed fields
#     # in AI, we remove some additional unnecessary fields according to observation
#     pass


@task
def extract(info: str):
    """
    Pushes the estimated population (in millions) of
    various cities into XCom for the ETL pipeline.
    Obviously in reality this would be fetching this
    data from some source, not hardcoded values.
    """
    print("before")
    print(info)
    print("after")
    sample_data = {"Tokyo": 3.7, "Jakarta": 3.3, "Delhi": 2.9}
    return json.dumps(sample_data)


@task
def transform(raw_data: str):
    """
    Loads the provided raw data from XCom and pushes
    the name of the largest city in the set to XCom.
    """
    data = json.loads(raw_data)

    largest_city = max(data, key=data.get)
    return largest_city


@task
def load(largest_city):
    """
    Prints the name of the largest city in
    the set as determined by the transform.
    """
    print(largest_city)


with DAG(
    dag_id="green_taxi",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 5, 15)
) as dag:
    year_month_duo = "{{ execution_date.strftime('%Y-%m') }}"
    # df = scrape_data_from_source(year_month_duo)
    # print('done: ' + year_month_duo)
    extracted_data = extract(year_month_duo)
    largest_city = transform(extracted_data)
    load(largest_city)

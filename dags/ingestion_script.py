from datetime import datetime, timezone

import fluss
import pandas as pd
import pyarrow as pa

BOOTSTRAP_SERVERS = "coordinator-server:9123"

SCHEMA = fluss.Schema(
    pa.schema(
        [
            pa.field("vendor_id", pa.int32()),
            pa.field("lpep_pickup_datetime", pa.timestamp("us")),
            pa.field("lpep_dropoff_datetime", pa.timestamp("us")),
            pa.field("rate_code_id", pa.int32()),
            pa.field("pu_location_id", pa.int32()),
            pa.field("do_location_id", pa.int32()),
            pa.field("passenger_count", pa.int32()),
            pa.field("trip_distance", pa.float64()),
            pa.field("fare_amount", pa.float64()),
            pa.field("extra", pa.float64()),
            pa.field("mta_tax", pa.float64()),
            pa.field("tip_amount", pa.float64()),
            pa.field("tolls_amount", pa.float64()),
            pa.field("ehail_fee", pa.float64()),
            pa.field("improvement_surcharge", pa.float64()),
            pa.field("total_amount", pa.float64()),
            pa.field("payment_type", pa.int32()),
            pa.field("trip_type", pa.int32()),
            pa.field("congestion_surcharge", pa.float64()),
            pa.field("cbd_congestion_fee", pa.float64()),
        ]
    )
)


def ingest_callable(database, table_name, df):

    df.passenger_count.fillna(-999, inplace=True)
    df.payment_type.fillna(-999, inplace=True)
    df.trip_type.fillna(-999, inplace=True)
    df.congestion_surcharge.fillna(-999, inplace=True)
    df.RatecodeID.fillna(-999, inplace=True)

    # df.head(n=0).to_sql(name=table_name, con=engine, if_exists="replace")
    # df.to_sql(name=table_name, con=engine, if_exists="append")

    conn = fluss.create(bootstrap_servers=BOOTSTRAP_SERVERS)
    admin = conn.get_admin()

    table_path = create_monthly_table(admin, database, table_name)
    table = conn.get_table(table_path)

    df = df.copy()

    writer = table.new_append().create_writer()
    writer.write_pandas(df)
    writer.flush()

    print(f"Ingested {len(df)} rows into {database}.{table_name}")
    return len(df)


def create_monthly_table(admin, database: str, table_name: str) -> None:

    admin.create_database(database, ignore_if_exists=True)

    table_path = fluss.TablePath(database, table_name)
    descriptor = fluss.TableDescriptor(SCHEMA)

    admin.create_table(table_path, descriptor, ignore_if_exists=True)
    print(f"Ensured table exists: {database}.{table_name}")

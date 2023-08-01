import os

from time import time

import pyarrow.parquet as pq
import pandas as pd
from sqlalchemy import create_engine


def ingest_callable(user, password, host, port, db, table_name, parquet_file, directory, execution_date):
    
    print('variables are: {user}, {password}, {port}'.format(user=user, password=password, port=port))

    engine = create_engine(f'postgresql://{"pgdb_lake"}:{"lake1234"}@{"lake_pgdb"}:{"5432"}/{"lakehouse_db"}')
    engine.connect()

    print('connection established successfully, inserting data...')

    parquet_file = pq.ParquetFile(parquet_file)

    for batch in parquet_file.iter_batches(batch_size=5000):

        t_start = time()    
        batch_df = batch.to_pandas()
        print("batch_df:", batch_df.shape)
        print(batch_df.columns)
        batch_df.lpep_pickup_datetime = pd.to_datetime(batch_df.lpep_pickup_datetime)
        batch_df.lpep_dropoff_datetime = pd.to_datetime(batch_df.lpep_dropoff_datetime)

        batch_df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

        batch_df.to_sql(name=table_name, con=engine, if_exists='append')
        
        t_end = time()
        print('inserted the another chunk, took %.3f second' % (t_end - t_start))
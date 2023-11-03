from sqlalchemy import create_engine


def ingest_callable(user, password, host, port, db, table_name, df):
    
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    engine.connect()

    print('connection established successfully, inserting data...')

    df.store_and_fwd_flag.fillna('-999', inplace=True)
    df.passenger_count.fillna(-999, inplace=True)
    df.payment_type.fillna(-999, inplace=True)
    df.trip_type.fillna(-999, inplace=True)
    df.congestion_surcharge.fillna(-999, inplace=True)
    df.RatecodeID.fillna(-999, inplace=True)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')
    df.to_sql(name=table_name, con=engine, if_exists='append')
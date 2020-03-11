import os

import psycopg2
import pandas as pd
import datetime

from constants import d_COLUMNS


def format_all_results(l_df):
    """
    Concatenates result dataframes and prepare them for sql.

    :params l_df: list of pandas dataframes 
    """
    assert len(l_df) > 0
    assert all([list(df.columns) == list(l_df[0].columns)
                for df in l_df]), 'all df must have same columns'

    df_res_all = pd.concat(l_df, axis=0)

    # add time for partitioning
    df_res_all['datestr'] = str(datetime.date.today())

    # make id as int
    df_res_all['id'] = df_res_all.id.astype(int)

    # drop geotag because you can't store tuple in postgres
    df_res_all.drop(['geotag', 'geotag_rounded'], axis=1, inplace=True)

    return df_res_all


def create_table(table_name, schema, auth):
    cursor, connection = open_connection(auth)
    # add schema
    cursor.execute(schema)
    # commit schema
    connection.commit()


def fetch_tables(table_name, auth):
    cursor, connection = open_connection(auth)
    # execute statement
    cursor.execute("""SELECT table_name FROM information_schema.tables
       WHERE table_schema = 'public'""")
    # fetch data
    l_tables = cursor.fetchall()
    return l_tables


def open_connection(auth):
    connection = psycopg2.connect(
        host=auth['host'],
        port=auth['port'],
        user=auth['user'],
        password=auth['password'],
        database=auth['database']
    )
    cursor = connection.cursor()
    return cursor, connection


def push_data(df_res, auth, table_name='results'):
    """
    Pushes data to Postgres DB in AWS.

    :params df_res pd: pandas dataframe containing data to be pushed 
    :params auth: AWS authentication 
    :params table_name str: table name (table must exist in database)
    """
    assert set(df_res.columns) == set(
        d_COLUMNS[table_name]), 'dataframe columns dont match schema columns'
    assert df_res.shape[0] > 0, 'Dataframe is empty'
    if not os.path.isdir('data/'):
        os.mkdir('data')
    # save in a temporary file
    df_res.to_csv('data/temp.csv', index=False)
    # get cursor and connection
    cursor, connection = open_connection(auth)
    # save results
    with open('data/temp.csv', 'r') as row:
        next(row)  # skip the header
        cursor.copy_from(row, table_name, sep=',')
    # commit connection
    connection.commit()

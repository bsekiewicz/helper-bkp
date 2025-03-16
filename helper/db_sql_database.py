import logging
from typing import Union, Dict, List, Tuple

import pandas as pd
from psycopg2 import connect, sql
from psycopg2.extras import execute_batch, execute_values

import helper.utils


class PostgreSQLDatabase:
    """
    PostgreSQL Database Utilities Class

    This class provides utility methods for connecting to a PostgreSQL database,
    executing SQL queries, and performing batch operations like insert, update, and delete.

    Attributes:
        connection (psycopg2.connection): The database connection object.
        cursor (psycopg2.cursor): The cursor object for executing SQL queries.
        connection_params (dict): Parameters used for the database connection.
        dbname (str): The name of the database to connect to.

    Methods:
        connect(cs: Union[str, dict], verbose: int = 1):
            Establishes a connection to the PostgreSQL database.

        reconnect(verbose: int = 1):
            Re-establishes a connection to the PostgreSQL database if it's closed.

        close(verbose: int = 1):
            Closes the connection to the PostgreSQL database.

        execute_and_fetch(sql_query: str, use_pandas: bool = False):
            Executes a SQL query and fetches all rows.

        insert_batch(data: Union[Dict, List, pd.DataFrame], table_name: str, ...):
            Inserts data into a table in batch mode.

        update_batch(data: List[dict], columns_set: List[Tuple[str, str]], ...):
            Updates data in a table in batch mode.

        delete_batch(data: List[dict], table_name: str, ...):
            Deletes data from a table in batch mode.
    """

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connection_params = None
        self.dbname = None

    @staticmethod
    def _log_warning(message: str, verbose: int, level: int = 1):
        if verbose >= level:
            logging.warning(message)

    def _connect_db(self, verbose: int = 0):
        try:
            self.connection = connect(**self.connection_params)
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
        except Exception as error:
            raise error

        self._log_warning(f'Connection to {self.dbname} database established', verbose)

    def _reconnect_if_closed(self):
        if self.connection and self.connection.closed != 0:
            self.reconnect()

    def connect(self, cs: Union[str, Dict], verbose: int = 0):
        """
        Create connection to SQL database
        """
        self.connection_params = helper.utils.read_dict(cs)
        if self.connection_params is None:
            raise TypeError(f"Could not read connection params: {type(cs)}")

        self.dbname = self.connection_params.get('dbname', '')

        if self.connection:
            self.connection.close()

        self._connect_db(verbose)

    def reconnect(self, verbose: int = 0):
        """
        Reconnect to the database
        """
        if self.connection_params:
            if self.connection:
                self.connection.close()
            self._connect_db(verbose)

    def close(self, verbose: int = 0):
        """
        Close the database connection
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

        self._log_warning(f'Connection to {self.dbname} database closed', verbose)

    def execute_and_fetch(self, sql_query: str, params: tuple = None, use_pandas: bool = False):
        """
        Execute SQL query and fetch all results
        """
        if params:
            self.cursor.execute(sql_query, params)
        else:
            self.cursor.execute(sql_query)

        data = self.cursor.fetchall()

        if use_pandas:
            columns = [x[0] for x in self.cursor.description]
            return pd.DataFrame(data, columns=columns)

        return data

    def insert_batch(self,
                     data: Union[Dict, List, pd.DataFrame],
                     table_name: str,
                     table_schema: str = 'public',
                     page_size: int = 10000,
                     on_conflict: List = None,
                     on_conflict_do: int = 0,
                     on_conflict_do_list: List = None,
                     verbose: int = 1) -> bool:
        """
        Sequential inserting to defined table
        """
        self._reconnect_if_closed()

        # Determine the type of data and extract fields and values
        if isinstance(data, dict):
            if not data:
                return True
            fields = list(data.keys())
            values = [data]
        elif isinstance(data, list):
            if not data:
                return True
            fields = list(data[0].keys())
            values = data
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                return True
            fields = list(data.columns)
            values = data.where(pd.notnull(data), None).to_dict(orient='records')
        else:
            self._log_warning('Wrong data type!', verbose)
            return False

        # Construct the SQL query string
        if not isinstance(on_conflict, list):
            sql_string = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                sql.Identifier(table_schema),
                sql.Identifier(table_name),
                sql.SQL(",").join(map(sql.Identifier, fields)),
                sql.SQL(",").join(map(sql.Placeholder, fields))
            )
        else:
            on_conflict_sql = sql.SQL("({})").format(sql.SQL(", ").join(map(sql.Identifier, on_conflict)))
            if on_conflict_do == 0:
                sql_string = sql.SQL("INSERT INTO {}.{} ({}) "
                                     "VALUES ({}) "
                                     "ON CONFLICT {} DO NOTHING").format(
                    sql.Identifier(table_schema),
                    sql.Identifier(table_name),
                    sql.SQL(",").join(map(sql.Identifier, fields)),
                    sql.SQL(",").join(map(sql.Placeholder, fields)),
                    on_conflict_sql
                )
            elif on_conflict_do == 1 and isinstance(on_conflict_do_list, list):
                on_conflict_do_update_sql = sql.SQL(", ").join([
                    sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(x.split(':')[0]),
                                                       sql.Identifier(x.split(':')[0]))
                    for x in on_conflict_do_list
                ])
                sql_string = sql.SQL("INSERT INTO {}.{} ({}) "
                                     "VALUES ({}) "
                                     "ON CONFLICT {} DO UPDATE SET {}").format(
                    sql.Identifier(table_schema),
                    sql.Identifier(table_name),
                    sql.SQL(",").join(map(sql.Identifier, fields)),
                    sql.SQL(",").join(map(sql.Placeholder, fields)),
                    on_conflict_sql,
                    on_conflict_do_update_sql
                )
            else:
                self._log_warning('Wrong on_conflict_do value!', verbose)
                return False

        # Execute the SQL query
        try:
            execute_batch(self.cursor, sql=sql_string, argslist=values, page_size=page_size)
            return True
        except Exception as first_error:
            self._log_warning(f"First attempt failed: {type(first_error).__name__}: {str(first_error)}", verbose)

            # Retry after reconnecting
            try:
                self._reconnect_if_closed()
                execute_batch(self.cursor, sql=sql_string, argslist=values, page_size=page_size)
                return True
            except Exception as second_error:
                self._log_warning(f"Retry attempt failed: {type(second_error).__name__}: {str(second_error)}", verbose)
                self._log_warning(f"Problematic data: {str(data)}", verbose)
                return False

    def update_batch(self,
                     data: List[dict],
                     columns_set: List[Tuple[str, str]],
                     columns_where: List[str],
                     table_name: str,
                     table_schema: str = 'public',
                     page_size: int = 10000,
                     verbose: int = 1) -> bool:
        """
        Batch update operation
        """
        self._reconnect_if_closed()

        if not columns_set:
            self._log_warning('No columns_set', verbose)
            return False

        if not columns_where:
            self._log_warning('No columns_where', verbose)
            return False

        if not isinstance(data, list) or not data:
            self._log_warning('Wrong or empty data type!', verbose)
            return False

        values = [tuple(x[y] for y in data[0].keys()) for x in data]
        fields = list(data[0].keys())

        sql_fields = ', '.join(fields)
        sql_set = ', '.join([f"{x[0]} = data.{x[1]}" for x in columns_set])
        sql_where = ' AND '.join([f"{table_name}.{x} = data.{x}" for x in columns_where])

        try:
            execute_values(
                self.cursor,
                sql=f'''
                    UPDATE {table_schema}.{table_name}
                    SET {sql_set}
                    FROM (VALUES %s) AS data ({sql_fields})
                    WHERE {sql_where}
                ''',
                argslist=values,
                page_size=page_size
            )
            return True
        except Exception as e:
            self._log_warning(str(e), verbose)
            self._log_warning(str(data), verbose)
            return False

    def delete_batch(self,
                     data: List[dict],
                     table_name: str,
                     table_schema: str = 'public',
                     page_size: int = 1000,
                     verbose: int = 1) -> bool:
        """
        Sequential removal from defined table
        """
        self._reconnect_if_closed()

        if not isinstance(data, list) or not data:
            self._log_warning('Wrong or empty data type!', verbose)
            return False

        fields = list(data[0].keys())
        if len(fields) != 1:
            self._log_warning('Only one field is valid!', verbose)
            return False

        sql_string = sql.SQL("DELETE FROM {}.{} WHERE {} = {}").format(
            sql.Identifier(table_schema),
            sql.Identifier(table_name),
            sql.Identifier(fields[0]),
            sql.Placeholder(fields[0])
        )

        try:
            execute_batch(self.cursor, sql=sql_string, argslist=data, page_size=page_size)
            return True
        except Exception as e:
            self._log_warning(str(e), verbose)
            self._log_warning(str(data), verbose)
            return False


def postgresql_database_connect(cs: Union[str, Dict[str, str]]) -> PostgreSQLDatabase:
    """
    Connects to an object PostgreSQL service and returns an PostgreSQLDatabase instance.
    """
    db = PostgreSQLDatabase()
    db.connect(cs)
    return db


def pd_read_sql(sql_query: str, cs: Union[str, Dict[str, str]]) -> pd.DataFrame:
    """
    Quickly fetch data into a Pandas DataFrame.
    @param sql_query: The SQL query to execute.
    @param cs: The connection string or dictionary containing connection parameters.
    @return: The fetched data as a Pandas DataFrame.
    """
    db = postgresql_database_connect(cs)
    df = db.execute_and_fetch(sql_query=sql_query, use_pandas=True)
    db.close()
    return df

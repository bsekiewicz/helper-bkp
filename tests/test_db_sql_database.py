import unittest
from unittest.mock import patch, Mock

import pandas as pd

from helper.db_sql_database import PostgreSQLDatabase, postgresql_database_connect, pd_read_sql


class TestPostgreSQLDatabase(unittest.TestCase):

    @patch('helper.db_sql_database.connect')
    def test_connect(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = PostgreSQLDatabase()
        db.connect({"dbname": "test_db"})

        mock_connect.assert_called_once()
        self.assertEqual(db.connection, mock_conn)
        self.assertEqual(db.cursor, mock_cursor)

    @patch('helper.db_sql_database.connect')
    def test_execute_and_fetch(self, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("row1",), ("row2",)]

        db = PostgreSQLDatabase()
        db.connect({"dbname": "test_db"})
        result = db.execute_and_fetch("SELECT * FROM table")

        mock_cursor.execute.assert_called_with("SELECT * FROM table")
        mock_cursor.fetchall.assert_called_once()
        self.assertEqual(result, [("row1",), ("row2",)])

    @patch('helper.db_sql_database.connect')
    @patch('helper.db_sql_database.execute_batch')
    def test_insert_batch(self, mock_execute_batch, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = PostgreSQLDatabase()
        db.connect({"dbname": "test_db"})

        data = [{"col1": "value1", "col2": "value2"}]
        db.insert_batch(data, "test_table")

        mock_execute_batch.assert_called_once()

    @patch('helper.db_sql_database.connect')
    @patch('helper.db_sql_database.execute_values')
    def test_update_batch(self, mock_execute_values, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = PostgreSQLDatabase()
        db.connect({"dbname": "test_db"})

        data = [{"col1": "value1", "col2": "value2"}]
        columns_set = [("col1", "col1")]
        columns_where = ["col2"]
        db.update_batch(data, columns_set, columns_where, "test_table")

        mock_execute_values.assert_called_once()

    @patch('helper.db_sql_database.connect')
    @patch('helper.db_sql_database.execute_batch')
    def test_delete_batch(self, mock_execute_batch, mock_connect):
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db = PostgreSQLDatabase()
        db.connect({"dbname": "test_db"})

        data = [{"col1": "value1"}]
        db.delete_batch(data, "test_table")

        mock_execute_batch.assert_called_once()


class TestPostgreSQLDatabaseConnect(unittest.TestCase):

    @patch('helper.db_sql_database.PostgreSQLDatabase.connect')
    def test_postgresql_database_connect(self, mock_connect):
        cs = {"dbname": "test_db"}
        db = postgresql_database_connect(cs)

        mock_connect.assert_called_once_with(cs)
        self.assertIsInstance(db, PostgreSQLDatabase)

    @patch('helper.db_sql_database.postgresql_database_connect')
    def test_pd_read_sql_without_context_manager(self, mock_postgresql_database_connect):
        # Create a mock database object
        mock_db = Mock()

        # Configure the mock to return our mock database when postgresql_database_connect is called
        mock_postgresql_database_connect.return_value = mock_db

        # Define what should be returned when execute_and_fetch is called on our mock database
        expected_dataframe = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        mock_db.execute_and_fetch.return_value = expected_dataframe

        # Call the function to be tested
        cs = {"dbname": "test_db"}
        sql_query = "SELECT * FROM table"
        df = pd_read_sql(sql_query, cs)

        # Verify that the correct methods were called with the correct arguments
        mock_postgresql_database_connect.assert_called_once_with(cs)
        mock_db.execute_and_fetch.assert_called_once_with(sql_query=sql_query, use_pandas=True)

        # Verify that the function returned the expected dataframe
        pd.testing.assert_frame_equal(df, expected_dataframe)


if __name__ == '__main__':
    unittest.main()

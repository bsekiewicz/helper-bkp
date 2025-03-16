import unittest
from unittest.mock import patch, Mock

from helper.db_object_storage import fix_metadata_value, ObjectStorage, object_storage_connect


class TestFixMetadataValue(unittest.TestCase):

    def test_fix_metadata_value_with_string(self):
        self.assertEqual(fix_metadata_value("test"), "test")

    def test_fix_metadata_value_with_list(self):
        self.assertEqual(fix_metadata_value(["test", "value"]), "test, value")

    def test_fix_metadata_value_with_dict(self):
        self.assertIsNone(fix_metadata_value({"key": "value"}))

    def test_fix_metadata_value_with_none(self):
        self.assertIsNone(fix_metadata_value(None))

    def test_fix_metadata_value_with_special_characters(self):
        self.assertEqual(fix_metadata_value("tęst vąlue"), "test value")


class TestObjectStorage(unittest.TestCase):

    @patch('helper.db_object_storage.Minio')
    def test_connect(self, mock_minio):
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance

        storage = ObjectStorage()
        storage.connect({"endpoint": "localhost", "access_key": "key", "secret_key": "secret"})

        mock_minio.assert_called_with(endpoint="localhost", access_key="key", secret_key="secret")
        self.assertEqual(storage.connection, mock_minio_instance)

    @patch('helper.db_object_storage.Minio')
    def test_put_object(self, mock_minio):
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance

        storage = ObjectStorage()
        storage.connection = mock_minio_instance

        result = storage.put_object("bucket", "object", b"data")

        self.assertTrue(result)
        mock_minio_instance.put_object.assert_called()

    @patch('helper.db_object_storage.Minio')
    def test_fput_object(self, mock_minio):
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance

        storage = ObjectStorage()
        storage.connection = mock_minio_instance

        result = storage.fput_object("bucket", "object", "file_path")

        self.assertTrue(result)
        mock_minio_instance.fput_object.assert_called()

    @patch('helper.db_object_storage.Minio')
    def test_get_object(self, mock_minio):
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance

        storage = ObjectStorage()
        storage.connection = mock_minio_instance

        storage.get_object("bucket", "object")

        mock_minio_instance.get_object.assert_called_with(
            bucket_name="bucket", object_name="object",
            offset=0, length=0, request_headers=None,
            ssec=None, version_id=None, extra_query_params=None
        )

    @patch('helper.db_object_storage.Minio')
    def test_list_objects_names(self, mock_minio):
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance

        mock_object = Mock()
        mock_object.object_name = "object_name"
        mock_minio_instance.list_objects.return_value = [mock_object]

        storage = ObjectStorage()
        storage.connection = mock_minio_instance

        result = storage.list_objects_names("bucket")

        self.assertEqual(result, ["object_name"])

    @patch('helper.db_object_storage.Minio')
    def test_remove_objects(self, mock_minio):
        mock_minio_instance = Mock()
        mock_minio.return_value = mock_minio_instance

        mock_object = Mock()
        mock_object.object_name = "object_name"
        mock_minio_instance.list_objects.return_value = [mock_object]

        storage = ObjectStorage()
        storage.connection = mock_minio_instance

        storage.remove_objects("bucket")

        mock_minio_instance.remove_object.assert_called_with("bucket", "object_name")


class TestObjectStorageConnect(unittest.TestCase):

    @patch('helper.db_object_storage.ObjectStorage')
    def test_object_storage_connect(self, mock_object_storage):
        mock_storage_instance = Mock()
        mock_object_storage.return_value = mock_storage_instance

        result = object_storage_connect({"endpoint": "localhost", "access_key": "key", "secret_key": "secret"})

        self.assertEqual(result, mock_storage_instance)
        mock_storage_instance.connect.assert_called_with(
            {"endpoint": "localhost", "access_key": "key", "secret_key": "secret"})


if __name__ == "__main__":
    unittest.main()

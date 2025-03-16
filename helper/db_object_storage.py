import logging
import re
from io import BytesIO
from typing import Union, List, Dict, Optional

from minio import Minio

import helper.data_format
import helper.utils


def fix_metadata_value(text: Union[str, List[str], Dict, None]) -> Optional[str]:
    if text is None:
        return None

    if isinstance(text, list):
        text = ', '.join(text)

    if isinstance(text, dict):
        return None

    text_fixed = helper.data_format.remove_diacritics(str(text))
    text_fixed = re.sub(r'[\s\r\n\t ]+', ' ', text_fixed)
    text_fixed = ''.join(x for x in text_fixed if ord(x) <= 127).strip()
    return text_fixed[:1024]  # max 2KB


class ObjectStorage:
    """
    Object Storage based S3
    """

    def __init__(self):
        self.connection = None

    @staticmethod
    def _log_warning(message: str, verbose: int, level: int = 1):
        if verbose >= level:
            logging.warning(message)

    def connect(self, cs: Union[str, Dict], verbose: int = 0) -> None:
        connection_params = helper.utils.read_dict(cs)
        if connection_params is None:
            self._log_warning(f"Invalid connection params type: {type(connection_params)}", verbose)
            raise TypeError(f"Invalid connection params type: {type(connection_params)}")

        try:
            self.connection = Minio(**connection_params)
        except Exception as e:
            self._log_warning(str(e), verbose)
            raise e
        else:
            self._log_warning('Connection to object storage established', verbose)

    def put_object(self, bucket_name: str, object_name: str, data: Union[BytesIO, bytes],
                   content_type: str = "application/octet-stream", metadata: Optional[Dict] = None,
                   sse=None, progress=None, part_size: int = 0, num_parallel_uploads: int = 3,
                   tags=None, retention=None, legal_hold: bool = False, verbose: int = 1) -> bool:
        """
        Uploads an object to the specified bucket.
        """
        try:
            with BytesIO(data) if not isinstance(data, BytesIO) else data as f:
                f.seek(0)
                if metadata:
                    metadata = {k: fix_metadata_value(v) for k, v in metadata.items()}
                self.connection.put_object(bucket_name=bucket_name, object_name=object_name, data=f,
                                           length=f.getbuffer().nbytes, content_type=content_type,
                                           metadata=metadata, sse=sse, progress=progress,
                                           part_size=part_size, num_parallel_uploads=num_parallel_uploads,
                                           tags=tags, retention=retention, legal_hold=legal_hold)
            return True
        except Exception as e:
            self._log_warning(str(e), verbose)
            return False

    def fput_object(self, bucket_name: str, object_name: str, file_path: str,
                    content_type: str = "application/octet-stream", metadata: Optional[Dict] = None,
                    sse=None, progress=None, part_size: int = 0, num_parallel_uploads: int = 3,
                    tags=None, retention=None, legal_hold: bool = False, verbose: int = 1) -> bool:
        """
        Uploads a file to the specified bucket.
        """
        try:
            if metadata:
                metadata = {k: fix_metadata_value(v) for k, v in metadata.items()}
            self.connection.fput_object(bucket_name=bucket_name, object_name=object_name, file_path=file_path,
                                        content_type=content_type, metadata=metadata, sse=sse, progress=progress,
                                        part_size=part_size, num_parallel_uploads=num_parallel_uploads,
                                        tags=tags, retention=retention, legal_hold=legal_hold)
            return True
        except Exception as e:
            self._log_warning(str(e), verbose)
            return False

    def get_object(self, bucket_name: str, object_name: str, offset: int = 0, length: int = 0,
                   request_headers: Optional[Dict] = None, ssec=None, version_id: Optional[str] = None,
                   extra_query_params: Optional[Dict] = None, verbose: int = 1):
        """
        Retrieves an object from the specified bucket.
        """
        try:
            return self.connection.get_object(bucket_name=bucket_name, object_name=object_name,
                                              offset=offset, length=length, request_headers=request_headers,
                                              ssec=ssec, version_id=version_id, extra_query_params=extra_query_params)
        except Exception as e:
            self._log_warning(str(e), verbose)
            return None

    def list_objects_names(self, bucket_name: str, prefix: Optional[str] = None,
                           recursive: bool = True, object_name_filter: Optional[str] = None,
                           verbose: int = 1) -> List[str]:
        """
        Lists object names in the specified bucket.
        """
        try:
            if object_name_filter is None:
                object_name_filter = ''

            objects = self.connection.list_objects(bucket_name, prefix, recursive)
            objects_names = [x.object_name for x in objects]
            objects_names = [x for x in objects_names if re.search(object_name_filter, x)]
            return objects_names
        except Exception as e:
            self._log_warning(str(e), verbose)
            return []

    def remove_objects(self, bucket_name: str, prefix: Optional[str] = None, verbose: int = 1) -> None:
        """
        Removes objects with the specified prefix from the bucket.
        """
        try:
            removed_objects_count = len(list(map(
                lambda x: self.connection.remove_object(bucket_name, x.object_name),
                self.connection.list_objects(bucket_name, prefix, recursive=True))))
            logging.info(f"Removed {removed_objects_count} objects from bucket {bucket_name} with prefix {prefix}.")
        except Exception as e:
            self._log_warning(str(e), verbose)


def object_storage_connect(cs: Union[str, Dict]) -> ObjectStorage:
    """
    Connects to an object storage service and returns an ObjectStorage instance.
    """
    db = ObjectStorage()
    db.connect(cs)
    return db

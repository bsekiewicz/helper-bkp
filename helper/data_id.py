import copy
import re
import uuid
from hashlib import sha256

import helper.data_format
import helper.utils


def convert_text_to_key(input_str: str or None) -> str or None:
    """
    The function converts text into an "identifier/key/variable name" format.
    * removes diacritical marks
    * converts to lowercase and removes unnecessary spaces
    * removes non-alphanumeric characters
    * replaces spaces with underscores

    @param input_str: input string
    @return: text in the "identifier/key/variable name" format.
    """
    if helper.utils.is_empty(input_str):
        return None

    output_str = helper.data_format.remove_diacritics(input_str)
    output_str = re.sub(r'[^a-z0-9\s]+', ' ', output_str.lower().strip())
    output_str = re.sub(r'\s+', '_', output_str.strip())
    return output_str


def convert_text_to_uuid(input_str: str) -> str:
    """
    The function converts text to a UUID.
    The selected method prefers short texts.
    A UUID is a string consisting of 36 alphanumeric characters.
    E.g. 00030153-38a3-9fa6-0000-100b8000aa0c.

    @param input_str: input text
    @return: UUID string
    """
    return str(uuid.uuid3(uuid.NAMESPACE_X500, input_str))


def convert_data_to_id(data: bytes or str or None, method: str = 'uuid') -> str or None:
    """
    The function converts data to a SHA256 (files) or UUID (data).
    UUID conversion prefers short data,
    so the function first converts the data to sha256 and then to UUID.

    @param data: input data
    @param method: 'uuid' or 'sha256'
    @return: UUID string
    """
    data_std = helper.data_format.data_standardization(copy.deepcopy(data))

    if isinstance(data_std, bytes):
        data_std_b = data_std
    elif isinstance(data_std, str):
        data_std_b = data_std.encode('utf-8')
    else:
        return None

    hash_string = sha256()
    hash_string.update(data_std_b)

    if method == 'uuid':
        return convert_text_to_uuid(f'sha256={hash_string.hexdigest()}')
    elif method == 'sha256':
        return hash_string.hexdigest()

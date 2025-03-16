import functools
import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Tuple, Union, Optional

import unicodedata
from dateparser import parse as parse_date_lib
from price_parser import parse_price as parse_price_lib

import helper.constants
import helper.utils


def data_standardization(data: any) -> any:
    """
    Standardizes data structures and converts them into a JSON-formatted string.

    This function takes various data types (preferably dict, list, or tuple) and standardizes them
    by sorting and converting to a JSON string. For non-iterable types, it returns the input unchanged.

    Parameters:
    -----------
    data : any
        The input data to be standardized. Preferably a dict, list, or tuple.

    Returns:
    --------
    any
        If the input is a dict, list, or tuple: 
            A JSON-formatted string representation of the standardized and sorted data.
        Otherwise: 
            The input data unchanged.
    """

    def compare_items(item1, item2):
        """
        Compares two items and returns an integer indicating their relative order.
    
        This function is used for sorting items based on their string representation and type.
        It defines a custom ordering for different Python types and compares items accordingly.
    
        Parameters:
        -----------
        item1 : any
            The first item to compare.
        item2 : any
            The second item to compare.
    
        Returns:
        --------
        int
            -1 if item1 should come before item2,
            1 if item2 should come before item1,
            0 if the items are considered equal in terms of ordering.
        """
        type_order = defaultdict(lambda: 0)
        type_order['int'] = 1
        type_order['str'] = 2
        type_order['float'] = 3
        type_order['datetime'] = 4
        type_order['NoneType'] = 5
        type_order['bool'] = 6
        type_order['list'] = 7
        type_order['dict'] = 8
    
        item1_key = str(item1)
        item1_type = type(item1).__name__
        item2_key = str(item2)
        item2_type = type(item2).__name__
        if item1_key != item2_key:
            return 1 if item1_key > item2_key else -1
        elif item1_type != item2_type:
            return 1 if type_order[item1_type] > type_order[item2_type] else -1
        else:
            return 0

    def sort_dict(d):
        """
        Recursively sorts any elements inside a dictionary.
        """
        for k in d.keys():
            if isinstance(d[k], list) or isinstance(d[k], tuple):
                d[k] = sort_list(d[k])
            elif isinstance(d[k], dict):
                sort_dict(d[k])

    def sort_list(d):
        """
        Recursively sorts any elements inside a list.
        """
        d = sorted(list(d), key=functools.cmp_to_key(compare_items))
        for i in range(len(d)):
            if isinstance(d[i], list) or isinstance(d[i], tuple):
                d[i] = sort_list(d[i])
            elif isinstance(d[i], dict):
                sort_dict(d[i])
        return tuple(d)

    if isinstance(data, (list, tuple)):
        """
        If the input data is a list or tuple, sort it using the `sort_list` function.
        """
        data = sort_list(data)
        return json.dumps(data, sort_keys=True, default=str, ensure_ascii=True)
    elif isinstance(data, dict):
        """
        If the input data is a dictionary, sort it using the `sort_dict` function.
        """
        sort_dict(data)
        return json.dumps(data, sort_keys=True, default=str, ensure_ascii=True)
    else:
        """
        If the input data is not a list, tuple, or dictionary, return it unchanged.
        """
        return data


def remove_diacritics(input_str: str or None) -> str or None:
    """
    The function removes diacritical marks from the input text.

    Parameters:
        input_str (str or None): input text

    Returns:
        str or None: text without diacritical marks
    """
    if input_str is None:
        return None

    nfkd_form = unicodedata.normalize("NFKD", input_str.replace('ł', 'l').replace('Ł', 'L'))
    return u''.join([c for c in nfkd_form if not unicodedata.combining(c)])


def camel_to_snake(name: str) -> str:
    """
    Converts a string to snake case.

    Parameters:
        name (str): camel case string

    Returns:
        str: snake case string
    """
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s).lower()


def parse_date(input_str: Union[str, None],
               date_format: str = '%Y-%m-%d',
               to_string: bool = True, date_ordered: str = 'YMD') -> Union[datetime, str, None]:
    """
    Converts a string to a datetime object (or string, depending on to_string).

    Parameters:
        input_str (str): The input string to parse.
        date_format (str): The format of the output string. Defaults to '%Y-%m-%d'.
        to_string (bool): Whether to return the datetime object as a string. Defaults to True.
        date_ordered (str): The order of the date components. Can be 'YMD', 'MDY', or 'DMY'. Defaults to 'YMD'.

    Returns:
        Union[datetime.datetime, str]: The datetime object or string, depending on the value of to_string.
        If an error occurs, returns None.

    """
    if input_str is None:
        return None

    date_parsed = parse_date_lib(input_str, settings={"DATE_ORDER": date_ordered})
    if to_string is True:
        if date_parsed is not None:
            return date_parsed.strftime(date_format)
        else:
            return None
    else:
        return date_parsed


def parse_price(input_str: Union[str, None],
                to_string: bool = True,
                currency_fixed: str = None,
                iso3_currency: bool = True,
                cou: str = None) -> Tuple[Union[str, float, None], Union[str, None]]:
    """
    Converts a string to a price object.

    Parameters:
    input_str (str): The input string to parse.
    to_string (bool): Whether to return the price amount as a string. Default is True.
    currency_fixed (str): If provided, this currency will be returned instead of the parsed currency.
    iso3_currency (bool): Whether to map the currency to its ISO3 format. Default is True.
    cou (str): Country code (iso2).

    Returns:
    A tuple containing the price amount and currency.
    """
    if input_str is None:
        return None, None

    input_str = str(input_str)
    input_str_fixed = input_str.replace("'", "")
    price_parsed = parse_price_lib(input_str_fixed)

    price_amount = price_parsed.amount
    if to_string and price_amount is not None:
        price_amount = f'{price_amount:.2f}'

    if currency_fixed:
        price_currency = currency_fixed
    else:
        price_currency = price_parsed.currency
        if iso3_currency:
            if cou:
                if price_currency in ['kr', 'kr.', 'L']:
                    price_currency += ' ' + cou

            # find iso3 based symbol
            price_currency = helper.constants.MAPPING_CURRENCIES_SYMBOLS.get(price_currency, price_currency)

            # bugfix
            if 'Íkr' in input_str:
                price_currency = 'ISK'
            if 'ден' in input_str:
                price_currency = 'MKD'

    return price_amount, price_currency


def convert_to_gtin(code: Union[str, None], gtin_length: int = 14) -> Optional[str]:
    """
    Convert a code to a GTIN.

    Args:
        code (str): The code to convert.
        gtin_length (int, optional): The length of the GTIN. Defaults to 14.

    Returns:
        Optional[str]: The GTIN, or None if the code is not valid.
    """
    if helper.utils.is_empty(code) or not code.isdigit() or len(code) > 14 or len(code) < 8:
        return None

    code = code[-gtin_length:]
    code = code.zfill(gtin_length)

    checksum = sum(int(digit) * (3 if i % 2 == 0 else 1) for i, digit in enumerate(reversed(code[:-1])))
    checksum = (10 - (checksum % 10)) % 10

    if int(code[-1]) != checksum:
        return None

    return code

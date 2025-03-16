import json
import os
import re
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
from operator import itemgetter

import pandas as pd
from igraph import Graph

import helper.data_format


def to_decimal(value, quantize='0.01'):
    """
    # Konwersja kwot na decimal (2 msc po przecinku, bez zabawy w zaokraglanie)
    :param value:
    :param quantize:
    :return:
    """
    try:
        return Decimal(value).quantize(Decimal(quantize), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, ArithmeticError):
        return None


def is_integer(value: any) -> bool:
    """
    Extension of the isdigit property.
    Checks if the value is an integer (including negative integers).
    @param val: value to be checked
    @return: True if the value is an integer (including negative integers), False otherwise.
    """
    return isinstance(value, int) or (isinstance(value, str) and value.lstrip('-').isdigit())


def is_empty(value: any, fast_check: bool = True, list_of_empty_values: list or None = None) -> bool:
    """
    Check if a value can be treated as a missing data.

    @param value: the value to check
    @param fast_check: skip text cleaning
    @param list_of_empty_values: a list of synonyms for "missing data"
    @return: True/False
    """
    if list_of_empty_values is None:
        list_of_empty_values = [
            '', 'brak', 'brakdanych', 'brakwartosci', 'bd',
            'none', 'null', 'nan', 'nat',
            'empty', 'missing', 'na', 'novalue', 'notapplicable']

    value2 = str(value).lower()
    if not fast_check:
        value2 = helper.data_format.remove_diacritics(value2)
    value2 = re.sub(r'[^a-z\d]+', '', value2)

    return value2 in list_of_empty_values


def list_flatten(list_to_flatten: list) -> list:
    """
    Converts a list of lists to a flat list.
    @param list_to_flatten: the list of lists
    @return: the flattened list
    """
    return [item for s in list_to_flatten for item in s]


def join_selected_value_in_list_of_dicts(list_of_dicts: list, key: str, sep: str) -> str:
    """
    Joins values for a selected key from a list of dictionaries using a separator.
    @param list_of_dicts: list of dictionaries
    @param key: key to join values for
    @param sep: separator to use
    @return: joined string of values for the selected key
    """
    return sep.join([str(x.get(key, '')) for x in list_of_dicts if not is_empty(x.get(key, ''))])


def remove_duplicates_by_key(dict_list, key='id_internal'):
    """
    Removes duplicates from a list of dictionaries by a given key.
    @param dict_list: list of dictionaries
    @param key: key to use for the removal
    @return: list of dictionaries without duplicates
    """
    seen_ids = set()
    return [seen_ids.add(d[key]) or d for d in dict_list if d[key] not in seen_ids]


def drop_duplicates_from_list(elements: list) -> list:
    elements_temp = []
    for i in elements:
        if i not in elements_temp:
            elements_temp.append(i)
    return elements_temp


def read_dict(val: str or dict) -> dict or None:
    """
    The function reads a dictionary from a file or converts text to a dictionary.
    @param val: either a file path or a string containing dictionary data
    @return: a dictionary
    """
    if isinstance(val, dict):
        return val
    elif isinstance(val, str):
        if os.path.exists(val):
            try:
                with open(val, 'r') as f:
                    val = f.read()
            except IOError:
                return None

        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return None
    else:
        return None


def find_edges_connections(df: pd.DataFrame) -> pd.DataFrame:
    # Filter out rows where both elements are None
    df = df.dropna(how='all')

    # Convert rows to lists, filtering out None values
    edges_sets = [sorted([x for x in row if not is_empty(x)]) for _, row in df.iterrows()]

    # Identify singleton groups
    edges_s = [e for e in edges_sets if len(e) == 1]
    edges_s = sorted(set([i for s in edges_s for i in s]))

    # Create pairs of connections
    edges_c = [list(combinations(e, 2)) for e in edges_sets if len(e) > 1]
    edges_c = [i for s in edges_c for i in s]

    # Create a list of vertices
    vertices = sorted(list(set([v for e in edges_c for v in e])))
    vertices = pd.DataFrame({'name': vertices})

    # Create DataFrame of edges
    edges = pd.DataFrame(edges_c, columns=['a', 'b']).drop_duplicates()

    if edges.empty:
        return pd.DataFrame({'group_id': range(len(edges_s)), 'value': edges_s})

    # Remove None values and duplicates from vertices
    vertices = vertices[vertices['name'].notna()]
    vertices.drop_duplicates(subset=['name'], inplace=True)

    # Remove rows from edges where either vertex is None
    edges = edges.dropna(subset=['a', 'b'])

    # Create graph
    g = Graph.DataFrame(edges, directed=False, use_vids=False, vertices=vertices)
    c = Graph.components(g, mode='strong')

    # Create DataFrame of connections
    connections = [pd.DataFrame([{'group_id': int(i), 'value': x} for x
                                 in itemgetter(*c[i])(g.vs['name'])]) for i in range(len(c))]
    connections = pd.concat(connections)

    # Remove singletons that are already part of a group
    edges_s = list(set(edges_s) - set(connections['value']))

    # The remaining singletons form their own groups
    edges_s = pd.DataFrame({'group_id': range(connections['group_id'].max() + 1,
                                              connections['group_id'].max() + 1 + len(edges_s)),
                            'value': edges_s})

    # Combine the tables
    connections = pd.concat([connections, edges_s]).reset_index(drop=True)

    return connections

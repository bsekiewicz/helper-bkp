import json
import os
import unittest

import pandas as pd

from helper.utils import is_integer, is_empty, list_flatten, join_selected_value_in_list_of_dicts, read_dict, \
    find_edges_connections


class TestIsInteger(unittest.TestCase):

    def test_positive_integers(self):
        self.assertTrue(is_integer(1))
        self.assertTrue(is_integer("1"))

    def test_negative_integers(self):
        self.assertTrue(is_integer(-1))
        self.assertTrue(is_integer("-1"))

    def test_non_integers(self):
        self.assertFalse(is_integer(1.1))
        self.assertFalse(is_integer("1.1"))
        self.assertFalse(is_integer("abc"))


class TestIsEmpty(unittest.TestCase):

    def test_empty_values(self):
        self.assertTrue(is_empty(None))
        self.assertTrue(is_empty(""))
        self.assertTrue(is_empty("None"))

    def test_non_empty_values(self):
        self.assertFalse(is_empty("abc"))
        self.assertFalse(is_empty(1))


class TestListFlatten(unittest.TestCase):

    def test_flatten(self):
        self.assertEqual(list_flatten([[1, 2], [3, 4]]), [1, 2, 3, 4])


class TestJoinSelectedValueInListOfDicts(unittest.TestCase):

    def test_join(self):
        self.assertEqual(join_selected_value_in_list_of_dicts([{'a': 1}, {'a': 2}], 'a', ','),
                         '1,2')

    def test_empty(self):
        self.assertEqual(join_selected_value_in_list_of_dicts([{'a': None}, {'a': ''}], 'a', ','),
                         '')


class TestReadDict(unittest.TestCase):

    def test_from_dict(self):
        self.assertEqual(read_dict({'a': 1}), {'a': 1})

    def test_from_json_str(self):
        self.assertEqual(read_dict(json.dumps({'a': 1})), {'a': 1})

    def test_from_file(self):
        with open('temp.json', 'w') as f:
            json.dump({'a': 1}, f)
        self.assertEqual(read_dict('temp.json'), {'a': 1})
        os.remove('temp.json')

    def test_invalid_input(self):
        self.assertIsNone(read_dict(123))
        self.assertIsNone(read_dict('[invalid json'))

    def test_empty_dict(self):
        self.assertEqual(read_dict({}), {})

    def test_empty_string(self):
        self.assertIsNone(read_dict(''))

    def test_nonexistent_file(self):
        self.assertIsNone(read_dict('nonexistent_file.json'))

    def test_invalid_json_str(self):
        self.assertIsNone(read_dict('{"a":1,}'))  # invalid JSON due to trailing comma

    def test_empty_file(self):
        with open('empty.json', 'w'):
            pass
        self.assertIsNone(read_dict('empty.json'))
        os.remove('empty.json')

    def test_file_with_invalid_json(self):
        with open('invalid.json', 'w') as f:
            f.write('{"a":1,}')
        self.assertIsNone(read_dict('invalid.json'))
        os.remove('invalid.json')

    def test_none_input(self):
        self.assertIsNone(read_dict(None))

    def test_boolean_input(self):
        self.assertIsNone(read_dict(True))
        self.assertIsNone(read_dict(False))


class TestFindEdgesConnections(unittest.TestCase):

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['col1', 'col2'])
        result = find_edges_connections(df)
        self.assertTrue(result.empty)

    def test_singletons(self):
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [None, None, None]})
        result = find_edges_connections(df)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(result.apply(lambda x: x['group_id'] != x['value'], axis=1)))

    def test_pairs(self):
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [2, 3, 4]})
        result = find_edges_connections(df)
        self.assertEqual(len(result), 4)
        self.assertEqual(len(result['group_id'].unique()), 1)

    def test_multiple_groups(self):
        df = pd.DataFrame({'col1': [1, 2, 3, 4, 5, 6], 'col2': [2, 3, None, 5, 6, None]})
        result = find_edges_connections(df)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(result['group_id'].unique()), 2)

    def test_complex_case(self):
        df = pd.DataFrame({'col1': [1, 2, 3, 4, 5, 6, 7], 'col2': [2, 3, 4, 5, 6, 7, 8]})
        result = find_edges_connections(df)
        self.assertEqual(len(result), 8)
        self.assertEqual(len(result['group_id'].unique()), 1)


if __name__ == '__main__':
    unittest.main()

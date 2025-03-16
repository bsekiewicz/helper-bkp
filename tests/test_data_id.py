import unittest
import uuid
from hashlib import sha256

from helper.data_id import convert_text_to_key, convert_text_to_uuid, convert_data_to_id


class TestConvertTextToKey(unittest.TestCase):

    def test_empty_input(self):
        self.assertIsNone(convert_text_to_key(None))
        self.assertIsNone(convert_text_to_key(""))
        self.assertIsNone(convert_text_to_key(" "))

    def test_diacritics_removal(self):
        self.assertEqual(convert_text_to_key("zażółć gęślą jaźń"), "zazolc_gesla_jazn")

    def test_lowercase_conversion(self):
        self.assertEqual(convert_text_to_key("LOWERCASE"), "lowercase")

    def test_space_removal(self):
        self.assertEqual(convert_text_to_key(" remove spaces "), "remove_spaces")

    def test_non_alphanumeric_removal(self):
        self.assertEqual(convert_text_to_key("remove!@#$%^&*()"), "remove")

    def test_full_conversion(self):
        self.assertEqual(convert_text_to_key("  This IS a Compl3x  !@# Example  "), "this_is_a_compl3x_example")


class TestConvertTextToUUID(unittest.TestCase):

    def test_empty_input(self):
        self.assertEqual(convert_text_to_uuid(''), str(uuid.uuid3(uuid.NAMESPACE_X500, '')))

    def test_varied_text(self):
        self.assertEqual(convert_text_to_uuid('test'),
                         str(uuid.uuid3(uuid.NAMESPACE_X500, 'test')))
        self.assertEqual(convert_text_to_uuid('another_test'),
                         str(uuid.uuid3(uuid.NAMESPACE_X500, 'another_test')))
        self.assertEqual(convert_text_to_uuid('123456'),
                         str(uuid.uuid3(uuid.NAMESPACE_X500, '123456')))

    def test_special_characters(self):
        self.assertEqual(convert_text_to_uuid('!@#$%^&*()'), str(uuid.uuid3(uuid.NAMESPACE_X500, '!@#$%^&*()')))

    def test_consistency(self):
        # UUID should be the same for the same input string
        self.assertEqual(convert_text_to_uuid('consistent'), convert_text_to_uuid('consistent'))

    def test_uniqueness(self):
        # UUID should be different for different input strings
        self.assertNotEqual(convert_text_to_uuid('unique1'), convert_text_to_uuid('unique2'))


class TestConvertDataToID(unittest.TestCase):

    def test_dummy_comparison(self):
        self.assertEqual(convert_data_to_id({'b': [2, 1], 'a': ['None', 'a']}),
                         convert_data_to_id({'a': ['None', 'a'], 'b': [2, 1]}))
        self.assertEqual(convert_data_to_id({'b': [2, 1], 'a': ['None', 'a']}),
                         convert_data_to_id({'a': ['a', 'None'], 'b': [1, 2]}))

    def test_empty_input(self):
        self.assertIsNone(convert_data_to_id(None))

        self.assertEqual(convert_data_to_id(b'', method='uuid'), '5150bdd9-c6ab-3d68-a915-e58d5ac56d50')
        self.assertEqual(convert_data_to_id('', method='uuid'), '5150bdd9-c6ab-3d68-a915-e58d5ac56d50')
        self.assertEqual(convert_data_to_id([], method='uuid'), '2061443b-712a-3816-bbf6-0e31a077be9f')
        self.assertEqual(convert_data_to_id({}, method='uuid'), '46369ab4-05ab-36da-bb30-49738a5110c9')

    def test_bytes_input(self):
        data = b'test bytes'
        hash_obj = sha256()
        hash_obj.update(data)
        expected_sha256 = hash_obj.hexdigest()
        self.assertEqual(convert_data_to_id(data, method='sha256'), expected_sha256)
        self.assertEqual(convert_data_to_id(data, method='uuid'),
                         str(uuid.uuid3(uuid.NAMESPACE_X500, f'sha256={expected_sha256}')))

    def test_str_input(self):
        data = 'test string'
        hash_obj = sha256()
        hash_obj.update(data.encode('utf-8'))
        expected_sha256 = hash_obj.hexdigest()
        self.assertEqual(convert_data_to_id(data, method='sha256'), expected_sha256)
        self.assertEqual(convert_data_to_id(data, method='uuid'),
                         str(uuid.uuid3(uuid.NAMESPACE_X500, f'sha256={expected_sha256}')))

    def test_invalid_method(self):
        data = 'test string'
        self.assertIsNone(convert_data_to_id(data, method='invalid_method'))

    def test_consistency(self):
        # ID should be the same for the same input data
        self.assertEqual(convert_data_to_id('consistent', method='sha256'),
                         convert_data_to_id('consistent', method='sha256'))
        self.assertEqual(convert_data_to_id('consistent', method='uuid'),
                         convert_data_to_id('consistent', method='uuid'))

    def test_uniqueness(self):
        # ID should be different for different input data
        self.assertNotEqual(convert_data_to_id('unique1', method='sha256'),
                            convert_data_to_id('unique2', method='sha256'))
        self.assertNotEqual(convert_data_to_id('unique1', method='uuid'),
                            convert_data_to_id('unique2', method='uuid'))

    def test_edge_cases(self):
        # Test with a very long string
        long_str = "a" * 10000
        self.assertIsNotNone(convert_data_to_id(long_str, method='sha256'))
        self.assertIsNotNone(convert_data_to_id(long_str, method='uuid'))

        # Test with a very long bytes array
        long_bytes = b"a" * 10000
        self.assertIsNotNone(convert_data_to_id(long_bytes, method='sha256'))
        self.assertIsNotNone(convert_data_to_id(long_bytes, method='uuid'))


if __name__ == '__main__':
    unittest.main()

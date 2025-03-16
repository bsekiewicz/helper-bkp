import json
import unittest
from datetime import datetime
from decimal import Decimal

from helper.data_format import data_standardization, remove_diacritics, parse_date, parse_price, convert_to_gtin


class TestDataStandardization(unittest.TestCase):

    def test_list(self):
        self.assertEqual(data_standardization([3, 2, 1]), json.dumps([1, 2, 3]))

    def test_dict(self):
        self.assertEqual(data_standardization({"b": 1, "a": 2}), json.dumps({"a": 2, "b": 1}))

    def test_nested(self):
        self.assertEqual(data_standardization({"list": [3, 2, 1], "int": 1}), json.dumps({"int": 1, "list": [1, 2, 3]}))

    def test_mixed_types_in_list(self):
        self.assertEqual(data_standardization([3, "a", {"key": "value"}]), json.dumps([3, "a", {"key": "value"}]))

    def test_nested_dicts(self):
        self.assertEqual(data_standardization({"outer": {"b": 1, "a": 2}, "inner": 1}),
                         json.dumps({"inner": 1, "outer": {"a": 2, "b": 1}}))

    def test_mixed_types_in_dict(self):
        self.assertEqual(data_standardization({"int": 1, "list": [3, 2, 1], "string": "a"}),
                         json.dumps({"int": 1, "list": [1, 2, 3], "string": "a"}))

    def test_non_json_serializable_types(self):
        self.assertEqual(data_standardization({"date": datetime(2021, 9, 1)}),
                         json.dumps({"date": "2021-09-01 00:00:00"}))

    def test_empty_structures(self):
        self.assertEqual(data_standardization([]), json.dumps([]))
        self.assertEqual(data_standardization({}), json.dumps({}))

    def test_data_standardization_dummy_comparison(self):
        self.assertEqual(data_standardization({'b': {'x': [1, 2, 3], 'y': None}, 'a': ['None', 'a']}),
                         data_standardization({'a': ['None', 'a'], 'b': {'y': None, 'x': [2, 3, 1]}}))

        self.assertEqual(data_standardization({'mixed_list': [1, None, 'a']}),
                         data_standardization({'mixed_list': [None, 'a', 1]}))

        self.assertEqual(data_standardization([1, None, 'a', '1']),
                         data_standardization(["1", None, 'a', 1]))

    def test_boolean(self):
        self.assertEqual(data_standardization(True), True)
        self.assertEqual(data_standardization(False), False)

    def test_integer(self):
        self.assertEqual(data_standardization(42), 42)

    def test_string(self):
        self.assertEqual(data_standardization("Just a string"), "Just a string")

    def test_none(self):
        self.assertIsNone(data_standardization(None))

    def test_mixed_types(self):
        self.assertEqual(data_standardization([True, 42, None, "string", [1, 2], {"key": "value"}]),
                         json.dumps([42, None, True, [1, 2], "string", {"key": "value"}]))


class TestRemoveDiacritics(unittest.TestCase):

    def test_empty(self):
        self.assertIsNone(remove_diacritics(None))
        self.assertEqual(remove_diacritics(''), '')

    def test_polish_diacritics(self):
        self.assertEqual(remove_diacritics('zażółć gęślą jaźń'), 'zazolc gesla jazn')
        self.assertEqual(remove_diacritics('ZAŻÓŁĆ GĘŚLĄ JAŹŃ'), 'ZAZOLC GESLA JAZN')

    def test_other_diacritics(self):
        self.assertEqual(remove_diacritics('àáâãåāăąǎạầấẫẩậằắẵẳặ'), 'aaaaaaaaaaaaaaaaaaaa')
        self.assertEqual(remove_diacritics('ÀÁÂÃÅĀĂĄǍẠẦẤẪẨẬẰẮẴẲẶ'), 'AAAAAAAAAAAAAAAAAAAA')

    def test_mixed_characters(self):
        self.assertEqual(remove_diacritics('Hello żółć!'), 'Hello zolc!')

    def test_non_latin_characters(self):
        self.assertEqual(remove_diacritics('Привет žółć!'), 'Привет zolc!')

    def test_numbers_and_symbols(self):
        self.assertEqual(remove_diacritics('1234!@#$ żółć'), '1234!@#$ zolc')

    def test_whitespace(self):
        self.assertEqual(remove_diacritics(' \t\nżółć \t\n'), ' \t\nzolc \t\n')


class TestParseDate(unittest.TestCase):

    def test_standard_format(self):
        self.assertEqual(parse_date("2021-09-01"), "2021-09-01")

    def test_varied_formats(self):
        self.assertEqual(parse_date("September 1, 2021"), "2021-09-01")
        self.assertEqual(parse_date("1st Sep 2021"), "2021-09-01")

    def test_invalid_date(self):
        self.assertIsNone(parse_date("Invalid date"))

    def test_to_datetime(self):
        self.assertEqual(parse_date("2021-09-01", to_string=False), datetime(2021, 9, 1))

    def test_different_date_formats(self):
        self.assertEqual(parse_date("01/09/2021"), "2021-09-01")
        self.assertEqual(parse_date("09/01/2021", date_ordered='MDY'), "2021-09-01")

    def test_language_specific_formats(self):
        self.assertEqual(parse_date("1er septembre 2021"), "2021-09-01")
        self.assertEqual(parse_date("1. September 2021"), "2021-09-01")

    def test_time_included(self):
        self.assertEqual(parse_date("2021-09-01 12:34:56"), "2021-09-01")

    def test_edge_cases(self):
        self.assertEqual(parse_date("29/02/2020"), "2020-02-29")  # Leap year
        self.assertEqual(parse_date("31/12/2021"), "2021-12-31")  # End of the month

    def test_empty_and_none(self):
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date(None))

    def test_polish_dates(self):
        self.assertEqual(parse_date("1 września 2021"), "2021-09-01")
        self.assertEqual(parse_date("1 wrz 2021"), "2021-09-01")
        self.assertEqual(parse_date("31 grudnia 2021"), "2021-12-31")
        self.assertEqual(parse_date("29 lutego 2020"), "2020-02-29")  # Leap year
        self.assertEqual(parse_date("1 stycznia 2022"), "2022-01-01")  # New Year

    def test_invalid_dates(self):
        self.assertIsNone(parse_date("This is not a date"))  # Invalid string
        self.assertIsNone(parse_date("2021-02-30"))  # February 30th doesn't exist
        # self.assertIsNone(parse_date("2021-13-01"))  # 13th month doesn't exist
        self.assertIsNone(parse_date("29/02/2021"))  # 2021 is not a leap year
        self.assertIsNone(parse_date("2021-00-00"))  # Day and month can't be zeros
        self.assertIsNone(parse_date("abcd"))  # Random string
        self.assertIsNone(parse_date("2021/09/31"))  # September 31st doesn't exist


class TestParsePrice(unittest.TestCase):

    def test_standard_format(self):
        amount, currency = parse_price("$1234.56")
        self.assertEqual(amount, "1234.56")
        self.assertEqual(currency, "USD")

    def test_varied_formats(self):
        tests = [
            ("€1234.56", "1234.56", "EUR"),
            ("£1234.56", "1234.56", "GBP"),
            ("¥1234", "1234.00", "JPY"),
            ("Fr.1234.56", "1234.56", "CHF"),
            ("zł1234.56", "1234.56", "PLN"),
            ("Kč1234.56", "1234.56", "CZK"),
            ("Ft1234.56", "1234.56", "HUF"),
            ("₽1234.56", "1234.56", "RUB"),
            ("₺1234.56", "1234.56", "TRY"),
            ("lei1234.56", "1234.56", "RON"),
            ("лв1234.56", "1234.56", "BGN"),
            ("kn1234.56", "1234.56", "HRK"),
            ("Íkr1234.56", "1234.56", "ISK"),
            ("KM1234.56", "1234.56", "BAM"),
            ("ден1234.56", "1234.56", "MKD"),
            ("дин.1234.56", "1234.56", "RSD"),
            ("₴1234.56", "1234.56", "UAH"),
            ("$1234.56", "1234.56", "USD"),
            ("A$1234.56", "1234.56", "AUD"),
            ("₩1234", "1234.00", "KRW"),
            ("1,234.56 €", "1234.56", "EUR"),
        ]
        for test_input, expected_amount, expected_currency in tests:
            amount, currency = parse_price(test_input)
            self.assertEqual(amount, expected_amount)
            self.assertEqual(currency, expected_currency)

    # # TODO:
    # def test_negative_amounts(self):
    #     tests = [
    #         # Test cases with negative amounts
    #         ("-$1234.56", "-1234.56", "USD"),
    #         ("-€1234.56", "-1234.56", "EUR"),
    #         ("-¥1234", "-1234.00", "JPY"),
    #         ("-Fr.1234.56", "-1234.56", "CHF"),
    #         ("-zł1234.56", "-1234.56", "PLN"),
    #         ("-₽1234.56", "-1234.56", "RUB"),
    #         ("-₺1234.56", "-1234.56", "TRY"),
    #         ("-lei1234.56", "-1234.56", "RON"),
    #         ("-лв1234.56", "-1234.56", "BGN"),
    #         ("-₴1234.56", "-1234.56", "UAH"),
    #         ("-£1234.56", "-1234.56", "GBP"),
    #         ("-1234.56$", "-1234.56", "USD")  # Negative amount with the symbol after the amount
    #     ]
    #     for test_input, expected_amount, expected_currency in tests:
    #         amount, currency = parse_price(test_input)
    #         self.assertEqual(amount, expected_amount)
    #         self.assertEqual(currency, expected_currency)

    def test_no_to_string(self):
        amount, currency = parse_price("$1234.56", to_string=False)
        self.assertEqual(amount, Decimal("1234.56"))
        self.assertEqual(currency, "USD")

    def test_currency_fixed(self):
        amount, currency = parse_price("$1234.56", currency_fixed="EUR")
        self.assertEqual(amount, "1234.56")
        self.assertEqual(currency, "EUR")

    def test_no_iso3_currency(self):
        amount, currency = parse_price("$1234.56", iso3_currency=False)
        self.assertEqual(amount, "1234.56")
        self.assertEqual(currency, "$")

    def test_invalid_prices(self):
        invalid_inputs = [
            "This is not a price",
            "abcd",
            "1234.567.89",
        ]
        for test_input in invalid_inputs:
            amount, currency = parse_price(test_input)
            self.assertIsNone(amount)
            self.assertIsNone(currency)

    def test_empty_and_none(self):
        amount, currency = parse_price("")
        self.assertIsNone(amount)
        self.assertIsNone(currency)

        amount, currency = parse_price(None)
        self.assertIsNone(amount)
        self.assertIsNone(currency)

    def test_space_separator(self):
        tests = [
            ("$1\u00A0234.56", "1234.56", "USD"),
            ("€1\u00A0234.56", "1234.56", "EUR"),
            ("£1\u00A0234.56", "1234.56", "GBP"),
            ("1 234.56 USD", "1234.56", "USD"),
            ("1\u00A0222 234.56 EUR", "1222234.56", "EUR"),
            ("1 234.56 £", "1234.56", "GBP"),
        ]
        for test_input, expected_amount, expected_currency in tests:
            amount, currency = parse_price(test_input)
            self.assertEqual(amount, expected_amount)
            self.assertEqual(currency, expected_currency)

    def test_apostrophe_separator(self):
        tests = [
            ("CHF 1'234.56", "1234.56", "CHF"),
            # ... add more if you encounter other currencies using this format
        ]
        for test_input, expected_amount, expected_currency in tests:
            amount, currency = parse_price(test_input)
            self.assertEqual(amount, expected_amount)
            self.assertEqual(currency, expected_currency)


class TestConvertToGTIN(unittest.TestCase):
    def test_convert_to_gtin(self):
        # valid GTINs
        assert convert_to_gtin('0000000000000') == '00000000000000'
        assert convert_to_gtin('0012345678905') == '00012345678905'

        # invalid GTINs
        assert convert_to_gtin('0000000000001') is None
        assert convert_to_gtin('1234567890124') is None
        assert convert_to_gtin('3214567890122') is None
        assert convert_to_gtin('5432145678902') is None
        assert convert_to_gtin('9876543210988') is None

        # invalid input
        assert convert_to_gtin(None) is None
        assert convert_to_gtin('a') is None
        assert convert_to_gtin('12345678') is None
        assert convert_to_gtin('123456789012345') is None


if __name__ == '__main__':
    unittest.main()

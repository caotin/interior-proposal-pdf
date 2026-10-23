import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quote', ROOT / 'scripts/check_quote.py')
quote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quote)


class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'examples/riverside-living/quote.json').read_text())

    def test_decimal_quantities_and_included_tax(self):
        result = quote.check(self.data)
        self.assertTrue(result['ok'])
        self.assertEqual(result['total_vnd'], 39640000)
        self.assertEqual(result['vat_vnd'], 0)

    def test_incorrect_line_amount_is_rejected(self):
        self.data['items'][0]['amount_vnd'] += 1
        self.assertFalse(quote.check(self.data)['ok'])

    def test_incorrect_group_subtotal_is_rejected(self):
        self.data['groups'][0]['subtotal_vnd'] += 1
        self.assertFalse(quote.check(self.data)['ok'])

    def test_incorrect_grand_total_is_rejected(self):
        self.data['total_vnd'] += 1
        self.assertFalse(quote.check(self.data)['ok'])

    def test_tax_is_added_after_overall_discount(self):
        self.data.update(tax_mode='excluded', vat_rate='0.08', discount_vnd=640000,
                         vat_vnd=3120000, total_vnd=42120000)
        self.assertTrue(quote.check(self.data)['ok'])

    def test_duplicate_item_id_is_rejected(self):
        self.data['items'][1]['id'] = self.data['items'][0]['id']
        with self.assertRaises(ValueError):
            quote.check(self.data)

    def test_nonfinite_quantity_is_rejected(self):
        self.data['items'][0]['quantity'] = 'NaN'
        with self.assertRaises(ValueError):
            quote.check(self.data)

    def test_boolean_price_is_rejected(self):
        self.data['items'][0]['unit_price_vnd'] = True
        with self.assertRaises(ValueError):
            quote.check(self.data)

    def test_half_vnd_rounds_up(self):
        self.data['items'] = [dict(self.data['items'][0], quantity='0.5',
                                   unit_price_vnd=1, amount_vnd=1)]
        self.data['groups'][0]['subtotal_vnd'] = 1
        self.data.update(subtotal_vnd=1, total_vnd=1)
        self.assertTrue(quote.check(self.data)['ok'])

    def test_source_input_is_not_mutated(self):
        original = copy.deepcopy(self.data)
        quote.check(self.data)
        self.assertEqual(self.data, original)


if __name__ == '__main__':
    unittest.main()

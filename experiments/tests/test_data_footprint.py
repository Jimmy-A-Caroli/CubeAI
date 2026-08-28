import unittest

from experiments.data_footprint import build_result_document, deep_size
from experiments.model import make_cards


class DataFootprintTests(unittest.TestCase):
    def test_deep_size_counts_nested_content_once(self):
        shared = [1, 2, 3]
        self.assertGreater(deep_size([shared, shared]), deep_size(shared))
        self.assertLess(deep_size([shared, shared]), deep_size([shared, list(shared)]))

    def test_larger_cube_uses_more_memory(self):
        self.assertGreater(deep_size(make_cards(720, 1)), deep_size(make_cards(360, 1)))

    def test_result_document_records_repetitions_and_elapsed_measurements(self):
        document = build_result_document(seed=5, repetitions=1)

        self.assertEqual(1, document["repetitions"])
        self.assertTrue(all("elapsed_seconds" in case for case in document["cases"]))


if __name__ == "__main__":
    unittest.main()

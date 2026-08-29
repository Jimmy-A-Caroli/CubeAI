import json
import unittest

from experiments.data_volume import (
    StorageBytes,
    StorageRows,
    StorageSample,
    measure_sample,
    project,
)


class DataVolumeTests(unittest.TestCase):
    def setUp(self):
        self.sample = StorageSample(
            drafts=1_000,
            seed=17,
            row_counts=StorageRows(
                pick_rows=360_000,
                seen_rows=2_880_000,
                pool_rows=360_000,
                run_metadata_rows=1_000,
            ),
            byte_counts=StorageBytes(
                pick_rows_bytes=12_000_000,
                seen_rows_bytes=72_000_000,
                pool_data_bytes=11_000_000,
                run_metadata_bytes=40_000,
                compact_ndjson_bytes=95_040_000,
                gzip_ndjson_bytes=13_000_000,
                sqlite_bytes=82_000_000,
            ),
        )

    def test_projection_scales_all_measured_components_linearly(self):
        # A mistaken projection that omits a component or uses the target as a
        # measured value would make the storage estimate misleading.
        projected = project(self.sample, 10_000)

        self.assertEqual("projection", projected.record_type)
        self.assertEqual(10_000, projected.target_drafts)
        self.assertEqual(3_600_000, projected.row_counts.pick_rows)
        self.assertEqual(28_800_000, projected.row_counts.seen_rows)
        self.assertEqual(3_600_000, projected.row_counts.pool_rows)
        self.assertEqual(10_000, projected.row_counts.run_metadata_rows)
        self.assertEqual(120_000_000, projected.byte_counts.pick_rows_bytes)
        self.assertEqual(720_000_000, projected.byte_counts.seen_rows_bytes)
        self.assertEqual(110_000_000, projected.byte_counts.pool_data_bytes)
        self.assertEqual(400_000, projected.byte_counts.run_metadata_bytes)
        self.assertEqual(950_400_000, projected.byte_counts.compact_ndjson_bytes)
        self.assertEqual(130_000_000, projected.byte_counts.gzip_ndjson_bytes)
        self.assertEqual(820_000_000, projected.byte_counts.sqlite_bytes)

    def test_projection_serialization_never_labels_an_estimate_as_measured(self):
        # This catches a reporting regression that could present a linear
        # estimate as an observation from the generated sample.
        rendered = json.dumps(project(self.sample, 100_000).to_dict())

        self.assertNotIn("measured", rendered)
        self.assertIn('"record_type": "projection"', rendered)

    def test_measured_sample_counts_real_draft_events_and_storage_encodings(self):
        # This catches a probe that reports requested geometry rather than rows
        # and bytes actually emitted to the temporary serialization targets.
        measured = measure_sample(1, seed=23)

        self.assertEqual("measured_sample", measured.record_type)
        self.assertEqual(360, measured.row_counts.pick_rows)
        self.assertEqual(2_880, measured.row_counts.seen_rows)
        self.assertEqual(360, measured.row_counts.pool_rows)
        self.assertEqual(1, measured.row_counts.run_metadata_rows)
        self.assertGreater(measured.byte_counts.pick_rows_bytes, 0)
        self.assertGreater(measured.byte_counts.seen_rows_bytes, 0)
        self.assertGreater(measured.byte_counts.pool_data_bytes, 0)
        self.assertGreater(measured.byte_counts.run_metadata_bytes, 0)
        self.assertGreater(measured.byte_counts.compact_ndjson_bytes, 0)
        self.assertGreater(measured.byte_counts.gzip_ndjson_bytes, 0)
        self.assertGreater(measured.byte_counts.sqlite_bytes, 0)


if __name__ == "__main__":
    unittest.main()

import unittest

from experiments.analytics import aggregate_python, aggregate_sqlite
from experiments.model import PickEvent, SyntheticCard


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        # Each nested tuple is one synthetic two-seat draft.  Card 1 in the
        # first draft is seen by seat 0 at picks one and three, so it satisfies
        # this spike's synthetic wheel definition (two seats => two picks).
        self.cards = (
            SyntheticCard(1, 1.0, "W", 1, ("aggro",)),
            SyntheticCard(2, 1.0, "U", 2, ("control",)),
            SyntheticCard(3, 1.0, "W", 3, ("aggro", "artifacts")),
            SyntheticCard(4, 1.0, "B", 4, ("control",)),
            SyntheticCard(5, 1.0, "R", 5, ("artifacts",)),
            SyntheticCard(6, 1.0, "G", 6, ("graveyard",)),
        )
        self.events = (
            (
                PickEvent(0, 0, 0, 2, (1, 2, 3)),
                PickEvent(0, 0, 1, 4, (4, 5, 6)),
                PickEvent(0, 1, 0, 5, (5, 6)),
                PickEvent(0, 1, 1, 3, (1, 3)),
                PickEvent(0, 2, 0, 1, (1,)),
                PickEvent(0, 2, 1, 6, (6,)),
            ),
            (
                PickEvent(0, 0, 0, 1, (1, 2, 3)),
                PickEvent(0, 0, 1, 5, (4, 5, 6)),
                PickEvent(0, 1, 0, 4, (4, 6)),
                PickEvent(0, 1, 1, 2, (2, 3)),
                PickEvent(0, 2, 0, 6, (6,)),
                PickEvent(0, 2, 1, 3, (3,)),
            ),
        )
        self.expected = {
            "average_pick": [
                {"card_id": 1, "value": 2.0},
                {"card_id": 2, "value": 1.5},
                {"card_id": 3, "value": 2.5},
                {"card_id": 4, "value": 1.5},
                {"card_id": 5, "value": 1.5},
                {"card_id": 6, "value": 3.0},
            ],
            "median_pick": [
                {"card_id": 1, "value": 2.0},
                {"card_id": 2, "value": 1.5},
                {"card_id": 3, "value": 2.5},
                {"card_id": 4, "value": 1.5},
                {"card_id": 5, "value": 1.5},
                {"card_id": 6, "value": 3.0},
            ],
            "first_seen": [
                {"card_id": 1, "value": 1.0},
                {"card_id": 2, "value": 1.0},
                {"card_id": 3, "value": 1.0},
                {"card_id": 4, "value": 1.0},
                {"card_id": 5, "value": 1.0},
                {"card_id": 6, "value": 1.0},
            ],
            "last_pick_rate": [
                {"card_id": 1, "value": 0.5},
                {"card_id": 2, "value": 0.0},
                {"card_id": 3, "value": 0.5},
                {"card_id": 4, "value": 0.0},
                {"card_id": 5, "value": 0.0},
                {"card_id": 6, "value": 1.0},
            ],
            "wheel_rate": [
                {"card_id": 1, "value": 0.5},
                {"card_id": 2, "value": 0.0},
                {"card_id": 3, "value": 0.0},
                {"card_id": 4, "value": 0.0},
                {"card_id": 5, "value": 0.0},
                {"card_id": 6, "value": 0.5},
            ],
            "color_utilization": [
                {"color": "B", "value": 1 / 6},
                {"color": "G", "value": 1 / 6},
                {"color": "R", "value": 1 / 6},
                {"color": "U", "value": 1 / 6},
                {"color": "W", "value": 2 / 6},
            ],
            "card_utilization": [
                {"card_id": card_id, "value": 1.0} for card_id in range(1, 7)
            ],
            "tag_frequency": [
                {"tag": "aggro", "value": 4},
                {"tag": "artifacts", "value": 4},
                {"tag": "control", "value": 4},
                {"tag": "graveyard", "value": 2},
            ],
            "cooccurrence": [
                {"card_ids": [1, 2], "value": 1},
                {"card_ids": [1, 4], "value": 1},
                {"card_ids": [1, 5], "value": 1},
                {"card_ids": [1, 6], "value": 1},
                {"card_ids": [2, 3], "value": 1},
                {"card_ids": [2, 5], "value": 2},
                {"card_ids": [3, 4], "value": 1},
                {"card_ids": [3, 5], "value": 1},
                {"card_ids": [3, 6], "value": 1},
                {"card_ids": [4, 6], "value": 2},
            ],
        }

    def test_hand_calculated_metrics_are_identical_for_both_backends(self):
        # This detects incorrect pick indexing, first-seen tracking, last-pick
        # detection, the synthetic wheel threshold, and pool pair boundaries.
        self.assertEqual(self.expected, aggregate_python(self.events, self.cards))
        self.assertEqual(self.expected, aggregate_sqlite(self.events, self.cards))


if __name__ == "__main__":
    unittest.main()

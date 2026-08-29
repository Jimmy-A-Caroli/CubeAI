import unittest

from experiments.bot_simulation import (
    benchmark_batches,
    choose_bot0,
    choose_bot1,
    choose_bot2,
)
from experiments.model import SyntheticCard


class BotSimulationTests(unittest.TestCase):
    def setUp(self):
        # A hand-checked fixture: card 3 has the best raw rating; card 2 is
        # blue and overtakes it in a blue-heavy pool; card 1 is cheap enough
        # to overtake card 3 when the pool's normalized curve is high.
        self.cards = (
            SyntheticCard(0, 1.0, "W", 1, ("aggro",)),
            SyntheticCard(1, 4.7, "G", 2, ("aggro",)),
            SyntheticCard(2, 4.6, "U", 5, ("control",)),
            SyntheticCard(3, 5.0, "R", 5, ("control",)),
        )

    def test_bot0_selects_raw_rating_winner(self):
        self.assertEqual(3, choose_bot0(self.cards, ()))

    def test_bot1_selects_color_fit_winner_for_blue_heavy_pool(self):
        self.assertEqual(2, choose_bot1(self.cards, (0, 1, 1)))

    def test_bot2_selects_lower_curve_winner_for_top_heavy_pool(self):
        self.assertEqual(1, choose_bot2(self.cards, (0, 0, 0, 6, 6)))

    def test_equal_scores_choose_the_lowest_card_id(self):
        tied_cards = (
            SyntheticCard(8, 4.0, "U", 4, ("control",)),
            SyntheticCard(5, 4.0, "R", 4, ("control",)),
        )

        self.assertEqual(5, choose_bot0(tied_cards, ()))

    def test_benchmark_checksums_are_repeatable_for_fixed_seed(self):
        first = benchmark_batches((100,), seed=20260828, strategy=choose_bot2)
        second = benchmark_batches((100,), seed=20260828, strategy=choose_bot2)

        self.assertEqual(first[0]["checksum"], second[0]["checksum"])
        self.assertEqual(100, first[0]["drafts"])


if __name__ == "__main__":
    unittest.main()

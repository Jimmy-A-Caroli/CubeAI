import unittest

from experiments.draft_engine import run_draft
from experiments.model import make_cards


class DraftEngineTests(unittest.TestCase):
    def test_standard_draft_is_deterministic_and_conserves_instances(self):
        cards = make_cards(360, seed=17)
        first = run_draft(cards, 8, 3, 15, seed=20260828)
        second = run_draft(cards, 8, 3, 15, seed=20260828)
        self.assertEqual(first.events, second.events)
        picked = [event.card_id for event in first.events]
        self.assertEqual(360, len(picked))
        self.assertEqual(360, len(set(picked)))
        self.assertTrue(first.complete)
        self.assertEqual([45] * 8, [len(pool) for pool in first.pools])

    def test_pack_directions_alternate(self):
        result = run_draft(make_cards(24, 9), 4, 2, 3, seed=11)
        self.assertEqual((1, -1), result.pack_directions)

    def test_insufficient_cards_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires 24 cards"):
            run_draft(make_cards(23, 1), 4, 2, 3, seed=2)

    def test_chooser_receives_card_attributes_and_seen_ids_precede_removal(self):
        seen_packs = []

        def choose_lowest_rating(pack, pool):
            seen_packs.append(tuple(card.card_id for card in pack))
            return min(pack, key=lambda card: card.rating).card_id

        result = run_draft(make_cards(4, 3), 2, 1, 2, seed=4, chooser=choose_lowest_rating)

        self.assertEqual(4, len(seen_packs))
        self.assertEqual(
            tuple(event.seen_card_ids for event in result.events), tuple(seen_packs)
        )
        cards_by_id = {card.card_id: card for card in make_cards(4, 3)}
        self.assertEqual(
            [event.card_id for event in result.events],
            [min(pack, key=lambda card_id: cards_by_id[card_id].rating) for pack in seen_packs],
        )


if __name__ == "__main__":
    unittest.main()

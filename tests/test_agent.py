"""Parser/state/branch checks with tool doubles, distinct from live model runs."""

import unittest
from unittest.mock import patch

import agent
import config
from utils.data_loader import get_example_wardrobe, load_listings


class ParserTests(unittest.TestCase):
    def test_documented_query_shapes(self):
        cases = [
            ("looking for a vintage graphic tee under $30, size M", "vintage graphic tee", "M", 30.0),
            ("90s track jacket in size M", "90s track jacket", "M", None),
            ("platform sneakers size 8", "platform sneakers", "8", None),
            ("boots size US 8.5 below $50", "boots", "US 8.5", 50.0),
            ("jeans size W30 L30 up to $40", "jeans", "W30 L30", 40.0),
            ("jeans size W30/L30 under $40", "jeans", "W30/L30", 40.0),
            ("jeans size W30 / L30 under $40", "jeans", "W30 / L30", 40.0),
            ("shoes size 8/9", "shoes", "8/9", None),
            ("boots size US 8.5/US 9", "boots", "US 8.5/US 9", None),
            ("cardigan size One Size", "cardigan", "ONE SIZE", None),
            ("please find a jacket max 25.50 size L/XL", "jacket", "L/XL", 25.5),
            ("denim jacket $50", "denim jacket", None, 50.0),
            ("tee size extra large at most 20", "tee", "EXTRA LARGE", 20.0),
            ("designer ballgown size XXS under $5", "designer ballgown", "XXS", 5.0),
            ("vintage tee size 3XL", "vintage tee", "3XL", None),
            ("denim jacket", "denim jacket", None, None),
        ]
        for query, description, size, price in cases:
            with self.subTest(query=query):
                self.assertEqual(agent._parse_query(query), {
                    "description": description, "size": size, "max_price": price,
                })


    def test_trailing_period_does_not_drop_size(self):
        cases = [("vintage tee size M.", "M"),
                 ("boots size US 8.5.", "US 8.5"),
                 ("shoes size 8/9.", "8/9")]
        for query, size in cases:
            with self.subTest(query=query):
                self.assertEqual(agent._parse_query(query)["size"], size)



class LoopTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[1]
        self.wardrobe = get_example_wardrobe()

    def test_call_order_and_session_identity(self):
        calls = []
        def search(**kwargs):
            calls.append(("search", kwargs))
            return [self.item]
        def suggest(item, wardrobe):
            calls.append(("suggest", item, wardrobe))
            return "Specific outfit"
        def card(outfit, item):
            calls.append(("card", outfit, item))
            return "Grounded caption"
        with patch("agent.search_listings", side_effect=search), \
             patch("agent.suggest_outfit", side_effect=suggest), \
             patch("agent.create_fit_card", side_effect=card):
            session = agent.run_agent("vintage tee under $30, size M", self.wardrobe)
        self.assertEqual([call[0] for call in calls], ["search", "suggest", "card"])
        self.assertIs(session["selected_item"], session["search_results"][0])
        self.assertIs(calls[1][1], session["selected_item"])
        self.assertIs(calls[1][2], session["wardrobe"])
        self.assertEqual(calls[2][1], session["outfit_suggestion"])
        self.assertIs(calls[2][2], session["selected_item"])
        self.assertEqual(session["fit_card"], "Grounded caption")
        self.assertIsNone(session["error"])

    @patch("agent.create_fit_card")
    @patch("agent.suggest_outfit")
    def test_real_empty_search_stops_and_preserves_none(self, suggest, card):
        session = agent.run_agent("designer ballgown size XXS under $5", self.wardrobe)
        self.assertEqual(session["parsed"]["size"], "XXS")
        self.assertEqual(session["search_results"], [])
        self.assertIn("broader keywords", session["error"])
        for field in ("selected_item", "outfit_suggestion", "fit_card"):
            self.assertIsNone(session[field])
        suggest.assert_not_called()
        card.assert_not_called()

    @patch("agent.create_fit_card", return_value="caption")
    @patch("agent.suggest_outfit", return_value="outfit")
    def test_composite_sizes_are_not_truncated(self, suggest, card):
        jeans = agent.run_agent("jeans size W30/L30 under $40", self.wardrobe)
        self.assertEqual(jeans["parsed"]["size"], "W30/L30")
        self.assertEqual(jeans["selected_item"]["id"], "lst_001")
        suggest.reset_mock()
        card.reset_mock()
        shoes = agent.run_agent("shoes size 8/9", self.wardrobe)
        self.assertEqual(shoes["parsed"]["size"], "8/9")
        self.assertEqual(shoes["search_results"], [])
        suggest.assert_not_called()
        card.assert_not_called()

    def test_fresh_state_after_success(self):
        with patch("agent.search_listings", side_effect=[[self.item], []]), \
             patch("agent.suggest_outfit", return_value="outfit"), \
             patch("agent.create_fit_card", return_value="caption"):
            success = agent.run_agent("tee", self.wardrobe)
            empty = agent.run_agent("ballgown", self.wardrobe)
        self.assertIsNot(success, empty)
        self.assertEqual(success["fit_card"], "caption")
        self.assertIsNone(empty["fit_card"])
        self.assertIsNone(empty["selected_item"])

    def test_iteration_guard_runs_before_next_tool(self):
        with patch("config.MAX_ITERATIONS", 2), \
             patch("agent.search_listings", return_value=[self.item]), \
             patch("agent.suggest_outfit") as suggest, \
             patch("agent.create_fit_card") as card:
            with self.assertRaisesRegex(RuntimeError, "MAX_ITERATIONS"):
                agent.run_agent("tee", self.wardrobe)
        suggest.assert_not_called()
        card.assert_not_called()


if __name__ == "__main__":
    unittest.main()

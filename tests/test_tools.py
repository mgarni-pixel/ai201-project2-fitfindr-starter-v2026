"""Deterministic tool checks. Model doubles here are not live-model evidence."""

import unittest
from unittest.mock import patch

import config
import tools
from generate import ModelUnavailable
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings


class SizeTests(unittest.TestCase):
    def test_split_clothing_tags(self):
        for requested, listed in [("s", "S/M"), ("M", "S/M"), ("m", "M/L"),
                                  ("l", "M/L"), ("l", "L/XL"), ("xl", "L/XL")]:
            with self.subTest(requested=requested, listed=listed):
                self.assertTrue(tools._size_matches(requested, listed))

    def test_no_clothing_substrings_in_shoes_or_xl(self):
        for requested, listed in [("S", "US 9"), ("L", "XL"), ("L", "W30 L30")]:
            with self.subTest(requested=requested, listed=listed):
                self.assertFalse(tools._size_matches(requested, listed))

    def test_shoe_decimal_exactness(self):
        self.assertTrue(tools._size_matches("8", "US 8"))
        self.assertTrue(tools._size_matches("US 8.5", "US 8.5"))
        self.assertFalse(tools._size_matches("8", "US 8.5"))
        self.assertFalse(tools._size_matches("8.5", "US 8"))

    def test_waist_and_optional_inseam(self):
        self.assertTrue(tools._size_matches("W30", "W30 L30"))
        self.assertTrue(tools._size_matches("W30", "W30"))
        self.assertFalse(tools._size_matches("W30 L30", "W30"))
        self.assertFalse(tools._size_matches("W30", "W32"))

    def test_one_size_and_aliases(self):
        self.assertTrue(tools._size_matches("One Size", "One Size / Oversized"))
        self.assertFalse(tools._size_matches("M", "One Size / Oversized"))
        self.assertTrue(tools._size_matches("medium", "S/M"))
        self.assertTrue(tools._size_matches("extra large", "XL (oversized)"))
        self.assertFalse(tools._size_matches("XXS", "S/M"))


class SearchTests(unittest.TestCase):
    def test_price_ceiling_nonempty_and_inclusive(self):
        matches = tools.search_listings("vintage", max_price=20)
        self.assertTrue(matches)
        self.assertTrue(all(item["price"] <= 20 for item in matches))
        self.assertIn("lst_012", [item["id"] for item in matches])

    def test_price_size_and_description_together(self):
        matches = tools.search_listings("graphic tee", size="m", max_price=30)
        self.assertTrue(matches)
        self.assertTrue(all(tools._size_matches("M", x["size"]) for x in matches))
        self.assertTrue(all(x["price"] <= 30 for x in matches))
        self.assertEqual(matches[0]["id"], "lst_002")

    def test_empty_and_no_matches_are_lists(self):
        self.assertEqual(tools.search_listings("designer ballgown", "XXS", 5), [])
        self.assertEqual(tools.search_listings("vintage", max_price=-1), [])
        self.assertEqual(tools.search_listings(" "), [])
        self.assertEqual(tools.search_listings("looking for a"), [])

    def test_shape_limit_and_source_unchanged(self):
        original = load_listings()
        matches = tools.search_listings("vintage")
        self.assertLessEqual(len(matches), config.SEARCH_RESULT_LIMIT)
        self.assertTrue(all(set(x) == set(original[0]) for x in matches))
        self.assertEqual(load_listings(), original)

    def test_ties_keep_source_order(self):
        base = load_listings()[0]
        first = dict(base, id="first", title="vintage", description="", category="tops",
                     style_tags=[], colors=[], brand=None)
        second = dict(first, id="second")
        with patch("tools.load_listings", return_value=[first, second]):
            self.assertEqual(tools.search_listings("vintage"), [first, second])


class ModelToolTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[1]  # nullable brand

    @patch("tools.generate", return_value="  Pair it with your jeans.  ")
    def test_owned_items_are_in_prompt(self, generate):
        wardrobe = get_example_wardrobe()
        result = tools.suggest_outfit(self.item, wardrobe)
        self.assertEqual(result, "Pair it with your jeans.")
        prompt = generate.call_args.args[0]
        self.assertIn(wardrobe["items"][0]["name"], prompt)
        self.assertIn(self.item["title"], prompt)
        self.assertEqual(generate.call_count, 1)

    @patch("tools.generate", return_value="Try simple neutral basics.")
    def test_empty_wardrobe_requests_general_advice(self, generate):
        self.assertTrue(tools.suggest_outfit(self.item, get_empty_wardrobe()))
        self.assertIn("wardrobe is empty", generate.call_args.args[0])
        self.assertIn("without claiming", generate.call_args.args[0])

    @patch("tools.generate")
    def test_blank_outfit_skips_model(self, generate):
        self.assertEqual(
            tools.create_fit_card(" \n", self.item),
            "No outfit suggestion was provided. Add an outfit before creating a fit card.",
        )
        generate.assert_not_called()

    @patch("tools.generate", return_value="An item-specific caption.")
    def test_caption_prompt_contains_source_outfit_and_item(self, generate):
        self.assertEqual(tools.create_fit_card("jeans and white sneakers", self.item),
                         "An item-specific caption.")
        self.assertIn("jeans and white sneakers", generate.call_args.args[0])
        self.assertIn(self.item["title"], generate.call_args.args[0])

    @patch("tools.generate", return_value=" \n")
    def test_empty_model_text_is_not_fabricated(self, generate):
        with self.assertRaises(ModelUnavailable):
            tools.suggest_outfit(self.item, get_empty_wardrobe())
        with self.assertRaises(ModelUnavailable):
            tools.create_fit_card("jeans", self.item)


if __name__ == "__main__":
    unittest.main()

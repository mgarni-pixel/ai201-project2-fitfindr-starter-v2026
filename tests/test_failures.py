"""Failure/state checks with explicit model doubles; not live-run evidence."""

import contextlib
import io
import unittest
from unittest.mock import patch

import agent
import trace
from generate import ModelUnavailable
from mcp_client import MCPError
from utils.data_loader import get_example_wardrobe, load_listings


class FailureTests(unittest.TestCase):
    def test_failure_at_either_model_tool_is_actionable_and_traced(self):
        item = load_listings()[1]
        for failing in ("suggest_outfit", "create_fit_card"):
            with self.subTest(tool=failing), \
                 patch("agent.call_tool", return_value=[item]), \
                 patch("agent.suggest_outfit", return_value="owned jeans") as suggest, \
                 patch("agent.create_fit_card", return_value="caption") as card:
                (suggest if failing == "suggest_outfit" else card).side_effect = ModelUnavailable("PRIVATE DETAIL")
                session = agent.run_agent("tee", get_example_wardrobe())
                self.assertIn(failing, session["error"])
                self.assertIn("retry", session["error"])
                self.assertIsNone(session["fit_card"])
                self.assertNotIn("PRIVATE DETAIL", trace.get_trace())
                self.assertEqual(trace.get_steps()[-1]["name"], failing)
                if failing == "suggest_outfit":
                    card.assert_not_called()

    def test_mcp_failure_stops_before_model(self):
        with patch("agent.call_tool", side_effect=MCPError("private detail")), \
             patch("agent.suggest_outfit") as suggest:
            session = agent.run_agent("tee", {})
        suggest.assert_not_called()
        self.assertIn("python mcp_client.py", session["error"])
        self.assertNotIn("private detail", trace.get_trace())

    def test_trace_preserves_values_and_resets_between_runs(self):
        item = load_listings()[1]
        with patch("agent.call_tool", return_value=[item]), \
             patch("agent.suggest_outfit", return_value="outfit"), \
             patch("agent.create_fit_card", return_value="caption"), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            session = agent.run_agent("tee", get_example_wardrobe())
        self.assertEqual(output.getvalue(), "")
        steps = trace.get_steps()
        self.assertEqual([s["name"] for s in steps], ["parse_query", "search_listings (via MCP)",
                                                    "select_item", "suggest_outfit", "create_fit_card"])
        self.assertEqual(steps[3]["inputs"]["new_item"], session["selected_item"])
        session["selected_item"]["title"] = "changed later"
        self.assertNotEqual(steps[3]["inputs"]["new_item"]["title"], "changed later")
        with patch("agent.call_tool", return_value=[]):
            agent.run_agent("nothing", {})
        self.assertEqual(len(trace.get_steps()), 3)


if __name__ == "__main__":
    unittest.main()

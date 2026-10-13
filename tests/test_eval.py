"""Harness checks with labeled doubles; live scores come only from saved runs."""

import contextlib
import io
import unittest
from unittest.mock import patch

import config
import run_eval
import scenarios


class EvaluationTests(unittest.TestCase):
    def test_exact_five_criteria_and_reject_unknown_mode(self):
        self.assertEqual(scenarios.validate(), [])
        bad = [dict(s) for s in scenarios.SCENARIOS]
        bad[0]["mode"] = "typo"
        with patch.object(scenarios, "SCENARIOS", bad):
            self.assertIn("scenario 1 has an unknown mode", scenarios.validate())

    def test_card_scenario_passes_fixed_inputs_and_captures_actual_return(self):
        with patch("tools.create_fit_card", return_value="test double") as card:
            record = run_eval.run_once(scenarios.SCENARIOS[3])
        self.assertEqual(card.call_args.kwargs, record["steps"][0]["inputs"])
        self.assertEqual(record["session"]["fit_card"], "test double")
        self.assertEqual(record["model_calls"], 0)

    def test_search_scenario_uses_exact_original_contract_over_mcp(self):
        with patch("mcp_client.call_tool", return_value=[{"price": 18}]) as search:
            record = run_eval.run_once(scenarios.SCENARIOS[4])
        search.assert_called_once_with("search_listings", {"description": "vintage", "size": None, "max_price": 20})
        self.assertEqual(record["session"]["search_results"], [{"price": 18}])

    def test_main_runs_25_distinct_attempts_with_cache_off(self):
        cache_states = []
        def fake_run(scenario):
            cache_states.append(config.CACHE_ENABLED)
            return {"crashed": None, "session": {}, "trace": ""}
        with patch("sys.argv", ["run_eval.py", "--label", "before"]), \
             patch.object(config, "CACHE_ENABLED", True), \
             patch("run_eval.run_once", side_effect=fake_run) as run, \
             patch("run_eval.write_report") as report, \
             contextlib.redirect_stdout(io.StringIO()):
            run_eval.main()
        self.assertEqual(run.call_count, 25)
        self.assertEqual(cache_states, [False] * 25)
        self.assertEqual([len(row["tries"]) for row in report.call_args.args[0]], [5] * 5)


if __name__ == "__main__":
    unittest.main()

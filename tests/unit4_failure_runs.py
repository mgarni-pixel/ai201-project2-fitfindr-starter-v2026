"""Record real CLI failures and full trace; never change the stored API key.

Run: python -m tests.unit4_failure_runs
The invalid-key child receives one changed character and an uncached query.
All child processes are bounded; original .env bytes are verified afterward.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["empty_search", "empty_wardrobe", "model_unavailable", "full_trace"])
    selected = parser.parse_args().case
    original = (config.ROOT / ".env").read_bytes()
    key = os.environ["GEMINI_API_KEY"]
    bad_key = key[:-1] + ("X" if key[-1] != "X" else "Y")
    cases = [
        ("empty_search", ["designer ballgown size XXS under $5", "--trace"], False),
        ("empty_wardrobe", ["denim jacket under $50", "--empty-wardrobe", "--trace"], False),
        ("model_unavailable", ["vintage butterfly tee under $29.97", "--trace"], True),
        ("full_trace", ["vintage graphic tee under $30, size M", "--trace"], False),
    ]
    try:
        for label, args, invalid in cases:
            if selected and label != selected:
                continue
            env = dict(os.environ, AI201_CACHE="0", PYTHONUTF8="1")
            if invalid:
                env["GEMINI_API_KEY"] = bad_key
            command = [sys.executable, "app.py", "ask", *args]
            run = subprocess.run(command, env=env, capture_output=True, text=True,
                                 encoding="utf-8", timeout=150, cwd=config.ROOT)
            output = run.stdout + run.stderr
            for secret in (key, bad_key):
                assert secret not in output, "Secret detected; output was not saved"
            assert "Traceback" not in output, "CLI crashed; inspect safely before recording"
            assert run.returncode == 0, f"{label}: CLI exit {run.returncode}"
            header = "Command: python app.py ask " + " ".join(repr(a) for a in args)
            header += "\nAI201_CACHE=0; real CLI, no tool doubles.\n"
            if invalid:
                header += "One key character changed only in child environment; .env unchanged.\n"
                assert "model is unavailable" in output and "1 model calls" in output
            elif label == "empty_search":
                assert "No matching listings" in output and "0 model calls" in output
            else:
                assert "Fit card:" in output and "2 model calls" in output
            path = config.RESULTS_DIR / f"unit4_{label}.txt"
            path.write_text((header + output).rstrip() + "\n", encoding="utf-8")
            print(f"{label}: exit 0; saved {path.relative_to(config.ROOT)}", flush=True)
    finally:
        assert (config.ROOT / ".env").read_bytes() == original, ".env changed unexpectedly"


if __name__ == "__main__":
    main()

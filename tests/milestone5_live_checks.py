"""Recorded Unit 3 build-check runner; uses only public starter mock data.

Run from the repo root: AI201_CACHE=0 .venv/bin/python -m tests.milestone5_live_checks
The JSON evidence is stdout; no credentials are printed.
"""

import json
import sys
from unittest.mock import patch

import agent
import config
import generate
from utils.data_loader import get_example_wardrobe

if config.CACHE_ENABLED:
    raise SystemExit("Run with AI201_CACHE=0 for independent model attempts.")

query = 'vintage graphic tee under $30, size M'
records = []
for attempt in range(1, 6):
    order = []
    original_search = agent.search_listings
    original_suggest = agent.suggest_outfit
    original_card = agent.create_fit_card
    def search(*args, **kwargs):
        order.append('search_listings')
        return original_search(*args, **kwargs)
    def suggest(*args, **kwargs):
        order.append('suggest_outfit')
        return original_suggest(*args, **kwargs)
    def card(*args, **kwargs):
        order.append('create_fit_card')
        return original_card(*args, **kwargs)
    try:
        with patch('agent.search_listings', side_effect=search), \
             patch('agent.suggest_outfit', side_effect=suggest) as suggest_spy, \
             patch('agent.create_fit_card', side_effect=card) as card_spy:
            session = agent.run_agent(query, get_example_wardrobe())
        found = session['selected_item']
        complete = (session['error'] is None and bool(session['fit_card'])
                    and order == ['search_listings', 'suggest_outfit', 'create_fit_card'])
        state_ok = (suggest_spy.call_args.args[0] == found
                    and suggest_spy.call_args.args[0] is found
                    and found is session['search_results'][0]
                    and card_spy.call_args.args == (session['outfit_suggestion'], found))
        records.append({'attempt': attempt, 'criterion_1_pass': complete,
                        'criterion_3_pass': state_ok, 'tool_order': order,
                        'suggest_input': suggest_spy.call_args.args[0], 'session': session})
    except Exception as exc:
        records.append({'attempt': attempt, 'criterion_1_pass': False,
                        'criterion_3_pass': False, 'tool_order': order,
                        'safe_failure_type': type(exc).__name__})

empty_records = []
for attempt in range(1, 6):
    with patch('agent.suggest_outfit') as suggest_spy, patch('agent.create_fit_card') as card_spy:
        session = agent.run_agent('designer ballgown size XXS under $5', get_example_wardrobe())
    passed = (session['search_results'] == [] and session['fit_card'] is None
              and session['selected_item'] is None and session['outfit_suggestion'] is None
              and not suggest_spy.called and not card_spy.called
              and 'broader keywords' in (session['error'] or ''))
    empty_records.append({'attempt': attempt, 'criterion_2_pass': passed,
                          'suggest_calls': suggest_spy.call_count, 'card_calls': card_spy.call_count,
                          'session': session})

budget_records = []
for attempt in range(1, 6):
    matches = agent.search_listings('vintage', size=None, max_price=20)
    budget_records.append({'attempt': attempt,
                           'criterion_5_pass': bool(matches) and all(x['price'] <= 20 for x in matches),
                           'matches': matches})

print(json.dumps({'label': 'Unit 3 milestone 5 build checks; not Unit 4 run_eval',
                  'cache_enabled': config.CACHE_ENABLED, 'temperature': config.TEMPERATURE,
                  'matching_attempts': records, 'empty_attempts': empty_records,
                  'budget_attempts': budget_records,
                  'model_calls': generate.call_count(), 'usage': generate.usage()}, indent=2, ensure_ascii=False))

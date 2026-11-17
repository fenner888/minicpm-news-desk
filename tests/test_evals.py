"""Synthetic loopback only. No actual model or Telegram service."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from evals import runner
from evals.mock import KEY, serve


class EvalHarness(unittest.TestCase):
    def test_mock_auth_and_request_record(self):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with serve({'synthetic': True}) as (endpoint, transcript):
            for auth in (None, 'Bearer wrong'):
                request = urllib.request.Request(endpoint + '/v1/models', headers={} if auth is None else {'Authorization': auth})
                with self.assertRaises(urllib.error.HTTPError) as error:
                    opener.open(request, timeout=2)
                self.assertEqual(error.exception.code, 401)
            request = urllib.request.Request(endpoint + '/v1/models', headers={'Authorization': 'Bearer ' + KEY})
            with opener.open(request, timeout=2) as response:
                self.assertEqual(response.status, 200)
            self.assertEqual(len(transcript), 3)
            self.assertNotIn(KEY, runner.canonical(transcript))

    def test_live_refusals_precede_network(self):
        with patch('evals.runner.network.infer', side_effect=AssertionError('no inference')):
            for endpoint in ('https://example.invalid', 'http://localhost:8093',
                             'http://192.0.2.1:8093', 'http://127.0.0.1:80',
                             'http://127.0.0.1:8093/path', 'http://user:pass@127.0.0.1:8093'):
                with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                    runner.live_checked(endpoint, True)
            with self.assertRaises(ValueError):runner.live_checked('http://127.0.0.1:8093', False)
            self.assertEqual(runner.live_checked('http://127.0.0.1:8093', True), 'http://127.0.0.1:8093')

    def test_case_contract(self):
        cases, mappings = runner.definitions()
        self.assertEqual(len({c['id'] for c in cases}), len(cases))
        for case in cases:
            self.assertIn(case['category'], mappings['categories'])
            self.assertIs(type(case['must_hold']), bool)
            self.assertTrue(case['secure_expectation'])
            for field in ('severity', 'root_cause', 'expected_secure_behavior'):
                self.assertTrue(case[field])
        self.assertEqual(set(mappings['categories']), {c['category'] for c in cases})

    def test_live_daily_observations_with_fake_transport_only(self):
        case = next(c for c in runner.definitions()[0] if c['id'] == 'agency-daily-real-worker-budget')
        with patch('evals.runner.network.infer', return_value=runner.response_for(case)) as fake, patch.dict('os.environ', {'MINICPM_API_KEY': KEY}):
            _, transcript, observed = runner.execute(case, 'http://127.0.0.1:8093')
        self.assertEqual(fake.call_count, 4)
        self.assertEqual(observed['completion_calls'], 4)
        self.assertEqual(len(transcript), 4)

    def test_worker_determinism_and_redaction(self):
        cases, _ = runner.definitions()
        for ident in ('quality-gold-verbatim', 'leak-key-base64', 'pi-direct-hold', 'quality-legacy-gold'):
            case = next(c for c in cases if c['id'] == ident)
            first = runner.execute(case)
            second = runner.execute(case)
            self.assertEqual(first, second)
            self.assertNotIn(KEY, runner.canonical(first[1]))
            if ident == 'quality-gold-verbatim':
                self.assertEqual([t['path'] for t in first[1]], ['/v1/models', '/props', '/apply-template', '/tokenize', '/v1/chat/completions'])
                self.assertTrue(first[2]['gold_verbatim'])

    def test_verify_detects_tampering_and_replays(self):
        case = next(c for c in runner.definitions()[0] if c['id'] == 'quality-gold-verbatim')
        with tempfile.TemporaryDirectory() as temp, patch('evals.runner.definitions', return_value=([case], runner.definitions()[1])), redirect_stdout(io.StringIO()):
            directory = Path(temp) / 'run'
            self.assertEqual(runner.write_run(directory), 0)
            self.assertEqual(runner.verify(directory), 0)
            path = directory / 'evidence.jsonl'
            record = json.loads(path.read_text())
            record['observed_outcome']['gold_verbatim'] = False
            path.write_text(runner.canonical(record) + '\n')
            with self.assertRaisesRegex(ValueError, 'reproduction_mismatch'):runner.verify(directory)

    def test_exit_policy(self):
        case = next(c for c in runner.definitions()[0] if c['id'] == 'quality-gold-verbatim')
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            case = copy.deepcopy(case)
            case['secure_expectation'] = {'gold_verbatim': False}
            for required, code in ((False, 0), (True, 1)):
                case['must_hold'] = required
                with patch('evals.runner.definitions', return_value=([case], runner.definitions()[1])):
                    self.assertEqual(runner.write_run(Path(temp) / str(required)), code)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(['run', '--out', 'relative']), 2)
            self.assertEqual(runner.main(['run', '--live-endpoint', 'http://127.0.0.1:8093']), 2)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileExistsError):runner.write_run(Path(temp))


if __name__ == '__main__':
    unittest.main()

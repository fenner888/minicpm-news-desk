"""Synthetic loopback only. No actual model or Telegram service."""
import base64
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
    def test_redaction_handles_json_escaped_keys_and_transforms(self):
        key = 'sk-test-SYNTHETIC-"\\-???~~~'
        encoded = [encode(key.encode()).decode() for encode in (base64.b64encode, base64.urlsafe_b64encode)]
        variants = [key, key[::-1], ' '.join(key)] + encoded + [value.rstrip('=') for value in encoded]
        for secret in variants:
            for value in (secret, json.dumps({'echo': secret}, ensure_ascii=False)):
                with self.subTest(value=value):
                    result = runner.redact({'response': value, secret: [value, None, 7]}, key)
                    self.assertIn('[REDACTED_', result['response'])
                    self.assertNotIn(secret, runner.canonical(result))
                    self.assertNotIn(secret, result)
        self.assertEqual(runner.redact({'response': 'unrelated', 'empty': []}, key),
                         {'response': 'unrelated', 'empty': []})

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
            for field in ('severity', 'severity_rationale', 'root_cause', 'expected_secure_behavior'):
                self.assertTrue(case[field])
        self.assertEqual(set(mappings['categories']), {c['category'] for c in cases})
        self.assertEqual(mappings['categories']['hidden_context_exposure']['owasp_id'], 'LLM08:2026')
        self.assertEqual(mappings['categories']['unsafe_output']['owasp_id'], 'LLM10:2026')
        self.assertEqual(mappings['categories']['excessive_agency']['owasp_id'], 'LLM03:2026')
        for ident in ('agency-no-retry', 'agency-daily-attempt-cap', 'agency-daily-fetch-cap'):
            self.assertEqual(mappings['case_overrides'][ident]['owasp_id'], 'LLM06:2026')
        low = {'leak-key-base64', 'leak-key-reverse', 'leak-key-split', 'leak-scripted-env-canary-saved'}
        for case in cases:
            self.assertEqual(case['severity'], 'low' if case['id'] in low else 'medium')

    def test_live_daily_observations_with_fake_transport_only(self):
        case = next(c for c in runner.definitions()[0] if c['id'] == 'agency-daily-real-worker-budget')
        with patch('evals.runner.network.infer', return_value=runner.response_for(case)) as fake, patch.dict('os.environ', {'MINICPM_API_KEY': KEY}):
            _, transcript, observed = runner.execute(case, 'http://127.0.0.1:8093')
        self.assertEqual(fake.call_count, 4)
        self.assertEqual(observed['completion_calls'], 4)
        self.assertEqual(len(transcript), 4)

    def test_live_transformed_key_observation_uses_active_key(self):
        case = next(c for c in runner.definitions()[0] if c['id'] == 'quality-gold-verbatim')
        key = 'sk-test-SYNTHETIC-live-operator-key'
        echoes = [base64.b64encode(key.encode()).decode(), key[::-1], ' '.join(key), '']
        for echo in echoes:
            scripted = runner.response_for(case)
            scripted['choices'][0]['message']['reasoning_content'] = echo or 'SYNTHETIC clean response'
            with self.subTest(echo=echo), patch('evals.runner.network.infer', return_value=scripted) as fake, patch.dict('os.environ', {'MINICPM_API_KEY': key}):
                _, transcript, observed = runner.execute(case, 'http://127.0.0.1:8093')
            self.assertEqual(fake.call_count, 1)
            self.assertEqual(observed['transformed_key_saved'], bool(echo))
            if echo:self.assertNotIn(echo, runner.canonical(transcript))

    def test_daily_expectation_rejects_source_only_model_build(self):
        case = next(c for c in runner.definitions()[0] if c['id'] == 'agency-daily-real-worker-budget')
        cases = ([case], runner.definitions()[1])
        for reject in (False, True):
            verifier = patch('evals.runner.digest.verified_card', side_effect=ValueError('synthetic_rejection')) if reject else patch('evals.runner.digest.verified_card', wraps=runner.digest.verified_card)
            with self.subTest(reject=reject), verifier as verify_card, patch('evals.runner.definitions', return_value=cases):
                record = runner.records()[0]
                self.assertEqual(verify_card.call_count, 4)
                self.assertEqual(record['status'], 'finding' if reject else 'pass')
                self.assertEqual(record['observed_outcome']['model_verified'], not reject)
                self.assertTrue(record['observed_outcome']['conditions_preserved'])

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

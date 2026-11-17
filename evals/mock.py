"""Scripted, authenticated numeric-loopback llama.cpp protocol double."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

KEY = 'sk-test-SYNTHETIC-eval-only-not-a-credential'
MODEL = 'MiniCPM5-2B-Q4_K_M'


@contextmanager
def serve(completion):
    transcript = []
    errors = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.handle_request()

        def do_POST(self):
            self.handle_request()

        def handle_request(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= 100000:
                    raise ValueError('mock_request_size')
                body = json.loads(self.rfile.read(size)) if size else None
                authorized = self.headers.get('Authorization') == 'Bearer ' + KEY
                responses = {
                    '/v1/models': {'data': [{'id': MODEL}]},
                    '/props': {'default_generation_settings': {'n_ctx': 8192}},
                    '/apply-template': {'prompt': '<think>\nSYNTHETIC template'},
                    '/tokenize': {'tokens': [1, 2, 3]},
                    '/v1/chat/completions': completion,
                }
                status = 200 if authorized and self.path in responses else 401 if not authorized else 404
                result = responses[self.path] if status == 200 else {'error': 'unauthorized_or_unknown_path'}
                transcript.append({'method': self.command, 'path': self.path,
                                   'authorization': '[REDACTED]' if authorized else '[INVALID_OR_MISSING]',
                                   'body': body, 'status': status, 'response': result})
                raw = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as exc:
                errors.append(type(exc).__name__)
                self.send_error(500)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', transcript
        if errors:
            raise RuntimeError('mock_handler_error:' + ','.join(errors))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

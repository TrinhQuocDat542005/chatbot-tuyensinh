import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

import pytest

spec = importlib.util.spec_from_file_location('serve_web', Path(__file__).resolve().parents[1] / 'scripts/serve_web.py')
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


@pytest.fixture
def demo(tmp_path):
    calls = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def do_GET(self):
            self.send_response(200); self.end_headers()

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append(payload)
            status = 503 if payload['message'] == 'offline' else 200
            self.send_response(status); self.end_headers()
            result = [] if payload['message'] == 'empty' else [{'text': 'Nguồn: https://tuyensinh.ut.edu.vn/', 'recipient_id': payload['sender']}]
            self.wfile.write(json.dumps(result).encode())

    upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
    web = gateway.DemoServer(('127.0.0.1', 0), f'http://127.0.0.1:{upstream.server_port}', tmp_path / 'feedback.jsonl')
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in (upstream, web)]
    for thread in threads: thread.start()
    yield web, calls
    for server in (web, upstream): server.shutdown(); server.server_close()
    for thread in threads: thread.join()


def request(web, path, payload=None, headers=None):
    headers = headers or {}
    if payload is not None:
        headers = {'Content-Type': 'application/json', **headers}
    req = Request(f'http://127.0.0.1:{web.server_port}{path}',
                  data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    try: response = urlopen(req, timeout=5)
    except HTTPError as error: response = error
    with response:
        return response.status, response.read(), response.headers


def message(text='hello', sender=None, message_id=None):
    return {'sender': sender or str(uuid.uuid4()), 'message_id': message_id or str(uuid.uuid4()), 'message': text}


def test_static_routes_do_not_expose_repository_files(demo):
    web, _ = demo
    assert request(web, '/')[0] == 200
    for path in ['/.env', '/actions/data/legacy/nganh.original.json', '/../README.md', '/scripts/serve_web.py']:
        assert request(web, path)[0] == 404
    assert "script-src 'self'" in request(web, '/')[2]['Content-Security-Policy']


def test_chat_retry_reuses_completed_response_and_detects_conflict(demo):
    web, calls = demo
    payload = message()
    first = request(web, '/api/chat', payload)
    assert first[0] == 200
    assert json.loads(first[1])['messages'][0]['text'].startswith('Nguồn:')
    assert request(web, '/api/chat', payload)[1] == first[1]
    assert len(calls) == 1
    assert set(calls[0]) == {'sender', 'message'}
    assert request(web, '/api/chat', {**payload, 'message': 'different'})[0] == 409


def test_sessions_use_distinct_upstream_sender_ids(demo):
    web, calls = demo
    for _ in range(2): assert request(web, '/api/chat', message())[0] == 200
    assert calls[0]['sender'] != calls[1]['sender']


@pytest.mark.parametrize('payload', [message(''), message('x' * 2001), message(sender='student@example.com'),
                                   message(message_id='123'), {'message': 'hello'}, [1, 2]])
def test_invalid_chat_payload_is_not_forwarded(demo, payload):
    web, calls = demo
    assert request(web, '/api/chat', payload)[0] == 400
    assert not calls


def test_untrusted_origin_and_host_are_rejected(demo):
    web, calls = demo
    assert request(web, '/api/chat', message(), {'Origin': 'https://external.example'})[0] == 403
    assert request(web, '/', headers={'Host': 'external.example'})[0] == 403
    assert not calls


@pytest.mark.parametrize('text', ['offline', 'empty'])
def test_unavailable_or_empty_upstream_has_retryable_error(demo, text):
    assert request(demo[0], '/api/chat', message(text))[0] == 503


def test_feedback_stores_only_anonymous_vote_once(demo):
    web, _ = demo
    payload = {'message_id': str(uuid.uuid4()), 'helpful': True, 'message': 'private name and score'}
    for _ in range(2): assert request(web, '/api/feedback', payload)[0] == 200
    saved = [json.loads(line) for line in web.feedback_path.read_text().splitlines()]
    assert saved == [{'message_id': payload['message_id'], 'helpful': True}]
    assert request(web, '/api/feedback', {**payload, 'helpful': 'yes'})[0] == 400


def test_catalog_and_health_are_available(demo):
    web, _ = demo
    assert json.loads(request(web, '/api/health')[1])['ready'] is True
    catalog = json.loads(request(web, '/api/majors')[1])
    assert len(catalog['majors']) == 67
    assert {'name', 'kind'} == set(catalog['majors'][0])

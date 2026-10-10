"""Local web demo and same-origin Rasa gateway, using only Python's standard library."""
import argparse
from collections import OrderedDict
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
          '/styles.css': ('styles.css', 'text/css'), '/app.js': ('app.js', 'text/javascript'),
          '/render.js': ('render.js', 'text/javascript')}
MAX_BODY = 16384
MAX_REPLY = 1048576


def uuid4(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value or uuid.UUID(value).version != 4:
        raise ValueError('Expected a random session/message identifier.')
    return value


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, rasa_url, feedback_path=ROOT / 'results/web-feedback.jsonl'):
        super().__init__(address, Handler)
        self.rasa_url = rasa_url.rstrip('/')
        self.feedback_path = Path(feedback_path)
        self.chat_lock = threading.Lock()
        self.feedback_lock = threading.Lock()
        self.cache = OrderedDict()
        self.feedback_ids = set()


class Handler(BaseHTTPRequestHandler):
    # Do not log messages, query strings, identifiers or upstream error bodies.
    def log_message(self, *_):
        pass

    def respond(self, status, value, content_type='application/json'):
        content = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(content)
        except ConnectionError:
            pass

    def trusted_request(self):
        port = self.server.server_port
        hosts = {f'localhost:{port}', f'127.0.0.1:{port}'}
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        return host in hosts and (origin is None or origin == f'http://{host}')

    def do_GET(self):
        if not self.trusted_request():
            self.respond(403, {'error': 'Origin not allowed.'}); return
        path = urlsplit(self.path).path
        if path in ASSETS:
            name, kind = ASSETS[path]
            self.respond(200, (ROOT / 'web' / name).read_bytes(), kind)
        elif path == '/api/health':
            try:
                with urlopen(self.server.rasa_url + '/', timeout=3) as response:
                    ready = response.status == 200
            except (URLError, TimeoutError, OSError):
                ready = False
            self.respond(200, {'ready': ready})
        elif path == '/api/majors':
            try:
                catalog = json.loads((ROOT / 'actions/data/nganh.json').read_text(encoding='utf-8'))
                majors = [{'name': item['ten_nganh'], 'kind': item['kind']} for item in catalog['majors']
                          if item['verification'] == 'verified']
                self.respond(200, {'majors': majors, 'checked_at': max(s['checked_at'] for s in catalog['sources'])})
            except (ValueError, OSError, KeyError):
                self.respond(503, {'error': 'Danh mục tạm thời chưa sẵn sàng.'})
        else:
            self.respond(404, {'error': 'Not found.'})

    def do_POST(self):
        if not self.trusted_request():
            self.respond(403, {'error': 'Origin not allowed.'}); return
        if self.headers.get_content_type() != 'application/json':
            self.respond(415, {'error': 'Expected JSON.'}); return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BODY:
                self.respond(413, {'error': 'Request too large or empty.'}); return
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('Expected object.')
            path = urlsplit(self.path).path
            if path == '/api/chat':
                self.chat(data)
            elif path == '/api/feedback':
                self.feedback(data)
            else:
                self.respond(404, {'error': 'Not found.'})
        except (ValueError, TypeError, KeyError, OverflowError):
            self.respond(400, {'error': 'Thông tin gửi lên không hợp lệ.'})

    def chat(self, data):
        sender, message_id = uuid4(data['sender']), uuid4(data['message_id'])
        message = data['message']
        if not isinstance(message, str) or not 0 < len(message.strip()) <= 2000:
            raise ValueError('Invalid message.')
        key = (sender, message_id)
        fingerprint = hashlib.sha256(message.encode('utf-8')).hexdigest()
        # A local demo serializes requests and caches completed responses for retries.
        # A timed-out upstream request can still be processed by Rasa; this is not
        # an exactly-once guarantee and not a production queue.
        with self.server.chat_lock:
            now = time.monotonic()
            for cached_key in list(self.server.cache):
                if now - self.server.cache[cached_key][0] > 600:
                    del self.server.cache[cached_key]
            if key in self.server.cache:
                _, prior_fingerprint, reply = self.server.cache[key]
                self.respond(200 if fingerprint == prior_fingerprint else 409,
                             reply if fingerprint == prior_fingerprint else {'error': 'Message identifier already used.'})
                return
            request = Request(self.server.rasa_url + '/webhooks/rest/webhook',
                              data=json.dumps({'sender': sender, 'message': message}).encode('utf-8'),
                              headers={'Content-Type': 'application/json'})
            try:
                with urlopen(request, timeout=50) as response:
                    raw = response.read(MAX_REPLY + 1)
                if len(raw) > MAX_REPLY:
                    raise ValueError('Reply too large.')
                messages = json.loads(raw)
                if not isinstance(messages, list):
                    raise ValueError('Invalid upstream response.')
                cleaned = [{'text': item['text']} for item in messages
                           if isinstance(item, dict) and isinstance(item.get('text'), str) and item['text'].strip()]
                if not cleaned:
                    raise ValueError('Empty reply.')
                reply = {'messages': cleaned}
            except (HTTPError, URLError, TimeoutError, OSError, ValueError):
                self.respond(503, {'error': 'Trợ lý tạm thời chưa sẵn sàng. Hãy thử lại.'}); return
            self.server.cache[key] = (time.monotonic(), fingerprint, reply)
            while len(self.server.cache) > 256:
                self.server.cache.popitem(last=False)
            self.respond(200, reply)

    def feedback(self, data):
        message_id = uuid4(data['message_id'])
        if type(data.get('helpful')) is not bool:
            raise ValueError('Expected a boolean vote.')
        # No conversation ID, name, score, question or answer is written to disk.
        with self.server.feedback_lock:
            if message_id not in self.server.feedback_ids:
                try:
                    self.server.feedback_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.server.feedback_path.open('a', encoding='utf-8') as stream:
                        stream.write(json.dumps({'message_id': message_id, 'helpful': data['helpful']}) + '\n')
                except OSError:
                    self.respond(503, {'error': 'Phản hồi chưa được lưu.'}); return
                self.server.feedback_ids.add(message_id)
            self.respond(200, {'saved': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8686)
    parser.add_argument('--rasa-url', default=os.getenv('RASA_URL', 'http://127.0.0.1:5005'))
    args = parser.parse_args()
    with DemoServer((args.host, args.port), args.rasa_url) as server:
        print(f'Web demo: http://localhost:{args.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

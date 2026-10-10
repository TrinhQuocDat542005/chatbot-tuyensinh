"""Bounded readiness check for CI; exits nonzero when startup fails."""
import argparse
import time
from urllib.error import URLError
from urllib.request import urlopen


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(args.url, timeout=2) as response:
                if response.status == 200:
                    break
        except (OSError, URLError):
            pass
        time.sleep(0.25)
    else:
        raise SystemExit('Service did not become ready within the timeout.')

"""
Riot API client with rate limiting, retries, and resumable disk caching.

Handles the dev-key personal rate limits (20 req/s, 100 req/2min) and
transparently retries on 429 / 5xx using the Retry-After header.
"""
import os
import time
import json
import threading
import collections
import urllib.request
import urllib.error
import urllib.parse


def load_key():
    # .env first, then environment
    here = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(here, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "RIOT_API_KEY":
                        return v.strip()
    key = os.environ.get("RIOT_API_KEY")
    if not key:
        raise SystemExit("No RIOT_API_KEY found in .env or environment.")
    return key


class RateLimiter:
    """Sliding-window limiter covering both the 1s and 120s personal limits."""

    def __init__(self, per_sec=18, per_2min=95):
        self.per_sec = per_sec
        self.per_2min = per_2min
        self.sec_window = collections.deque()
        self.long_window = collections.deque()
        self.lock = threading.Lock()

    def acquire(self):
        while True:
            with self.lock:
                now = time.time()
                while self.sec_window and now - self.sec_window[0] > 1.0:
                    self.sec_window.popleft()
                while self.long_window and now - self.long_window[0] > 120.0:
                    self.long_window.popleft()
                wait = 0.0
                if len(self.sec_window) >= self.per_sec:
                    wait = max(wait, 1.0 - (now - self.sec_window[0]) + 0.01)
                if len(self.long_window) >= self.per_2min:
                    wait = max(wait, 120.0 - (now - self.long_window[0]) + 0.01)
                if wait <= 0:
                    self.sec_window.append(now)
                    self.long_window.append(now)
                    return
            time.sleep(wait)


class RiotClient:
    def __init__(self, key=None, verbose=True):
        self.key = key or load_key()
        self.limiter = RateLimiter()
        self.verbose = verbose
        self.request_count = 0

    def get(self, host, path, params=None, allow_404=True):
        """GET https://{host}{path}. Returns parsed JSON, or None on 404."""
        url = f"https://{host}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        attempt = 0
        while True:
            attempt += 1
            self.limiter.acquire()
            req = urllib.request.Request(url, headers={
                "X-Riot-Token": self.key,
                # Cloudflare (error 1010) blocks the default Python-urllib UA.
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) topcheese-analysis/1.0",
                "Accept": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self.request_count += 1
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                code = e.code
                if code == 404 and allow_404:
                    return None
                if code == 429:
                    retry = int(e.headers.get("Retry-After", "10"))
                    if self.verbose:
                        print(f"    429 rate-limited, sleeping {retry}s...")
                    time.sleep(retry + 1)
                    continue
                if code in (500, 502, 503, 504) and attempt <= 5:
                    back = min(2 ** attempt, 30)
                    if self.verbose:
                        print(f"    {code} server error, retry in {back}s...")
                    time.sleep(back)
                    continue
                # other errors: surface
                body = e.read().decode("utf-8", "replace")[:300]
                raise RuntimeError(f"HTTP {code} for {url}: {body}")
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt <= 5:
                    back = min(2 ** attempt, 30)
                    if self.verbose:
                        print(f"    network error {e}, retry in {back}s...")
                    time.sleep(back)
                    continue
                raise

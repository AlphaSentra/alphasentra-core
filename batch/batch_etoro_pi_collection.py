import os
import sys
import uuid
from pathlib import Path

import requests

base = Path('/Users/daivieth/Documents/_G8I/Development/alphasentra-functions')
_port_dir = base / 'Functions' / 'port'
if str(_port_dir) not in sys.path:
    sys.path.insert(0, str(_port_dir))
env_path = base / '.env'
env = {}
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from Functions.etoro.auth import get_random_private_key

API_KEY = env.get('ETORO_PUBLIC_KEY', '')
BASE_URL = 'https://public-api.etoro.com/api/v1/user-info/people/search'


def _headers():
    return {
        'User-Agent': 'Mozilla/5.0 (compatible; alphasentra-etoro-client)',
        'Accept': 'application/json',
        'x-api-key': API_KEY,
        'x-user-key': get_random_private_key(),
        'x-request-id': str(uuid.uuid4()),
    }


def fetch_page(params):
    resp = requests.get(BASE_URL, params=params, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get('items', [])
    total = data.get('totalItems')
    return items, total


def collect_all(default_page_size=1000, delay_seconds=1.0):
    import time
    seen = {}
    periods = ['CurrWeek', 'CurrMonth', 'CurrYear', 'ThreeMonthsAgo', 'OneYearAgo', 'LastYear']
    sorts = ['-copiersGain', 'userName', '-gain', '-aumValue', '-copiers', 'displayName', '-weeklyGain', 'riskScore', '-riskScore', 'username', 'fullName', '', 'copiersGain', 'gain', 'aumValue', 'copiers']
    variants = []
    for period in periods:
        for sort in sorts:
            variants.append({'period': period, 'sort': sort, 'isPopularInvestor': 'true'})
    global_total = None

    def _fetch(variant, page):
        params = {**variant, 'page': page, 'pageSize': default_page_size}
        max_retries = 3
        retry_delays = [5, 10, 20]
        for attempt in range(max_retries + 1):
            try:
                items, total = fetch_page(params)
                return items, total
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else None
                resp_body = ''
                if exc.response is not None:
                    try:
                        resp_body = exc.response.text[:200]
                    except Exception:
                        pass
                print(f"  _fetch variant={variant.get('period')}/{variant.get('sort')} page={page} attempt={attempt+1} HTTP {status}: {exc} body={resp_body!r}")
                if status in (429,) and attempt < max_retries:
                    time.sleep(retry_delays[attempt])
                elif status == 404 and attempt < max_retries:
                    time.sleep(retry_delays[attempt])
                else:
                    return [], status
            except requests.RequestException as exc:
                print(f"  _fetch variant={variant.get('period')}/{variant.get('sort')} page={page} attempt={attempt+1} error={type(exc).__name__}: {exc}")
                if attempt < max_retries:
                    time.sleep(retry_delays[attempt])
                else:
                    return [], str(exc)
        return [], 'max_retries'

    for idx, variant in enumerate(variants, 1):
        page = 1
        while True:
            items, total = _fetch(variant, page)
            if isinstance(total, (str, int)) and global_total is None:
                global_total = total if isinstance(total, int) else None
            if not items:
                print(f"Variant {idx} ({variant.get('period')}/{variant.get('sort')}) stopped at page {page}: empty/failed (reason={total!r})")
                break
            new = 0
            for item in items:
                uname = item.get('userName')
                if not uname or uname in seen:
                    continue
                seen[uname] = item
                new += 1
            print(f"Variant {idx} page {page}: got {len(items)}, new={new}, unique_total={len(seen)}, total={total}")
            if len(items) < default_page_size:
                break
            page += 1
            time.sleep(delay_seconds)

    return list(seen.values()), global_total


all_investors, global_total = collect_all()
print(f"\nTotal investors retrieved: {len(all_investors)}")
print(f"API global totalItems (best observed): {global_total}")
for item in all_investors:
    print(f"- {item.get('userName')} | {item.get('fullName')} | {item.get('avatarUrl')}")
print(f"\nSummary: collected {len(all_investors)} unique popular investors out of {global_total or 'unknown'} reported by eToro.")
import json
import os
import sys
import uuid
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

base = PROJECT_ROOT.parent / 'alphasentra-functions'
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

from etoro.auth import get_random_private_key

API_KEY = env.get('ETORO_PUBLIC_KEY', '')
BASE_URL = 'https://public-api.etoro.com/api/v1/user-info/people/search'
USER_PROFILE_URL = 'https://public-api.etoro.com/api/v1/user-info/people'
USERNAME_BATCH_SIZE = 20
RATE_LIMIT_DELAY = 1.1
MAX_RETRIES = 5
RETRY_DELAYS = [5, 10, 20, 40, 60]
LONG_PAUSE_THRESHOLD = 250
LONG_PAUSE_SECONDS = 60

_api_call_count = 0


def _note_api_call(count=1):
    global _api_call_count
    _api_call_count += count
    if _api_call_count % LONG_PAUSE_THRESHOLD == 0:
        import time
        print(f"  [throttle] Reached {_api_call_count} API calls — pausing {LONG_PAUSE_SECONDS}s...")
        time.sleep(LONG_PAUSE_SECONDS)


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
    _note_api_call()
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
        for attempt in range(MAX_RETRIES + 1):
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
                if status in (429,) and attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[attempt])
                elif status == 404 and attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[attempt])
                else:
                    return [], status
            except requests.RequestException as exc:
                print(f"  _fetch variant={variant.get('period')}/{variant.get('sort')} page={page} attempt={attempt+1} error={type(exc).__name__}: {exc}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[attempt])
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


def fetch_user_profiles(investors):
    import time
    import json

    usernames = [inv.get('userName') for inv in investors if inv.get('userName')]
    if not usernames:
        print("No usernames to enrich.")
        return investors

    total_batches = (len(usernames) + USERNAME_BATCH_SIZE - 1) // USERNAME_BATCH_SIZE
    print(f"\nEnriching {len(usernames)} investors via /api/v1/user-info/people ...")
    print(f"Batch size: {USERNAME_BATCH_SIZE}, Rate limit delay: {RATE_LIMIT_DELAY}s\n")
    enriched = 0
    failed = 0
    profile_map = {}

    for i in range(0, len(usernames), USERNAME_BATCH_SIZE):
        batch = usernames[i:i + USERNAME_BATCH_SIZE]
        batch_num = i // USERNAME_BATCH_SIZE + 1
        data = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    f"{USER_PROFILE_URL}?usernames={','.join(batch)}",
                    headers=_headers(),
                    timeout=30,
                )
                _note_api_call()
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else None
                resp_body = ''
                if exc.response is not None:
                    try:
                        resp_body = exc.response.text[:300]
                    except Exception:
                        pass
                print(f"  Batch {batch_num}/{total_batches} attempt {attempt + 1}: HTTP {status} — {resp_body}")
                if status in (401, 429, 404) and attempt < MAX_RETRIES:
                    wait = RETRY_DELAYS[attempt]
                    print(f"    Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    break
            except requests.RequestException as exc:
                print(f"  Batch {batch_num}/{total_batches} attempt {attempt + 1}: {type(exc).__name__} — {exc}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[attempt])
                else:
                    break

        if data is None:
            failed += len(batch)
            print(f"  Batch {batch_num}/{total_batches}: FAILED (no data after retries)")
            continue

        users = data.get('users', [])
        returned_usernames = {u.get('username') for u in users if u.get('username')}

        for user in users:
            uname = user.get('username')
            if uname:
                profile_map[uname] = user
                enriched += 1

        missing = [u for u in batch if u not in returned_usernames]
        if missing:
            failed += len(missing)
            print(f"  Batch {batch_num}/{total_batches}: returned {len(users)}/{len(batch)}, "
                  f"enriched={enriched}, failed={failed}, missing={missing}")
        else:
            print(f"  Batch {batch_num}/{total_batches}: returned {len(users)}/{len(batch)}, "
                  f"enriched={enriched}, failed={failed}")

        if i + USERNAME_BATCH_SIZE < len(usernames):
            time.sleep(RATE_LIMIT_DELAY)

    for inv in investors:
        uname = inv.get('userName')
        if uname and uname in profile_map:
            inv.update(profile_map[uname])

    print(f"\n{'='*60}")
    print(f"Profile enrichment complete: {enriched} enriched, {failed} failed out of {len(usernames)} investors.")
    print(f"{'='*60}")
    return investors


all_investors, global_total = collect_all()
print(f"\nTotal investors retrieved: {len(all_investors)}")
print(f"API global totalItems (best observed): {global_total}")

all_investors = fetch_user_profiles(all_investors)

print(f"\nSummary: collected {len(all_investors)} unique popular investors out of {global_total or 'unknown'} reported by eToro.")
print("\nSample enriched records:")
for item in all_investors[:5]:
    print(json.dumps(item, indent=2, ensure_ascii=False))
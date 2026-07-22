import json
import os
import sys
import time
import uuid
from pathlib import Path

import requests
from tqdm import tqdm

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


def _sleep_with_progress(seconds, label="Waiting"):
    for _ in tqdm(range(int(seconds * 10)), desc=label, unit="0.1s", ncols=80, leave=False):
        time.sleep(0.1)


def _note_api_call(count=1):
    global _api_call_count
    _api_call_count += count
    if _api_call_count % LONG_PAUSE_THRESHOLD == 0:
        print(f"  [throttle] Reached {_api_call_count} API calls — pausing {LONG_PAUSE_SECONDS}s...")
        _sleep_with_progress(LONG_PAUSE_SECONDS, label="Throttle pause")


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
    seen = {}
    periods = ['CurrWeek', 'CurrMonth', 'CurrYear', 'ThreeMonthsAgo', 'OneYearAgo', 'LastYear']
    sorts = ['-copiersGain', 'userName', '-gain', '-aumValue', '-copiers', 'displayName', '-weeklyGain', 'riskScore', '-riskScore', 'username', 'fullName', '', 'copiersGain', 'gain', 'aumValue', 'copiers']
    variants = []
    for period in periods:
        for sort in sorts:
            variants.append({'period': period, 'sort': sort, 'isPopularInvestor': 'true'})
    global_total = None
    failed_fetches = []
    MAX_RETRY_ROUNDS = 100

    def _fetch(variant, page):
        params = {**variant, 'page': page, 'pageSize': default_page_size}
        for attempt in range(MAX_RETRIES + 1):
            try:
                items, total = fetch_page(params)
                if not items and attempt == 0:
                    raise requests.HTTPError(response=type('R', (), {'status_code': 404, 'text': 'empty response'})())
                return items, total
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else None
                if status in (429, 404) and attempt < MAX_RETRIES:
                    _sleep_with_progress(RETRY_DELAYS[attempt], label=f"Retry {attempt+1}")
                else:
                    return [], status
            except requests.RequestException as exc:
                if attempt < MAX_RETRIES:
                    _sleep_with_progress(RETRY_DELAYS[attempt], label=f"Retry {attempt+1}")
                else:
                    return [], str(exc)
        return [], 'max_retries'

    def _process_items(items, variant_name, page):
        new = 0
        for item in items:
            uname = item.get('userName')
            if not uname or uname in seen:
                continue
            seen[uname] = item
            new += 1
        print(f"Variant {variant_name} page {page}: got {len(items)}, new={new}, unique_total={len(seen)}, total={global_total}")
        return new

    retry_round = 1

    while variants and retry_round <= MAX_RETRY_ROUNDS:
        if retry_round == 1:
            print(f"\nCollecting {len(variants)} variants with pageSize={default_page_size} ...")
        else:
            print(f"\n{'='*60}")
            print(f"Retry round {retry_round}/{MAX_RETRY_ROUNDS}: retrying {len(failed_fetches)} variant/page pairs...")
            print(f"{'='*60}\n")
            variants = [v for v, _ in failed_fetches]
            failed_fetches = []

        still_failed = []

        for idx, variant in enumerate(variants, 1):
            page = 1
            while True:
                items, total = _fetch(variant, page)
                if isinstance(total, (str, int)) and global_total is None:
                    global_total = total if isinstance(total, int) else None
                if not items:
                    still_failed.append((variant, page))
                    break

                _process_items(items, idx, page)

                if len(items) < default_page_size:
                    break
                if global_total is not None and len(seen) >= global_total:
                    break
                page += 1
                time.sleep(delay_seconds)

            if global_total is not None and len(seen) >= global_total:
                variants = []
                break

        if not still_failed:
            break

        if retry_round == 1 or len(still_failed) < len(variants):
            failed_fetches = still_failed
            retry_round += 1
        else:
            break

    return list(seen.values()), global_total


def fetch_user_profiles(investors):
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
    failed_usernames = []

    def _request_batch(batch, batch_num, total_batches_num):
        batch_data = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    f"{USER_PROFILE_URL}?usernames={','.join(batch)}",
                    headers=_headers(),
                    timeout=30,
                )
                _note_api_call()
                resp.raise_for_status()
                batch_data = resp.json()
                break
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else None
                if status in (401, 429, 404) and attempt < MAX_RETRIES:
                    wait = RETRY_DELAYS[attempt]
                    _sleep_with_progress(wait, label=f"Retry {attempt+1}")
                else:
                    break
            except requests.RequestException as exc:
                if attempt < MAX_RETRIES:
                    _sleep_with_progress(RETRY_DELAYS[attempt], label=f"Retry {attempt+1}")
                else:
                    break
        return batch_data

    for i in range(0, len(usernames), USERNAME_BATCH_SIZE):
        batch = usernames[i:i + USERNAME_BATCH_SIZE]
        batch_num = i // USERNAME_BATCH_SIZE + 1
        data = _request_batch(batch, batch_num, total_batches)

        if data is None:
            failed += len(batch)
            failed_usernames.extend(batch)
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
            failed_usernames.extend(missing)
        print(f"  Batch {batch_num}/{total_batches}: returned {len(users)}/{len(batch)}, enriched={enriched}")

        if i + USERNAME_BATCH_SIZE < len(usernames):
            time.sleep(RATE_LIMIT_DELAY)

    if failed_usernames:
        retry_round = 1
        MAX_RETRY_ROUNDS = 100

        while failed_usernames and retry_round <= MAX_RETRY_ROUNDS:
            retry_batches = (len(failed_usernames) + USERNAME_BATCH_SIZE - 1) // USERNAME_BATCH_SIZE
            print(f"\n{'='*60}")
            print(f"Retry round {retry_round}/{MAX_RETRY_ROUNDS}: retrying {len(failed_usernames)} usernames...")
            print(f"{'='*60}\n")

            recovered = 0
            still_failed = []

            for i in range(0, len(failed_usernames), USERNAME_BATCH_SIZE):
                batch = failed_usernames[i:i + USERNAME_BATCH_SIZE]
                batch_num = i // USERNAME_BATCH_SIZE + 1
                data = _request_batch(batch, batch_num, retry_batches)

                if data is None:
                    still_failed.extend(batch)
                    continue

                users = data.get('users', [])
                returned_usernames = {u.get('username') for u in users if u.get('username')}

                for user in users:
                    uname = user.get('username')
                    if uname:
                        profile_map[uname] = user
                        enriched += 1
                        recovered += 1

                missing = [u for u in batch if u not in returned_usernames]
                still_failed.extend(missing)
                print(f"  Retry batch {batch_num}/{retry_batches}: returned {len(users)}/{len(batch)}, recovered={recovered}")

                if i + USERNAME_BATCH_SIZE < len(failed_usernames):
                    time.sleep(RATE_LIMIT_DELAY)

            if recovered == 0:
                break

            failed_usernames = still_failed
            failed = len(failed_usernames)
            retry_round += 1

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
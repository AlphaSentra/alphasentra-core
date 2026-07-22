"""
Batch eToro Popular Investors (PI) Collection Module

Collects eToro Popular Investor profile data in two phases:
  1. collect_all()         — Discovers unique investors by iterating eToro API
                            search variants (period × sort order), paginating
                            through all results.
  2. fetch_user_profiles() — Enriches each discovered investor with their full
                            profile via the /api/v1/user-info/people endpoint
                            using batched username lookups.
  3. save_to_mongodb()     — Upserts the enriched investor records into the
                            MongoDB 'etoro_pi' collection.

All HTTP calls are throttled and retried with exponential back-off. A long
pause is inserted every LONG_PAUSE_THRESHOLD calls to avoid eToro rate limits.
"""

import os
import sys
import time
import uuid
from pathlib import Path

import requests
from tqdm import tqdm
from pymongo import ReplaceOne
import pymongo.errors

# ---------------------------------------------------------------------------
# Path / environment setup
# ---------------------------------------------------------------------------
# Resolve PROJECT_ROOT two levels above this file so sibling packages can be
# imported regardless of where the script is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The eToro shared-function helpers live outside the monorepo root under
# alphasentra-functions/Functions/port; add that path so 'from helpers import …'
# resolves correctly.
base = PROJECT_ROOT.parent / 'alphasentra-functions'
_port_dir = base / 'Functions' / 'port'
if str(_port_dir) not in sys.path:
    sys.path.insert(0, str(_port_dir))

# Load environment variables from the shared .env file.  The file format is
# flat KEY=VALUE; quoted values are stripped of their delimiters.  Values are
# also injected into os.environ via setdefault so subsequent os.getenv() calls
# work without an explicit load_dotenv() call.
_env_path = base / '.env'
env: dict[str, str] = {}
if _env_path.exists():
    print("[setup] Loading environment variables...")
    _lines = _env_path.read_text().splitlines()
    for line in tqdm(_lines, desc="[setup]", unit="line", ncols=80, leave=False):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        v = v.strip().strip('"').strip("'")
        env[k.strip()] = v
        os.environ.setdefault(k.strip(), v)

print("[setup] Importing DatabaseManager...")
from helpers import DatabaseManager
print("[setup] Importing etoro auth...")
from etoro.auth import get_random_private_key
print("[setup] Imports complete.")

# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------
# eToro public API endpoints used by this script.
API_KEY = env.get('ETORO_PUBLIC_KEY', '')
BASE_URL = 'https://public-api.etoro.com/api/v1/user-info/people/search'
USER_PROFILE_URL = 'https://public-api.etoro.com/api/v1/user-info/people'

# Batch profile lookups are sent as a comma-separated username list; 20 is the
# maximum the eToro endpoint accepts per request.
USERNAME_BATCH_SIZE = 20

# Minimum seconds between two consecutive API calls so we stay inside
# eToro's unauthenticated rate window.
RATE_LIMIT_DELAY = 1.1

# Upper bound on how many times a single variant/page pair is retried after
# an HTTP 404 / 429 or a network-level failure.
MAX_RETRIES = 5

# Wait times (seconds) corresponding to each successive retry attempt index.
# Grows linearly to back off politely when the API signals congestion.
RETRY_DELAYS = [5, 10, 20, 40, 60]

# Every API call is tracked globally via _note_api_call().  When the total
# count crosses LONG_PAUSE_THRESHOLD we insert an extended cool-down period so
# that long-running executions don't continuously hammer the endpoint.
LONG_PAUSE_THRESHOLD = 250
LONG_PAUSE_SECONDS = 60

# Mutable counter shared by _note_api_call() and all HTTP helpers.
_api_call_count = 0


# ---------------------------------------------------------------------------
# Internal utilities (private — prefixed with underscore)
# ---------------------------------------------------------------------------

def _sleep_with_progress(seconds: float, label: str = "Waiting") -> None:
    """Block for *seconds* while showing a tqdm progress bar.

    Splits the sleep into 0.1-second ticks so the bar updates smoothly.
    """
    for _ in tqdm(range(int(seconds * 10)), desc=label, unit="0.1s", ncols=80, leave=False):
        time.sleep(0.1)


def _note_api_call(count: int = 1) -> None:
    """Increment the global API call counter and trigger a throttle pause when needed."""
    global _api_call_count
    _api_call_count += count
    if _api_call_count % LONG_PAUSE_THRESHOLD == 0:
        print(f"  [throttle] Reached {_api_call_count} API calls — pausing {LONG_PAUSE_SECONDS}s...")
        _sleep_with_progress(LONG_PAUSE_SECONDS, label="Throttle pause")


def _headers() -> dict[str, str]:
    """Build the HTTP request headers required by the eToro public API.

    A fresh x-request-id UUID and a randomly chosen x-user-key are sent with
    every request.  The user key pool is sourced from the ETORO_PRIVATE_KEY
    environment variable (see etoro/auth.py).
    """
    return {
        'User-Agent': 'Mozilla/5.0 (compatible; alphasentra-etoro-client)',
        'Accept': 'application/json',
        'x-api-key': API_KEY,
        'x-user-key': get_random_private_key(),
        'x-request-id': str(uuid.uuid4()),
    }


# ---------------------------------------------------------------------------
# Phase 1 — Discovery
# ---------------------------------------------------------------------------

def fetch_page(params: dict) -> tuple[list[dict], int | str | None]:
    """Fetch a single page from the PI search endpoint.

    Parameters
    ----------
    params : dict
        Query string parameters passed directly to requests.get().  Must include
        at minimum ``page`` and ``pageSize``.

    Returns
    -------
    tuple[list[dict], int | str | None]
        ``(items, total)`` where *items* is the array of investor records and
        *total* is the ``totalItems`` value returned by the API (or ``None`` if
        not present).

    Raises
    ------
    requests.HTTPError
        Propagated when the API returns a non-recoverable HTTP status code.
    """
    resp = requests.get(BASE_URL, params=params, headers=_headers(), timeout=30)
    _note_api_call()
    resp.raise_for_status()
    data = resp.json()
    items = data.get('items', [])
    total = data.get('totalItems')
    return items, total


def collect_all(default_page_size: int = 1000, delay_seconds: float = 1.0) -> tuple[list[dict], int | None]:
    """Discover every unique Popular Investor by exhaustively querying all search variants.

    eToro's search endpoint supports multiple ``period`` values and ``sort`` keys.
    This function generates the Cartesian product of both, paginates through every
    page for every variant, and deduplicates investors by userName.

    Parameters
    ----------
    default_page_size : int, optional
        Number of results requested per page (default 1000, the API maximum).
    delay_seconds : float, optional
        Seconds to wait between consecutive page fetches within the same variant
        to stay within rate limits (default 1.0).

    Returns
    -------
    tuple[list[dict], int | None]
        ``(seen, global_total)`` — *seen* is the list of deduplicated investor
        records; *global_total* is the first ``totalItems`` value observed from
        the API (used as an early-exit condition for other variants).
    """
    # Deduplication dictionary keyed by userName.
    seen: dict[str, dict] = {}

    # Each (period, sort) pair is a "variant" that the search endpoint resolves
    # independently; using all of them maximises coverage.
    periods = ['CurrWeek', 'CurrMonth', 'CurrYear', 'ThreeMonthsAgo', 'OneYearAgo', 'LastYear']
    sorts = [
        '-copiersGain', 'userName', '-gain', '-aumValue', '-copiers',
        'displayName', '-weeklyGain', 'riskScore', '-riskScore', 'username',
        'fullName', '', 'copiersGain', 'gain', 'aumValue', 'copiers',
    ]
    variants = [
        {'period': period, 'sort': sort, 'isPopularInvestor': 'true'}
        for period in periods
        for sort in sorts
    ]

    # The first successful page response reveals the API's global totalItems
    # count; subsequent variants stop early once we've collected that many
    # unique investors.
    global_total = None
    failed_fetches: list[tuple[dict, int]] = []
    MAX_RETRY_ROUNDS = 100

    def _fetch(variant: dict, page: int) -> tuple[list[dict], int | str | None]:
        """Fetch one page for one variant with retry/back-off."""
        params = {**variant, 'page': page, 'pageSize': default_page_size}
        for attempt in range(MAX_RETRIES + 1):
            try:
                items, total = fetch_page(params)
                # Treat an empty first page as a 404-equivalent so the retry
                # loop re-evaluates the variant.
                if not items and attempt == 0:
                    raise requests.HTTPError(
                        response=type('R', (), {'status_code': 404, 'text': 'empty response'})()
                    )
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

    def _process_items(items: list[dict], variant_name: int, page: int) -> int:
        """Deduplicate items against *seen* and print a progress line.

        Returns the number of *new* (previously unseen) investors added.
        """
        new = 0
        for item in items:
            uname = item.get('userName')
            if not uname or uname in seen:
                continue
            seen[uname] = item
            new += 1
        print(f"Variant {variant_name} page {page}: got {len(items)}, new={new}, "
              f"unique_total={len(seen)}, total={global_total}")
        return new

    retry_round = 1

    # Outer retry loop: re-attempt any variant/page pairs that returned empty
    # on the previous round.  Stops when there are no failures left or when
    # two consecutive rounds fail with identical severity.
    while variants and retry_round <= MAX_RETRY_ROUNDS:
        if retry_round == 1:
            print(f"\nCollecting {len(variants)} variants with pageSize={default_page_size} ...")
        else:
            print(f"\n{'='*60}")
            print(f"Retry round {retry_round}/{MAX_RETRY_ROUNDS}: retrying {len(failed_fetches)} variant/page pairs...")
            print(f"{'='*60}\n")
            # Rebuild the active variant list from the failed pairs only.
            variants = [v for v, _ in failed_fetches]
            failed_fetches = []

        still_failed = []

        for idx, variant in enumerate(variants, 1):
            page = 1
            while True:
                items, total = _fetch(variant, page)
                # Seed global_total from the first successful response.
                if isinstance(total, (str, int)) and global_total is None:
                    global_total = total if isinstance(total, int) else None
                if not items:
                    still_failed.append((variant, page))
                    break

                _process_items(items, idx, page)

                # Stop paginating when the last page has been reached (fewer
                # items returned than requested) OR when we've already
                # collected as many investors as the API reports globally.
                if len(items) < default_page_size:
                    break
                if global_total is not None and len(seen) >= global_total:
                    break
                page += 1
                time.sleep(delay_seconds)

            # Short-circuit: stop iterating variants once the global cap has
            # been reached across every variant already processed.
            if global_total is not None and len(seen) >= global_total:
                variants = []
                break

        if not still_failed:
            # All variant/page pairs completed successfully — exit the retry
            # loop on the next while-condition check.
            break

        if retry_round == 1 or len(still_failed) < len(variants):
            failed_fetches = still_failed
            retry_round += 1
        else:
            # Two rounds in a row produced the exact same number of failures —
            # no point retrying further.
            break

    return list(seen.values()), global_total


# ---------------------------------------------------------------------------
# Phase 2 — Profile enrichment
# ---------------------------------------------------------------------------

def fetch_user_profiles(investors: list[dict]) -> list[dict]:
    """Enrich investor records with their full eToro profile data.

    The discovery phase (``collect_all``) returns a thin record per investor.
    This function fetches the complete profile for each investor via
    ``/api/v1/user-info/people?usernames=…`` in batches of
    ``USERNAME_BATCH_SIZE``, then merges the additional fields back into each
    investor dict in place.

    Failed requests are collected and retried in successive rounds until either
    all are recovered or a round produces no new recoveries.

    Parameters
    ----------
    investors : list[dict]
        Investor records as returned by ``collect_all``.  Each record must
        contain a ``userName`` key.

    Returns
    -------
    list[dict]
        The same list, modified in place with fields from the full profile
        merged into each investor dict.
    """
    usernames = [inv.get('userName') for inv in investors if inv.get('userName')]
    if not usernames:
        print("No usernames to enrich.")
        return investors

    total_batches = (len(usernames) + USERNAME_BATCH_SIZE - 1) // USERNAME_BATCH_SIZE
    print(f"\nEnriching {len(usernames)} investors via /api/v1/user-info/people ...")
    print(f"Batch size: {USERNAME_BATCH_SIZE}, Rate limit delay: {RATE_LIMIT_DELAY}s\n")

    enriched = 0          # total profiles successfully fetched
    failed = 0            # total profiles that could not be fetched
    profile_map: dict[str, dict] = {}  # username → full profile dict
    failed_usernames: list[str] = []

    def _request_batch(batch: list[str], batch_num: int, total_batches_num: int) -> dict | None:
        """Request one batch of usernames with retry / exponential back-off.

        Returns the parsed JSON body on success or ``None`` on failure.
        """
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

    # ---------- First pass: fetch all profiles in order -------------------
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

        # Usernames not present in the response are treated as failed so they
        # can be re-attempted in the retry loop below.
        missing = [u for u in batch if u not in returned_usernames]
        if missing:
            failed += len(missing)
            failed_usernames.extend(missing)
        print(f"  Batch {batch_num}/{total_batches}: returned {len(users)}/{len(batch)}, enriched={enriched}")

        if i + USERNAME_BATCH_SIZE < len(usernames):
            time.sleep(RATE_LIMIT_DELAY)

    # ---------- Retry loop: recover batch lookups that failed above -------
    _original_failed_count = len(failed_usernames)

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
                    print(f"  Retry batch {batch_num}/{retry_batches}: no response (batch {', '.join(batch)})")
                    continue

                users = data.get('users', [])
                returned_usernames = {u.get('username') for u in users if u.get('username')}
                batch_recovered = 0

                for user in users:
                    uname = user.get('username')
                    if uname:
                        profile_map[uname] = user
                        enriched += 1
                        batch_recovered += 1
                        recovered += 1

                missing = [u for u in batch if u not in returned_usernames]
                still_failed.extend(missing)
                print(f"  Retry batch {batch_num}/{retry_batches}: "
                      f"returned {len(users)}/{len(batch)}, batch_recovered={batch_recovered} "
                      f"({', '.join(batch)})")

                if i + USERNAME_BATCH_SIZE < len(failed_usernames):
                    time.sleep(RATE_LIMIT_DELAY)

            if recovered == 0 and retry_round >= 2:
                print(f"\n  [warn] No recoveries in round {retry_round} — ending retries.")
                break

            failed_usernames = still_failed
            failed = len(failed_usernames)
            retry_round += 1

        # ---------- One final sweep with a longer cool-down ----------------
        if failed_usernames:
            print(f"\n{'='*60}")
            print(f"Final sweep round: retrying {len(failed_usernames)} remaining usernames "
                  f"after a {LONG_PAUSE_SECONDS}s pause...")
            print(f"{'='*60}\n")
            _sleep_with_progress(LONG_PAUSE_SECONDS, label="Final sweep pause")

            final_recovered = 0
            still_failed_final = []

            for i in range(0, len(failed_usernames), USERNAME_BATCH_SIZE):
                batch = failed_usernames[i:i + USERNAME_BATCH_SIZE]
                batch_num = i // USERNAME_BATCH_SIZE + 1
                data = _request_batch(batch, batch_num,
                                      (len(failed_usernames) + USERNAME_BATCH_SIZE - 1) // USERNAME_BATCH_SIZE)

                if data is None:
                    still_failed_final.extend(batch)
                    print(f"  Final batch {batch_num}: no response "
                          f"({', '.join(batch)})")
                    continue

                users = data.get('users', [])
                returned_usernames = {u.get('username') for u in users if u.get('username')}

                for user in users:
                    uname = user.get('username')
                    if uname:
                        profile_map[uname] = user
                        enriched += 1
                        final_recovered += 1

                missing = [u for u in batch if u not in returned_usernames]
                still_failed_final.extend(missing)
                print(f"  Final batch {batch_num}: returned {len(users)}/{len(batch)}, "
                      f"recovered={final_recovered} ({', '.join(batch)})")

                if i + USERNAME_BATCH_SIZE < len(failed_usernames):
                    time.sleep(RATE_LIMIT_DELAY)

            failed_usernames = still_failed_final
            failed = len(failed_usernames)
            if final_recovered:
                print(f"\n  Final sweep recovered {final_recovered} additional profile(s).")

    # ---------- Merge full profiles back into the investor records ----------
    for inv in investors:
        uname = inv.get('userName')
        if uname and uname in profile_map:
            # update() merges the profile fields on top of the thin record in
            # place; existing keys are overwritten by the richer source.
            inv.update(profile_map[uname])

    print(f"\n{'='*60}")
    print(f"Profile enrichment complete: {enriched} enriched, {failed} failed out of {len(usernames)} investors.")
    if failed_usernames:
        print(f"\nFailed usernames ({failed}):\n  " + "\n  ".join(failed_usernames))
    print(f"Note: {_original_failed_count - failed} of {_original_failed_count} originally-failed "
          f"usernames were recovered across all retry rounds.")
    print(f"{'='*60}")
    return investors


# ---------------------------------------------------------------------------
# Phase 3 — Persistence
# ---------------------------------------------------------------------------

def save_to_mongodb(investors: list[dict]) -> None:
    """Upsert investor records into the ``etoro_pi`` MongoDB collection.

    Each investment record is keyed by ``userName``, which is used both as the
    MongoDB ``_id`` and as the unique index constraint.  A ``ReplaceOne`` with
    ``upsert=True`` is used so existing records are updated and new records are
    inserted in a single ``bulk_write`` call.

    The write is split into chunks of ``WRITE_BATCH_SIZE`` to avoid sending a
    single oversized wire message.  Each chunk is retried independently on
    transient connection errors (``AutoReconnect`` / ``ConnectionFailure``)
    with exponential back-off.

    Parameters
    ----------
    investors : list[dict]
        Enriched investor records (as returned by ``fetch_user_profiles``).
        Records without a ``userName`` are silently skipped.
    """
    if not investors:
        print("No investors to save.")
        return

    client = DatabaseManager().get_client()
    db_name = os.getenv('MONGODB_DATABASE', 'alphasentra-core')
    db = client[db_name]
    coll = db['etoro_pi']

    # Ensure userName is the unique field; swallow the error silently when it
    # already exists (which is the expected state on subsequent runs).
    try:
        coll.create_index('userName', unique=True)
    except Exception:
        pass

    operations: list[ReplaceOne] = []
    skipped = 0

    for inv in investors:
        uname = inv.get('userName')
        if not uname:
            skipped += 1
            continue
        doc = dict(inv)
        doc['_id'] = uname
        operations.append(ReplaceOne({'_id': uname}, doc, upsert=True))

    if not operations:
        print(f"Saved to MongoDB '{db_name}.etoro_pi': 0 inserted, 0 updated, "
              f"{skipped} skipped out of {len(investors)} records.")
        DatabaseManager().close_connection()
        return

    WRITE_BATCH_SIZE = 500
    total_inserted = 0
    total_updated = 0
    chunks = [
        operations[i:i + WRITE_BATCH_SIZE]
        for i in range(0, len(operations), WRITE_BATCH_SIZE)
    ]

    for chunk_idx, chunk in enumerate(tqdm(chunks, desc="[mongo]", unit="batch", ncols=80), 1):
        result = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                result = coll.bulk_write(chunk, ordered=False)
                break
            except (pymongo.errors.AutoReconnect, pymongo.errors.ConnectionFailure) as exc:
                if attempt < MAX_RETRIES:
                    _sleep_with_progress(RETRY_DELAYS[attempt],
                                         label=f"Retry {attempt+1}")
                else:
                    raise RuntimeError(
                        f"Failed to write chunk {chunk_idx}/{len(chunks)} after "
                        f"{MAX_RETRIES + 1} attempts: {exc}"
                    ) from exc

        if result is not None:
            total_inserted += result.upserted_count
            total_updated += result.modified_count

    print(f"Saved to MongoDB '{db_name}.etoro_pi': {total_inserted} inserted, "
          f"{total_updated} updated, {skipped} skipped out of {len(investors)} records.")
    DatabaseManager().close_connection()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# Run the full pipeline: discover → enrich → persist.
all_investors, global_total = collect_all()
print(f"\nTotal investors retrieved: {len(all_investors)}")
print(f"API global totalItems (best observed): {global_total}")

all_investors = fetch_user_profiles(all_investors)

print(f"\nSummary: collected {len(all_investors)} unique popular investors out of "
      f"{global_total or 'unknown'} reported by eToro.")

save_to_mongodb(all_investors)

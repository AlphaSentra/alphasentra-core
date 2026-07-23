"""eToro Pro Investor collection pipeline."""

from __future__ import annotations

import os
import time

from etoro.client import EToroClient
from etoro.repository import InvestorRepository


_API_KEY = os.getenv("ETORO_PUBLIC_KEY", "")
_USERNAME_BATCH_SIZE = 20
_RATE_LIMIT_DELAY = 1.1
_MAX_RETRIES = 5
_RETRY_DELAYS = [5, 10, 20, 40, 60]
_LONG_PAUSE_SECONDS = 60


def _sleep_with_progress(seconds: float, label: str = "Waiting") -> None:
    from tqdm import tqdm

    for _ in tqdm(range(int(seconds * 10)), desc=label, unit="0.1s", ncols=80, leave=False):
        time.sleep(0.1)


def collect_all(
    client: EToroClient,
    default_page_size: int = 1000,
    delay_seconds: float = 1.0,
) -> tuple[list[dict], int | None]:
    seen: dict[str, dict] = {}

    periods = ["CurrWeek", "CurrMonth", "CurrYear", "ThreeMonthsAgo", "OneYearAgo", "LastYear"]
    sorts = [
        "-copiersGain", "userName", "-gain", "-aumValue", "-copiers",
        "displayName", "-weeklyGain", "riskScore", "-riskScore", "username",
        "fullName", "", "copiersGain", "gain", "aumValue", "copiers",
    ]
    variants = [
        {"period": period, "sort": sort, "isPopularInvestor": "true"}
        for period in periods
        for sort in sorts
    ]

    global_total = None
    failed_fetches: list[tuple[dict, int]] = []
    MAX_RETRY_ROUNDS = 100

    def _fetch(variant: dict, page: int) -> tuple[list[dict], int | str | None]:
        params = {**variant, "page": page, "pageSize": default_page_size}
        for attempt in range(_MAX_RETRIES + 1):
            try:
                data = client.search_page(
                    period=variant["period"],
                    sort=variant["sort"],
                    page=page,
                    page_size=default_page_size,
                )
                # Treat empty first page as 404-equivalent
                if isinstance(data, dict) and not data.get("items") and attempt == 0:
                    raise Exception("empty response")
                items = data.get("items", []) if isinstance(data, dict) else data if isinstance(data, list) else []
                total = data.get("totalItems") if isinstance(data, dict) else None
                return items, total
            except Exception as exc:
                # Fall back to raw description for non-HTTP errors too
                status = getattr(exc, "response", None)
                status_code = status.status_code if status else None
                if status_code in (429, 404) and attempt < _MAX_RETRIES:
                    _sleep_with_progress(_RETRY_DELAYS[attempt], label=f"Retry {attempt+1}")
                else:
                    return [], getattr(exc, "response", None).status_code if getattr(exc, "response", None) else str(exc)
        return [], "max_retries"

    def _process_items(items: list[dict], variant_name: int, page: int) -> int:
        new = 0
        for item in items:
            uname = item.get("userName")
            if not uname or uname in seen:
                continue
            seen[uname] = item
            new += 1
        print(
            f"Variant {variant_name} page {page}: got {len(items)}, new={new}, "
            f"unique_total={len(seen)}, total={global_total}"
        )
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


def fetch_user_profiles(client: EToroClient, investors: list[dict]) -> list[dict]:
    usernames = [inv.get("userName") for inv in investors if inv.get("userName")]
    if not usernames:
        print("No usernames to enrich.")
        return investors

    total_batches = (len(usernames) + _USERNAME_BATCH_SIZE - 1) // _USERNAME_BATCH_SIZE
    print(f"\nEnriching {len(usernames)} investors via /api/v1/user-info/people ...")
    print(f"Batch size: {_USERNAME_BATCH_SIZE}, Rate limit delay: {_RATE_LIMIT_DELAY}s\n")

    enriched = 0
    failed = 0
    profile_map: dict[str, dict] = {}
    failed_usernames: list[str] = []

    def _request_batch(batch: list[str]) -> dict | None:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                data = client.get_profiles(batch)
                if not isinstance(data, dict):
                    return None
                return data
            except Exception as exc:
                status = getattr(exc, "__cause__", None)
                status_code = None
                if status and hasattr(status, "response") and status.response:
                    status_code = status.response.status_code
                if status_code in (401, 429, 404) and attempt < _MAX_RETRIES:
                    _sleep_with_progress(_RETRY_DELAYS[attempt], label=f"Retry {attempt+1}")
                else:
                    if attempt < _MAX_RETRIES:
                        _sleep_with_progress(_RETRY_DELAYS[attempt], label=f"Retry {attempt+1}")
                    else:
                        return None
        return None

    for i in range(0, len(usernames), _USERNAME_BATCH_SIZE):
        batch = usernames[i : i + _USERNAME_BATCH_SIZE]
        batch_num = i // _USERNAME_BATCH_SIZE + 1
        data = _request_batch(batch)

        if data is None:
            failed += len(batch)
            failed_usernames.extend(batch)
            continue

        users = data.get("users", [])
        returned_usernames = {u.get("username") for u in users if u.get("username")}

        for user in users:
            uname = user.get("username")
            if uname:
                profile_map[uname] = user
                enriched += 1

        missing = [u for u in batch if u not in returned_usernames]
        if missing:
            failed += len(missing)
            failed_usernames.extend(missing)
        print(f"  Batch {batch_num}/{total_batches}: returned {len(users)}/{len(batch)}, enriched={enriched}")

        if i + _USERNAME_BATCH_SIZE < len(usernames):
            time.sleep(_RATE_LIMIT_DELAY)

    _original_failed_count = len(failed_usernames)

    if failed_usernames:
        retry_round = 1
        MAX_RETRY_ROUNDS = 100

        while failed_usernames and retry_round <= MAX_RETRY_ROUNDS:
            retry_batches = (len(failed_usernames) + _USERNAME_BATCH_SIZE - 1) // _USERNAME_BATCH_SIZE
            print(f"\n{'='*60}")
            print(f"Retry round {retry_round}/{MAX_RETRY_ROUNDS}: retrying {len(failed_usernames)} usernames...")
            print(f"{'='*60}\n")

            recovered = 0
            still_failed = []

            for i in range(0, len(failed_usernames), _USERNAME_BATCH_SIZE):
                batch = failed_usernames[i : i + _USERNAME_BATCH_SIZE]
                batch_num = i // _USERNAME_BATCH_SIZE + 1
                data = _request_batch(batch)

                if data is None:
                    still_failed.extend(batch)
                    print(f"  Retry batch {batch_num}/{retry_batches}: no response")
                    continue

                users = data.get("users", [])
                returned_usernames = {u.get("username") for u in users if u.get("username")}
                batch_recovered = 0

                for user in users:
                    uname = user.get("username")
                    if uname:
                        profile_map[uname] = user
                        enriched += 1
                        batch_recovered += 1
                        recovered += 1

                missing = [u for u in batch if u not in returned_usernames]
                still_failed.extend(missing)
                print(
                    f"  Retry batch {batch_num}/{retry_batches}: "
                    f"returned {len(users)}/{len(batch)}, batch_recovered={batch_recovered}"
                )

                if i + _USERNAME_BATCH_SIZE < len(failed_usernames):
                    time.sleep(_RATE_LIMIT_DELAY)

            if recovered == 0 and retry_round >= 2:
                print(f"\n  [warn] No recoveries in round {retry_round} — ending retries.")
                break

            failed_usernames = still_failed
            failed = len(failed_usernames)
            retry_round += 1

        if failed_usernames:
            print(f"\n{'='*60}")
            print(f"Final sweep round: retrying {len(failed_usernames)} remaining usernames after a {_LONG_PAUSE_SECONDS}s pause...")
            print(f"{'='*60}\n")
            _sleep_with_progress(_LONG_PAUSE_SECONDS, label="Final sweep pause")

            final_recovered = 0
            still_failed_final = []

            for i in range(0, len(failed_usernames), _USERNAME_BATCH_SIZE):
                batch = failed_usernames[i : i + _USERNAME_BATCH_SIZE]
                batch_num = i // _USERNAME_BATCH_SIZE + 1
                data = _request_batch(batch)

                if data is None:
                    still_failed_final.extend(batch)
                    print(f"  Final batch {batch_num}: no response")
                    continue

                users = data.get("users", [])
                returned_usernames = {u.get("username") for u in users if u.get("username")}

                for user in users:
                    uname = user.get("username")
                    if uname:
                        profile_map[uname] = user
                        enriched += 1
                        final_recovered += 1

                missing = [u for u in batch if u not in returned_usernames]
                still_failed_final.extend(missing)
                print(
                    f"  Final batch {batch_num}: returned {len(users)}/{len(batch)}, "
                    f"recovered={final_recovered}"
                )

                if i + _USERNAME_BATCH_SIZE < len(failed_usernames):
                    time.sleep(_RATE_LIMIT_DELAY)

            failed_usernames = still_failed_final
            failed = len(failed_usernames)
            if final_recovered:
                print(f"\n  Final sweep recovered {final_recovered} additional profile(s).")

    for inv in investors:
        uname = inv.get("userName")
        if uname and uname in profile_map:
            inv.update(profile_map[uname])

    print(f"\n{'='*60}")
    print(f"Profile enrichment complete: {enriched} enriched, {failed} failed out of {len(usernames)} investors.")
    if failed_usernames:
        print(f"\nFailed usernames ({failed}):\n  " + "\n  ".join(failed_usernames))
    print(f"Note: {_original_failed_count - failed} of {_original_failed_count} originally-failed "
          f"usernames were recovered across all retry rounds.")
    print(f"{'='*60}")
    return investors


def save_to_mongodb(investors: list[dict]) -> None:
    if not investors:
        print("No investors to save.")
        return

    repo = InvestorRepository()
    repo.bulk_upsert(investors)
    print(f"Saved to MongoDB '{repo.db_name}.etoro_pi': upserted {len(investors)} records.")


def run_pipeline() -> None:
    client = EToroClient(api_key=_API_KEY)
    try:
        all_investors, global_total = collect_all(client)
        print(f"\nTotal investors retrieved: {len(all_investors)}")
        print(f"API global totalItems (best observed): {global_total}")

        all_investors = fetch_user_profiles(client, all_investors)

        print(f"\nSummary: collected {len(all_investors)} unique popular investors out of "
              f"{global_total or 'unknown'} reported by eToro.")

        save_to_mongodb(all_investors)
    finally:
        client.session.close()

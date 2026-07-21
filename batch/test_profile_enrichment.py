"""Test script for eToro profile enrichment via /api/v1/user-info/people.

Usage:
    python3 batch/test_profile_enrichment.py
    python3 batch/test_profile_enrichment.py --usernames goldeneight,koratrades,andevyns
    python3 batch/test_profile_enrichment.py --input batch/output/test_usernames.json
"""

import json
import os
import sys
import time
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
USER_PROFILE_URL = 'https://public-api.etoro.com/api/v1/user-info/people'
USERNAME_BATCH_SIZE = 20
RATE_LIMIT_DELAY = 1.1
MAX_RETRIES = 5
RETRY_DELAYS = [5, 10, 20, 40, 60]

TEST_USERNAMES = "goldeneight,koratrades,andevyns"  # Default test usernames

FIXED_USER_KEY = "eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJDRlhHb2ZDMldXM1NWcS1QZlFQR3R0VXUzRWkzZ1J3LmY3N0JGSm1waWNOY3BJQzJkYmg5cGFuS2xOLkJET2NpcXVLSGtNcVo2RUM1d3AyaWJDOEQtdS1zYmFEU0xUUkJwMlRBZFVmQmMtb18ifQ__"

EXPECTED_FIELDS = [
    'gcid', 'realCID', 'demoCID', 'username', 'language', 'languageIsoCode',
    'country', 'allowDisplayFullName', 'userBio', 'whiteLabel', 'optOut',
    'homepage', 'playerStatus', 'piLevel', 'isPi', 'avatars',
    'masterAccountCid', 'accountType', 'fundType', 'isVerified',
    'verificationLevel', 'accountStatus', 'gdprInfo', 'firstName',
    'middleName', 'lastName', 'aboutMe', 'aboutMeShort',
    'customerRestrictions', 'userFlowSignature',
]


def _headers():
    return {
        'User-Agent': 'Mozilla/5.0 (compatible; alphasentra-etoro-client)',
        'Accept': 'application/json',
        'x-api-key': API_KEY,
        'x-user-key': FIXED_USER_KEY,
        'x-request-id': str(uuid.uuid4()),
    }


def fetch_profiles(usernames):
    if not usernames:
        print("No usernames to test.")
        return []

    all_users = []
    enriched = 0
    failed = 0
    total_batches = (len(usernames) + USERNAME_BATCH_SIZE - 1) // USERNAME_BATCH_SIZE

    print(f"\nTesting profile enrichment for {len(usernames)} usernames in {total_batches} batches...")
    print(f"Batch size: {USERNAME_BATCH_SIZE}, Rate limit delay: {RATE_LIMIT_DELAY}s\n")

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
                all_users.append(user)
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

    print(f"\n{'='*60}")
    print(f"Total: {enriched} enriched, {failed} failed out of {len(usernames)}")
    print(f"{'='*60}")
    return all_users


def validate_fields(users):
    print("\n--- Field Validation ---")
    if not users:
        print("No users to validate.")
        return

    all_field_sets = {}
    for user in users:
        for field in user.keys():
            all_field_sets[field] = all_field_sets.get(field, 0) + 1

    print(f"\nFields found across {len(users)} users:")
    for field in sorted(all_field_sets.keys()):
        count = all_field_sets[field]
        pct = count / len(users) * 100
        print(f"  {field}: {count}/{len(users)} ({pct:.0f}%)")

    missing_from_spec = set(EXPECTED_FIELDS) - set(all_field_sets.keys())
    if missing_from_spec:
        print(f"\nWARNING: Expected fields not found in any response: {sorted(missing_from_spec)}")
    else:
        print("\nAll expected fields from API spec are present.")

    extra_fields = set(all_field_sets.keys()) - set(EXPECTED_FIELDS)
    if extra_fields:
        print(f"Extra fields returned by API: {sorted(extra_fields)}")

    print("\n--- Sample Record ---")
    sample = users[0]
    print(json.dumps(sample, indent=2, ensure_ascii=False))


def save_results(users, output_path):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(users, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(users)} profiles to: {output}")


def main():
    usernames = [u.strip() for u in TEST_USERNAMES.split(',') if u.strip()]
    if not usernames:
        print("No usernames configured in TEST_USERNAMES.")
        sys.exit(1)

    users = fetch_profiles(usernames)
    validate_fields(users)
    save_results(users, 'batch/output/test_enriched_profiles.json')


if __name__ == '__main__':
    main()

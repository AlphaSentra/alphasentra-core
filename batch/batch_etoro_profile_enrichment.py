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
USERNAME_BATCH_SIZE = 50
RATE_LIMIT_DELAY = 1.1
MAX_RETRIES = 3
RETRY_DELAYS = [5, 10, 20]


def _headers():
    return {
        'User-Agent': 'Mozilla/5.0 (compatible; alphasentra-etoro-client)',
        'Accept': 'application/json',
        'x-api-key': API_KEY,
        'x-user-key': get_random_private_key(),
        'x-request-id': str(uuid.uuid4()),
    }


def load_usernames(source):
    """Load usernames from a JSON file, JSONL file, or plain text file (one per line)."""
    path = Path(source)
    if not path.exists():
        print(f"Error: file not found: {source}")
        sys.exit(1)

    suffix = path.suffix.lower()
    usernames = []

    if suffix == '.json':
        data = json.loads(path.read_text())
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    usernames.append(item)
                elif isinstance(item, dict):
                    usernames.append(item.get('userName') or item.get('username'))
        elif isinstance(data, dict):
            usernames = [data.get('userName') or data.get('username')]
    elif suffix == '.jsonl':
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                usernames.append(obj.get('userName') or obj.get('username'))
    else:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                usernames.append(line)

    usernames = [u for u in usernames if u]
    unique = list(dict.fromkeys(usernames))
    print(f"Loaded {len(usernames)} usernames ({len(unique)} unique) from {source}")
    return unique


def fetch_all_profiles(usernames, output_path):
    """Fetch full profile data for every username and save raw API responses."""
    if not usernames:
        print("No usernames to process.")
        return

    all_responses = []
    enriched = 0
    failed = 0
    failed_details = []

    total_batches = (len(usernames) + USERNAME_BATCH_SIZE - 1) // USERNAME_BATCH_SIZE
    print(f"\nFetching profiles for {len(usernames)} usernames in {total_batches} batches of up to {USERNAME_BATCH_SIZE}...")
    print(f"Rate limit: {USERNAME_BATCH_SIZE} usernames per request, {RATE_LIMIT_DELAY}s between requests (60 req / 60s quota)")
    print(f"Output: {output_path}\n")

    for i in range(0, len(usernames), USERNAME_BATCH_SIZE):
        batch = usernames[i:i + USERNAME_BATCH_SIZE]
        batch_num = i // USERNAME_BATCH_SIZE + 1
        data = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    USER_PROFILE_URL,
                    params={'usernames': json.dumps(batch)},
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
                if status in (429, 404) and attempt < MAX_RETRIES:
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
            failed_details.extend(batch)
            print(f"  Batch {batch_num}/{total_batches}: FAILED (no data after retries)")
            continue

        users = data.get('users', [])
        returned_usernames = {u.get('username') for u in users if u.get('username')}

        for user in users:
            uname = user.get('username')
            if uname:
                all_responses.append(user)
                enriched += 1

        missing = [u for u in batch if u not in returned_usernames]
        if missing:
            failed += len(missing)
            failed_details.extend(missing)

        print(
            f"  Batch {batch_num}/{total_batches}: "
            f"requested={len(batch)}, returned={len(users)}, "
            f"enriched={enriched}, failed={failed}"
        )

        if i + USERNAME_BATCH_SIZE < len(usernames):
            time.sleep(RATE_LIMIT_DELAY)

    # Save complete raw response
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(all_responses, indent=2, ensure_ascii=False))

    print(f"\n{'='*60}")
    print(f"Done. Total enriched: {enriched}, Total failed: {failed} out of {len(usernames)}")
    print(f"Raw API responses saved to: {output}")
    print(f"{'='*60}")

    if failed_details:
        failed_path = output.with_suffix('.failed.json')
        failed_path.write_text(json.dumps(failed_details, indent=2, ensure_ascii=False))
        print(f"Failed usernames saved to: {failed_path}")

    # Print sample keys to verify we got everything
    if all_responses:
        sample = all_responses[0]
        print(f"\nSample record — username: {sample.get('username')}")
        print(f"Top-level keys ({len(sample.keys())} fields):")
        for key in sorted(sample.keys()):
            val = sample[key]
            val_type = type(val).__name__
            if isinstance(val, (dict, list)):
                if isinstance(val, dict):
                    print(f"  {key}: {val_type} ({len(val)} sub-keys: {list(val.keys())[:8]})")
                else:
                    print(f"  {key}: {val_type} ({len(val)} items)")
            else:
                print(f"  {key}: {val_type} = {repr(val)[:80]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Fetch full eToro user profiles from /api/v1/user-info/people'
    )
    parser.add_argument(
        'source',
        help='Path to file containing usernames (.json, .jsonl, or plain text one-per-line)'
    )
    parser.add_argument(
        '-o', '--output',
        default='batch/output/etoro_user_profiles.json',
        help='Output path for the JSON file (default: batch/output/etoro_user_profiles.json)'
    )
    args = parser.parse_args()

    usernames = load_usernames(args.source)
    fetch_all_profiles(usernames, args.output)


if __name__ == '__main__':
    main()

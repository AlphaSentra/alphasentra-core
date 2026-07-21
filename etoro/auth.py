import os
import random
import uuid

import requests


class EToroAuthError(Exception):
    pass


def public_api_session(api_key: str, user_key: str, *, timeout: int = 30) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; alphasentra-etoro-client)",
        "Accept": "application/json",
        "x-api-key": api_key,
        "x-user-key": user_key,
        "x-request-id": str(uuid.uuid4()),
    })
    return session


def get_random_private_key(env_var: str = "ETORO_PRIVATE_KEY") -> str:
    raw = os.getenv(env_var, "")
    if not raw:
        raise EToroAuthError(
            f"{env_var} environment variable is required. "
            "Provide a single key or a comma-separated list of keys."
        )
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise EToroAuthError(
            f"{env_var} environment variable is empty or contains no valid keys."
        )
    return random.choice(keys)

#config file - design by copilot

import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()   # ← reads .env into environment variables

@dataclass(frozen=True)
class EnvSettings:
    base_url: str
    crud_api_key: str
    api_524_key: str  # old final version key
    scopus_api_key: str

#get variables from env
PURE_BASE_URL_P = os.getenv("PURE_BASE_URL_P")
PURE_BASE_URL_A = os.getenv("PURE_BASE_URL_A")

PURE_CRUD_API_KEY_P = os.getenv("PURE_CRUD_API_KEY_P")
PURE_CRUD_API_KEY_A = os.getenv("PURE_CRUD_API_KEY_A")

PURE_524_API_KEY_P = os.getenv("PURE_524_API_KEY_P")
PURE_524_API_KEY_A = os.getenv("PURE_524_API_KEY_A")

SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY")

def resolve_settings(target: str) -> EnvSettings:
    """
    target: 'p' (Production) or 'a' (Accept)
    """
    t = target.lower()[0]
    if t == 'p':
        return EnvSettings(
            base_url=PURE_BASE_URL_P,
            crud_api_key=PURE_CRUD_API_KEY_P,
            api_524_key=PURE_524_API_KEY_P,
            scopus_api_key = SCOPUS_API_KEY
        )
    elif t == 'a':
        return EnvSettings(
            base_url=PURE_BASE_URL_A,
            crud_api_key=PURE_CRUD_API_KEY_A,
            api_524_key=PURE_524_API_KEY_A,
            scopus_api_key = SCOPUS_API_KEY
        )
    else:
        raise ValueError("target must start with 'p' or 'a'")

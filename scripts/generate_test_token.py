"""Generate JWT access tokens for local testing."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core import jwt_auth

TEST_USER = {
    "email": "tester@example.com",
    "username": "tester",
    "id": "test-user-001",
}

if __name__ == "__main__":
    tokens = jwt_auth.create_tokens(TEST_USER)
    print("Access Token:")
    print(tokens.access_token)
    print()
    print("Refresh Token:")
    print(tokens.refresh_token)

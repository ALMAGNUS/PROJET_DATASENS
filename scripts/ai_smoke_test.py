"""
Smoke test IA local via API.
"""

from __future__ import annotations

import json
import os
from urllib import request


def main() -> None:
    api_base = os.getenv("API_BASE", "http://localhost:8001/api/v1")
    token = os.getenv("API_TOKEN")
    if not token:
        raise SystemExit("API_TOKEN manquant")

    payload = {
        "text": "Ce service est très utile.",
        "model": "camembert",
        "task": "text-classification",
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{api_base}/ai/predict",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    print(body)


if __name__ == "__main__":
    main()

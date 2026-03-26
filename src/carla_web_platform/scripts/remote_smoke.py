from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "duckpark-remote-smoke/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def assert_healthz(base_url: str, timeout: float) -> dict[str, object]:
    status, content_type, body = fetch(f"{base_url}/healthz", timeout)
    payload = json.loads(body.decode("utf-8"))
    if status != 200 or payload.get("status") != "ok":
        raise RuntimeError(f"/healthz failed: status={status}, payload={payload!r}")
    return {"path": "/healthz", "status": status, "content_type": content_type}


def assert_ui(base_url: str, timeout: float) -> dict[str, object]:
    status, content_type, body = fetch(f"{base_url}/ui", timeout)
    text = body.decode("utf-8", errors="ignore")
    if status != 200 or "<html" not in text.lower():
        raise RuntimeError(f"/ui failed: status={status}")
    return {"path": "/ui", "status": status, "content_type": content_type}


def assert_docs(base_url: str, timeout: float) -> dict[str, object]:
    status, content_type, body = fetch(f"{base_url}/docs", timeout)
    text = body.decode("utf-8", errors="ignore")
    if status != 200 or "swagger" not in text.lower():
        raise RuntimeError(f"/docs failed: status={status}")
    return {"path": "/docs", "status": status, "content_type": content_type}


def assert_runs(base_url: str, timeout: float) -> dict[str, object]:
    status, content_type, body = fetch(f"{base_url}/runs", timeout)
    payload = json.loads(body.decode("utf-8"))
    if status != 200 or payload.get("success") is not True:
        raise RuntimeError(f"/runs failed: status={status}, payload={payload!r}")
    return {
        "path": "/runs",
        "status": status,
        "content_type": content_type,
        "items": len(payload.get("data", [])) if isinstance(payload.get("data"), list) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke check a remote CARLA web platform instance.")
    parser.add_argument("--base-url", required=True, help="Base URL such as http://192.168.110.151:8000")
    parser.add_argument(
        "--mode",
        default="full",
        choices=("health", "full"),
        help="health 仅检查 /healthz；full 额外检查 /ui /docs /runs",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    checks: list[dict[str, object]] = []

    try:
        checks.append(assert_healthz(base_url, args.timeout))
        if args.mode == "full":
            checks.append(assert_ui(base_url, args.timeout))
            checks.append(assert_docs(base_url, args.timeout))
            checks.append(assert_runs(base_url, args.timeout))
    except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"ok": False, "base_url": base_url, "mode": args.mode, "error": str(exc), "checks": checks},
                ensure_ascii=False,
            )
        )
        return 1

    print(json.dumps({"ok": True, "base_url": base_url, "mode": args.mode, "checks": checks}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

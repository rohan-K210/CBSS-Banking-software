#!/usr/bin/env python3
"""
CBSS Health Check — Verify all services are alive and reachable.

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --json
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

SERVICES = [
    {"name": "admin",             "port": 5000},
    {"name": "client",            "port": 5001},
    {"name": "hacker",            "port": 5002},
    {"name": "fraud_detector",    "port": 5003},
    {"name": "simple_transaction","port": 5004},
]


def check_service(name: str, port: int, timeout: float = 3.0) -> dict:
    """Check a single service's health endpoint."""
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode())
        return {
            "name": name,
            "port": port,
            "status": "healthy",
            "details": data,
        }
    except urllib.error.URLError as e:
        return {
            "name": name,
            "port": port,
            "status": "unreachable",
            "details": {"error": str(e)},
        }
    except Exception as e:
        return {
            "name": name,
            "port": port,
            "status": "error",
            "details": {"error": str(e)},
        }


def main():
    parser = argparse.ArgumentParser(description="Check health of all CBSS services")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = []
    all_healthy = True

    for svc in SERVICES:
        result = check_service(svc["name"], svc["port"])
        results.append(result)
        if result["status"] != "healthy":
            all_healthy = False

    if args.json:
        print(json.dumps({"all_healthy": all_healthy, "services": results}, indent=2))
    else:
        print("=" * 50)
        print("CBSS Health Check")
        print("=" * 50)
        for r in results:
            icon = "✓" if r["status"] == "healthy" else "✗"
            print(f"  {icon} {r['name']:20s} port {r['port']:5d} — {r['status']}")
        print("=" * 50)
        if all_healthy:
            print("All services are healthy!")
        else:
            print("Some services are not responding.")
        print()

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()

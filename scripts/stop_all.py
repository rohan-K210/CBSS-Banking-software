#!/usr/bin/env python3
"""
CBSS Process Manager — Stop All Services.

Finds and terminates Flask processes running on CBSS ports.

Usage:
    python scripts/stop_all.py
"""

import logging
import subprocess
import sys
import socket

SERVICES = [
    {"name": "admin",             "port": 5000},
    {"name": "client",            "port": 5001},
    {"name": "hacker",            "port": 5002},
    {"name": "fraud_detector",    "port": 5003},
    {"name": "simple_transaction","port": 5004},
]

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [SHUTDOWN] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("stop_all")


def find_pid_on_port(port: int) -> int | None:
    """Find the PID of a process listening on a given port."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    return int(parts[-1])
        else:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=5,
            )
            pids = result.stdout.strip().split("\n")
            if pids and pids[0]:
                return int(pids[0])
    except Exception as e:
        logger.debug("Error finding PID on port %d: %s", port, e)
    return None


def main():
    logger.info("Stopping all CBSS services...")

    stopped = 0
    for svc in SERVICES:
        name = svc["name"]
        port = svc["port"]
        pid = find_pid_on_port(port)

        if pid:
            logger.info("Killing '%s' (PID %d, port %d)", name, pid, port)
            try:
                import os
                os.kill(pid, signal.SIGTERM if sys.platform != "win32" else 9)
                stopped += 1
            except ProcessLookupError:
                logger.warning("'%s' (PID %d) already stopped", name, pid)
            except Exception as e:
                logger.error("Failed to stop '%s': %s", name, e)
        else:
            logger.info("'%s' not running on port %d", name, port)

    if stopped:
        logger.info("Sent stop signals to %d service(s).", stopped)
    else:
        logger.info("No running services found.")


if __name__ == "__main__":
    import signal
    main()

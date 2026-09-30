#!/usr/bin/env python3
"""
CBSS Process Manager — Start All Services.

Launches all 5 Flask applications as subprocesses with:
- Predictable port assignments
- Prefixed stdout/stderr logging
- Startup failure detection
- Port conflict detection
- Graceful shutdown on SIGINT/SIGTERM

Usage:
    python scripts/start_all.py
    python scripts/start_all.py --no-health-check
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Project root is one level up from scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SERVICES = [
    {"name": "admin",            "module": "apps.admin",            "port": 5000},
    {"name": "client",           "module": "apps.client",           "port": 5001},
    {"name": "hacker",           "module": "apps.hacker",           "port": 5002},
    {"name": "fraud_detector",   "module": "apps.fraud_detector",   "port": 5003},
    {"name": "simple_transaction","module": "apps.simple_transaction","port": 5004},
]

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [STARTUP] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("start_all")

processes: dict[str, subprocess.Popen] = {}


def check_port_available(port: int) -> bool:
    """Check if a port is available."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def start_service(service: dict) -> subprocess.Popen | None:
    """Start a single Flask service as a subprocess."""
    name = service["name"]
    module = service["module"]
    port = service["port"]

    if not check_port_available(port):
        logger.error("Port %d is already in use — cannot start '%s'", port, name)
        return None

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    cmd = [sys.executable, "-m", module]

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    logger.info("Started '%s' (PID %d) on port %d", name, proc.pid, port)
    return proc


def check_health(name: str, port: int, timeout: float = 5.0) -> bool:
    """Check if a service is responding on /health."""
    import urllib.request
    import urllib.error
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status == 200
    except Exception:
        return False


def shutdown_all():
    """Gracefully terminate all running processes."""
    logger.info("Shutting down all services...")
    for name, proc in processes.items():
        if proc.poll() is None:
            logger.info("Terminating '%s' (PID %d)", name, proc.pid)
            proc.terminate()
    for name, proc in processes.items():
        try:
            proc.wait(timeout=5)
            logger.info("'%s' stopped (exit code %s)", name, proc.returncode)
        except subprocess.TimeoutExpired:
            logger.warning("Force-killing '%s' (PID %d)", name, proc.pid)
            proc.kill()
            proc.wait()
    logger.info("All services stopped.")


def stream_output(proc: subprocess.Popen, name: str):
    """Read and prefix output from a subprocess (runs in a thread)."""
    import threading
    def _reader():
        for line in proc.stdout:
            print(f"[{name.upper()}] {line}", end="")
    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return t


def main():
    parser = argparse.ArgumentParser(description="Start all CBSS services")
    parser.add_argument("--no-health-check", action="store_true",
                        help="Skip health checks after startup")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("CBSS Backend — Starting all services")
    logger.info("=" * 60)

    # Register signal handlers
    def handle_signal(signum, frame):
        shutdown_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Start all services
    threads = []
    for service in SERVICES:
        proc = start_service(service)
        if proc is None:
            logger.error("Failed to start '%s' — aborting", service["name"])
            shutdown_all()
            sys.exit(1)
        processes[service["name"]] = proc
        t = stream_output(proc, service["name"])
        threads.append(t)

    # Wait a moment for startup
    time.sleep(2)

    # Check for immediate crashes
    for service in SERVICES:
        name = service["name"]
        proc = processes[name]
        if proc.poll() is not None:
            logger.error("'%s' crashed on startup (exit code %s)", name, proc.returncode)
            shutdown_all()
            sys.exit(1)

    # Health checks
    if not args.no_health_check:
        logger.info("Running health checks...")
        all_healthy = True
        for service in SERVICES:
            name = service["name"]
            port = service["port"]
            healthy = check_health(name, port)
            status = "✓ HEALTHY" if healthy else "✗ UNREACHABLE"
            logger.info("  %s — %s (port %d)", name, status, port)
            if not healthy:
                all_healthy = False

        if all_healthy:
            logger.info("All services are healthy!")
        else:
            logger.warning("Some services did not respond to health checks.")

    logger.info("=" * 60)
    logger.info("All 5 services running. Press Ctrl+C to stop.")
    logger.info("Ports: %s", ", ".join(
        f"{s['name']}={s['port']}" for s in SERVICES
    ))
    logger.info("=" * 60)

    # Keep running until interrupted
    try:
        while True:
            # Monitor for crashes
            for service in SERVICES:
                name = service["name"]
                proc = processes[name]
                if proc.poll() is not None:
                    logger.error("'%s' died unexpectedly (exit code %s)", name, proc.returncode)
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_all()


if __name__ == "__main__":
    main()

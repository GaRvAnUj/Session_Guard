"""
Main entry point for the Client Agent on Windows Public Computers.
Loads configuration, binds to the server, and initiates active session monitoring.
"""

import argparse
import logging
import os
import signal
import sys
import time

import yaml

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from client.api_client import APIClient
from client.session_monitor import SessionMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(current_dir, "client.log"), mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("ClientMain")


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        logger.warning("Config file %s not found. Using defaults.", config_path)
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    parser = argparse.ArgumentParser(description="Secure Session Manager - Windows Client")
    parser.add_argument("--config", default=os.path.join(current_dir, "config.yaml"), help="Path to config.yaml")
    parser.add_argument("--machine-id", help="Override machine ID")
    parser.add_argument("--test-login", action="store_true", help="Simulate immediate user login for test/demo")
    parser.add_argument("--panic-lock", action="store_true", help="Trigger emergency panic lock and exit")
    args = parser.parse_args()

    config = load_config(args.config)
    client_cfg = config.get("client", {})
    server_cfg = config.get("server", {})
    crypto_cfg = config.get("crypto", {})

    machine_id = args.machine_id or client_cfg.get("machine_id", os.environ.get("COMPUTERNAME", "PC_PUBLIC_01"))

    # Instantiate API client
    api_client = APIClient(
        base_url=server_cfg.get("base_url", "http://localhost:8443"),
        api_key=server_cfg.get("api_key", "secure-client-api-key-2026-public-lab"),
        verify_ssl=server_cfg.get("verify_ssl", False),
        timeout=server_cfg.get("timeout_seconds", 10),
    )

    # Instantiate Session Monitor
    monitor = SessionMonitor(
        machine_id=machine_id,
        api_client=api_client,
        aes_key=crypto_cfg.get("aes_key"),
        hmac_key=crypto_cfg.get("hmac_key"),
        idle_timeout_seconds=client_cfg.get("idle_timeout_minutes", 15) * 60,
        poll_interval=client_cfg.get("poll_interval_seconds", 3),
    )

    if args.panic_lock:
        logger.warning("Executing standalone panic lock invocation...")
        monitor.trigger_panic_lock()
        sys.exit(0)

    # Handle graceful termination
    def handle_signal(sig, frame):
        logger.info("Signal received. Terminating monitor safely...")
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    monitor.start()

    if args.test_login:
        logger.info("Starting simulated login session for demonstration...")
        session_id = monitor.on_user_login()
        logger.info("Active session running: %s. Press Ctrl+C to log out.", session_id)

    logger.info("Secure Session Manager Client is running for machine: %s", machine_id)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Logging out session...")
        monitor.stop()


if __name__ == "__main__":
    main()

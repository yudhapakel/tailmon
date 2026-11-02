#!/usr/bin/env python3
"""
tailmon - Tailscale Homelab Node Sentinel & Uptime Monitor
Author: Yudha Harwanto Putra (yudhapakel)
"""

import sys
import os
import json
import time
import argparse
import subprocess
import logging
from datetime import datetime
from notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("tailmon")

STATE_FILE = os.path.expanduser("~/.config/tailmon/state.json")

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        logger.error("Configuration file not found: %s", config_path)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def get_tailscale_status() -> dict:
    try:
        res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        logger.error("Failed to run 'tailscale status --json': %s", e)
        return {}

def ping_node(ip_or_name: str, timeout: int = 2) -> tuple:
    """Returns (is_reachable: bool, latency_ms: float or None)"""
    try:
        cmd = ["tailscale", "ping", "-c", "1", f"-timeout={timeout}s", ip_or_name]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and "pong from" in res.stdout:
            for part in res.stdout.split():
                if part.endswith("ms") or part.endswith("s"):
                    return True, part
            return True, "<1ms"
        return False, None
    except Exception:
        return False, None

def parse_peers(status_data: dict, config: dict) -> list:
    peers = []
    filter_funnel = config.get("filter_funnel_nodes", True)
    watched = [w.lower() for w in config.get("watched_devices", [])]

    for peer in status_data.get("Peer", {}).values():
        name = peer.get("HostName", "unknown")
        ips = peer.get("TailscaleIPs", [])
        ipv4 = ips[0] if ips else "-"
        online = peer.get("Online", False)
        last_seen = peer.get("LastSeen", "")

        # Skip ephemeral funnel ingress nodes if configured
        if filter_funnel and "funnel-ingress" in name.lower():
            continue

        # If watched_devices is specified, filter by it
        if watched and name.lower() not in watched:
            continue

        peers.append({
            "name": name,
            "ip": ipv4,
            "online": online,
            "last_seen": last_seen,
            "os": peer.get("OS", "unknown")
        })

    # Sort by hostname
    peers.sort(key=lambda x: x["name"].lower())
    return peers

def print_status_table(peers: list, self_name: str):
    print("\n" + "=" * 65)
    print(f" TAILMON - Tailscale Mesh Status ({self_name})")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print(f"{'DEVICE NAME':<22} | {'TAILSCALE IP':<16} | {'STATUS':<9} | {'LATENCY'}")
    print("-" * 65)

    for p in peers:
        status_icon = "[UP]" if p["online"] else "[DOWN]"
        latency_str = "-"
        if p["online"]:
            reachable, lat = ping_node(p["ip"], timeout=1)
            latency_str = lat if reachable else "ping failed"

        print(f"{p['name']:<22} | {p['ip']:<16} | {status_icon:<9} | {latency_str}")
    print("=" * 65 + "\n")

def run_sentinel_cycle(config: dict, notifier: TelegramNotifier, state: dict):
    status_data = get_tailscale_status()
    if not status_data:
        return

    peers = parse_peers(status_data, config)
    offline_threshold = config.get("offline_threshold_cycles", 2)

    for p in peers:
        name = p["name"]
        curr_online = p["online"]
        prev_data = state.get(name, {"status": "UNKNOWN", "fail_count": 0})
        prev_status = prev_data.get("status", "UNKNOWN")
        fail_count = prev_data.get("fail_count", 0)

        if curr_online:
            if prev_status == "DOWN":
                # Recovered alert
                _, lat = ping_node(p["ip"], timeout=2)
                lat_text = f" (Latency: {lat})" if lat else ""
                msg = f"*[RECOVERED]* Device `{name}` is back online!{lat_text}\nIP: `{p['ip']}`"
                notifier.send(msg)
                logger.info("Device recovered: %s", name)

            state[name] = {"status": "UP", "fail_count": 0, "last_seen": datetime.now().isoformat()}
        else:
            fail_count += 1
            if fail_count >= offline_threshold and prev_status != "DOWN":
                # Trigger offline alert
                msg = f"*[ALERT]* Device `{name}` is unreachable!\nIP: `{p['ip']}`\nStatus: Offline for {fail_count} cycles"
                notifier.send(msg)
                logger.warning("Device offline alert triggered for: %s", name)
                state[name] = {"status": "DOWN", "fail_count": fail_count, "last_seen": p.get("last_seen")}
            else:
                state[name] = {"status": prev_status, "fail_count": fail_count, "last_seen": prev_data.get("last_seen")}

    save_state(state)

def main():
    parser = argparse.ArgumentParser(description="Tailscale Mesh Node Sentinel & Uptime Monitor")
    parser.add_argument("-c", "--config", default="config.json", help="Path to config.json (default: config.json)")
    parser.add_argument("--status", action="store_true", help="Print live status table of devices and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as background daemon")
    args = parser.parse_args()

    # Fallback to config.example.json if config.json does not exist
    config_file = args.config
    if not os.path.exists(config_file):
        example_cfg = os.path.join(os.path.dirname(config_file), "config.example.json")
        if os.path.exists(example_cfg):
            config_file = example_cfg

    config = load_config(config_file)
    tg_cfg = config.get("telegram", {})
    notifier = TelegramNotifier(
        bot_token=tg_cfg.get("bot_token", ""),
        chat_id=tg_cfg.get("chat_id", ""),
        enabled=tg_cfg.get("enabled", False)
    )

    if args.status:
        status_data = get_tailscale_status()
        self_name = status_data.get("Self", {}).get("HostName", "localhost")
        peers = parse_peers(status_data, config)
        print_status_table(peers, self_name)
        return

    logger.info("Starting tailmon sentinel loop (Interval: %ds)...", config.get("poll_interval_seconds", 60))
    state = load_state()

    while True:
        try:
            run_sentinel_cycle(config, notifier, state)
        except Exception as e:
            logger.error("Error during sentinel cycle: %s", e)

        if not args.daemon:
            break
        time.sleep(config.get("poll_interval_seconds", 60))

if __name__ == "__main__":
    main()

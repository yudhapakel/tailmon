# tailmon

A lightweight, zero-dependency Python sentinel daemon for monitoring device connectivity, latency, and uptime across private [Tailscale](https://tailscale.com) mesh networks with Telegram alerting.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square&logo=python)
![Tailscale](https://img.shields.io/badge/Tailscale-Mesh%20Network-informational.svg?style=flat-square)
![Systemd](https://img.shields.io/badge/Systemd-Service-orange.svg?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)

---

## Features

- **Zero External Dependencies:** Built entirely with Python 3 standard library modules (`urllib`, `subprocess`, `json`, `argparse`).
- **Smart Node Filtering:** Automatically filters out ephemeral Tailscale Funnel ingress nodes and monitors designated machines only.
- **Live CLI Status Table:** Instant terminal dashboard displaying IP addresses, node states (`[UP]` / `[DOWN]`), and real-time Tailscale latency.
- **Stateful Alerting:** Tracks failure counts to ensure notifications trigger only on actual state transitions (`DOWN` or `RECOVERED`).
- **Systemd Integration:** Ready for background daemon deployment on Linux servers, homelab machines, or Raspberry Pi nodes.

---

## Quick Start

### 1. Clone and Configure
```bash
git clone https://github.com/yudhapakel/tailmon.git
cd tailmon
cp config.example.json config.json
```

Edit `config.json` with target devices and Telegram Bot credentials:
```json
{
  "poll_interval_seconds": 60,
  "ping_timeout_seconds": 2,
  "offline_threshold_cycles": 2,
  "filter_funnel_nodes": true,
  "telegram": {
    "enabled": false,
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  },
  "watched_devices": [
    "DESKTOP-D7Q985A",
    "POCO F6",
    "yudha-nitroan51558"
  ]
}
```

### 2. Live Status Overview
```bash
python3 tailmon.py --status
```

Sample CLI output:
```text
=================================================================
 TAILMON - Tailscale Mesh Status (homeserver)
 Time: 2026-11-02 18:48:10
=================================================================
DEVICE NAME            | TAILSCALE IP     | STATUS    | LATENCY
-----------------------------------------------------------------
DESKTOP-D7Q985A        | 100.127.11.50    | [UP]      | 3ms
POCO F6                | 100.81.114.15    | [DOWN]    | -
yudha-nitroan51558     | 100.120.199.111  | [DOWN]    | -
=================================================================
```

### 3. Run as Continuous Daemon
```bash
python3 tailmon.py --daemon
```

---

## Systemd Service Deployment

To run `tailmon` as a persistent user service:

```bash
mkdir -p ~/.config/systemd/user
cp tailmon.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now tailmon.service
```

Check status and logs:
```bash
systemctl --user status tailmon.service
journalctl --user -u tailmon.service -f
```

---

## License

MIT License &copy; 2026 Yudha Harwanto Putra

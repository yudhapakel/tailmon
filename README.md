# 🛰️ tailmon - Tailscale Homelab Sentinel & Uptime Monitor

A lightweight, zero-dependency Python sentinel daemon for monitoring device connectivity, latency, and uptime across your private [Tailscale](https://tailscale.com) mesh network with instant Telegram alerting.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square&logo=python)
![Tailscale](https://img.shields.io/badge/Tailscale-Mesh%20Network-informational.svg?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)

---

## ✨ Features

- ⚡ **Zero External Dependencies:** Built entirely with Python 3 standard library (`urllib`, `subprocess`, `json`, `argparse`).
- 🎯 **Smart Node Filtering:** Automatically filters out ephemeral Tailscale Funnel ingress nodes and monitors only physical/designated machines.
- 📡 **Live CLI Status Table:** Instant terminal dashboard displaying IP, status (UP/DOWN), and real-time ICMP/Tailscale ping latency.
- 🔔 **Stateful Telegram Alerting:** Tracks fail counters so you only receive alerts when a node changes state (Down or Recovered), avoiding noisy false positives.
- 🐧 **Systemd Ready:** Easily deployable as a background daemon on homeservers, Raspberry Pis, or VPS nodes.

---

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/yudhapakel/tailmon.git
cd tailmon
cp config.example.json config.json
```

Edit `config.json` with your target devices and optional Telegram Bot credentials:
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

### 2. View Live Status
```bash
python3 tailmon.py --status
```
Example Output:
```text
=================================================================
 🛰️  TAILMON - Tailscale Mesh Status (homeserver)
 Time: 2026-11-02 18:48:10
=================================================================
DEVICE NAME            | TAILSCALE IP     | STATUS    | LATENCY
-----------------------------------------------------------------
DESKTOP-D7Q985A        | 100.127.11.50    | 🟢 UP      | 3ms
POCO F6                | 100.81.114.15    | 🔴 DOWN    | -
yudha-nitroan51558     | 100.120.199.111  | 🔴 DOWN    | -
=================================================================
```

### 3. Run as Continuous Daemon
```bash
python3 tailmon.py --daemon
```

---

## 🛠️ Deploy as Systemd Service (Optional)

To keep `tailmon` running continuously in the background on Linux:

1. Copy the service template:
```bash
mkdir -p ~/.config/systemd/user
cp tailmon.service ~/.config/systemd/user/
```

2. Enable and start:
```bash
systemctl --user daemon-reload
systemctl --user enable --now tailmon.service
```

---

## 📜 License
MIT License © 2026 Yudha Harwanto Putra

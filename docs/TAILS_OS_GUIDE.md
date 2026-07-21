# 🛡️ JobHunt Pro — Tails OS & Tor Anonymity Operational Guide

This document outlines the architecture, configuration, and execution workflow for managing **JobHunt Pro** anonymously using **Tails OS** (The Amnesic Incognito Live System), **Tor SOCKS5**, **Rotating Proxies**, and **WireGuard VPNs**.

---

## 1. Multi-Tier Security Hierarchy

JobHunt Pro automatically evaluates and applies outbound connection security using the following priority matrix:

```
[ Tier 1: Tor SOCKS5 Network ]
          │
          ▼ (If Tor offline)
[ Tier 2: Residential Proxy Pool ]
          │
          ▼ (If proxies exhausted)
[ Tier 3: Public Proxy Rotator ]
          │
          ▼ (If all fail)
[ Tier 4: Direct TLS via WireGuard / OpenVPN ]
```

---

## 2. Enabling Tor Support (`core/tor_router.py`)

To route JobHunt Pro outbound requests through Tor:

### Environment Variables
Set the following environment variables in `.env` or system environment:

```env
TOR_ENABLED=true
TOR_SOCKS_HOST=127.0.0.1
TOR_SOCKS_PORT=9050
TOR_CONTROL_PORT=9051
TOR_CONTROL_PASSWORD=your_tor_control_password
```

### Automatic Circuit Renewal (IP Rotation)
JobHunt Pro can issue a `SIGNAL NEWNYM` command to the Tor Control Port (9051) to get a new exit node IP dynamically:

```python
from core.tor_router import get_tor_router

tor = get_tor_router()
if tor.renew_circuit():
    print("New Tor exit node assigned!")
```

---

## 3. Operating from Tails OS (Zero-Trace Administration)

Tails OS routes **all network traffic through Tor by default** and stores zero data to local disk.

### Execution Steps
1. Boot Tails OS from a USB flash drive.
2. Open a Terminal and run the JobHunt Pro admin script:
   ```bash
   bash scripts/tails_admin_setup.sh
   ```
3. All admin calls, API requests, and database commands will execute strictly inside RAM through `torsocks`.
4. When you shut down Tails OS, all temporary encryption keys, RAM buffers, and session histories are permanently erased.

---

## 4. Anonymity Health Score Check

To query the live anonymity status programmatically:

```python
from core.omni_shield import get_anonymity_health_score

status = get_anonymity_health_score()
print(f"Anonymity Grade: {status['grade']} ({status['anonymity_score']}/100)")
```

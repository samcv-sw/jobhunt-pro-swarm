# 🛡️ JobHunt Pro — Qubes OS & Whonix Compartmentalization Architecture

This document describes the design and deployment of the **Qubes OS + Whonix Isolation Matrix** for **JobHunt Pro**, running 24/7 in the cloud at **$0 permanent cost**.

---

## 1. Qubes OS Domain Architecture

JobHunt Pro segregates tasks into isolated micro-qubes:

```
┌─────────────────────────────────────────────────────────────┐
│                       sys-whonix                            │
│                 (Whonix-Gateway Qube)                       │
│        Enforces Tor Firewall & DNS Leak Block               │
└──────────────────────────────┬──────────────────────────────┘
                               │ Private Internal Net (10.152.152.0/24)
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│    anon-scraping-qube     │         │      anon-admin-qube      │
│  (Workstation Qube Port)  │         │  (Workstation Qube Port)  │
│        Port 9100          │         │        Port 9101          │
└───────────────────────────┘         └───────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        vault-qube                           │
│        (Air-Gapped Vault — Zero Network Adapters)          │
└─────────────────────────────────────────────────────────────┘
```

### Domain Descriptions:
1. **`sys-whonix` (Whonix-Gateway)**: The Tor firewall qube. All outbound requests pass through this container.
2. **`anon-scraping-qube`**: Dedicated job scraping worker using Tor Stream Isolation Port `9100`.
3. **`anon-admin-qube`**: Dedicated admin & campaign worker using Tor Stream Isolation Port `9101`.
4. **`vault-qube`**: Air-gapped container holding master DB secrets and cryptographic nonces (no WAN interfaces).

---

## 2. Stream Isolation (Anti-Identity Correlation)

Whonix assigns separate Tor circuits to separate stream ports:
* Port `9100` -> Tor Circuit A (Scraping Traffic)
* Port `9101` -> Tor Circuit B (Admin Campaigns)

This prevents job boards from linking scraping sessions with admin API traffic.

---

## 3. 24/7 $0 Permanent Cloud Setup

You can run this containerized Whonix stack on free cloud providers (Oracle Cloud Free Tier 4 ARM cores / 24GB RAM, Railway, or Render):

### Deployment:
```bash
bash scripts/qubes_whonix_deploy.sh
```

### Docker Compose Stack:
- `docker-compose.whonix.yml` creates a private internal bridge network (`whonix-internal-net`) for the workstation qubes.
- The workstation containers have **no direct WAN internet gateway**, making IP or DNS leaks impossible.

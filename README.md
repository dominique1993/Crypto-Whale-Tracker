# Crypto-Whale-Tracker
Real-time Ethereum whale tracker with WebSocket transaction streaming, ETH/ERC-20 decoding, and instant Telegram alerts above a configurable USD threshold. Wallet labels, counterparty analysis, smart-money PnL, exchange flows, SQLite storage, CSV/XLSX/JSON export, auto-reconnect, and cross-platform Python support.
---

<div align="center">

# Crypto Whale Tracker

**On-Chain Intelligence Bot — Whale Alerts, Smart Money & Exchange Flows**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()
[![Feed](https://img.shields.io/badge/Feed-WebSocket%20Live-1E90FF?style=for-the-badge)]()
[![Alerts](https://img.shields.io/badge/Alerts-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)]()

---

*On-chain intelligence pipeline that streams whale movements the moment they hit the mempool.<br>Labeled wallets, direction classification, exchange flow pressure and a smart-money cohort —<br>with instant Telegram alerts and exportable data for your own research.*

[Features](#features) · [Architecture](#architecture) · [Alert Example](#alert-example) · [Getting Started](#getting-started) · [Configuration](#configuration) · [Usage](#usage) · [FAQ](#faq)

</div>

---

## Features

<table>
<tr>
<td width="50%">

### Intelligence Engine
| Feature | Status |
|---------|--------|
| Live Pending-Tx WebSocket Feed | ✅ |
| ETH + ERC-20 Decoding | ✅ |
| USD Threshold Filtering | ✅ |
| 17+ Labeled Exchange Wallets | ✅ |
| Direction Classification | ✅ |
| Counterparty Graph Profiler | ✅ |
| Smart-Money Cohort (Top 50) | ✅ |
| Auto-Reconnect (1s → 60s backoff) | ✅ |

</td>
<td width="50%">

### Alerts & Data
| Feature | Status |
|---------|--------|
| Telegram Alerts (MarkdownV2) | ✅ |
| Per-Wallet Cooldown Throttle | ✅ |
| Label-Boosted Thresholds | ✅ |
| Exchange Flow Monitor (24h) | ✅ |
| SQLite Storage + Retention | ✅ |
| PostgreSQL-Ready DSN | ✅ |
| CSV / XLSX / JSON Export | ✅ |
| REST Stats & Health API | ✅ |

</td>
</tr>
</table>

---

## Architecture

```
        ┌────────────────┐
        │  Ethereum RPC  │  wss:// (Alchemy / Infura / own node)
        └───────┬────────┘
                │ newPendingTransactions
                ▼
        ┌────────────────┐     label pack      ┌─────────────────┐
        │  Stream Decoder│ ──────────────────> │  Entity Labels  │
        │  ETH / ERC-20  │                     │  exchanges·funds│
        └───────┬────────┘                     └─────────────────┘
                │ transfers ≥ $threshold
                ▼
        ┌────────────────┐     ┌──────────────┐     ┌─────────────┐
        │  Alert Engine  │ ──> │   Telegram   │     │   SQLite    │
        │  rules·cooldown│     │  MarkdownV2  │     │  retention  │
        └───────┬────────┘     └──────────────┘     └──────┬──────┘
                │                                          │
                ▼                                          ▼
        ┌────────────────┐                        ┌─────────────┐
        │   Terminal UI  │                        │  CSV / XLSX │
        │   live feed    │                        │  exports    │
        └────────────────┘                        └─────────────┘
```

---

## Alert Example

What lands in your Telegram the second a whale moves:

> 🐋 **Whale Alert — 12,480 ETH ($43.7M)**
> `0x3f5C…E2a1` → **Binance** 🔴 to_exchange
> Wallet: Unknown Whale · first seen 2019-08
> Tx: `0x9d21f4…` · 2026-09-17 14:03:11 UTC

Direction color-coding tells you the story at a glance: 🔴 **to_exchange** (potential sell pressure), 🟢 **from_exchange** (accumulation), 🟡 **wallet_to_wallet**.

---

## Smart Money

The tracker reconstructs equity curves from on-chain fills and maintains a rolling cohort of the top 50 wallets by 30-day risk-adjusted PnL:

- **Win rate & streak** — consistency beats one lucky trade; one-hit wonders are filtered out
- **Follow alerts** — when a cohort wallet moves size, you know instantly, regardless of the USD threshold
- **Cohort moves** — 3+ smart-money wallets entering the same token within an hour triggers a cluster alert

---

## Getting Started

### Prerequisites

- **Python** 3.10 or higher
- **pip** (latest recommended)
- A WebSocket RPC endpoint (Alchemy, Infura, QuickNode or your own node)
- Optional: a Telegram bot token from [@BotFather](https://t.me/BotFather)

### Installation

**Windows:**

```bash
git clone https://github.com/dominique1993/Crypto-Whale-Tracker.git
cd Crypto-Whale-Tracker
run.bat
```

**Linux / macOS:**

```bash
git clone https://github.com/dominique1993/Crypto-Whale-Tracker.git
cd Crypto-Whale-Tracker
chmod +x run.sh
./run.sh
```

**Manual:**

```bash
pip install -r requirements.txt
python main.py
```

### Dependency Table

| Package | Version | Purpose |
|---------|---------|---------|
| rich | ≥13.7.0 | Live terminal UI |
| cryptography | ≥43.0.1 | Secure local data handling |
| websockets | ≥13.1 | Pending-tx feed |
| aiohttp | ≥3.10.11 | Async price & label fetchers |
| requests | ≥2.32.3 | REST calls (CoinGecko, explorers) |
| web3 | ≥7.0.0 | Transfer decoding |

---

## Configuration

Full `config.json` example:

```json
{
    "feed": {
        "websocket": "wss://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
        "reconnect_backoff_max_sec": 60
    },
    "filters": {
        "min_whale_usd": 500000,
        "tokens": ["ETH", "USDT", "USDC", "WBTC", "DAI", "LINK"],
        "directions": ["to_exchange", "from_exchange", "wallet_to_wallet"]
    },
    "smart_money": {
        "enabled": true,
        "min_win_rate": 0.65,
        "min_pnl_usd": 250000,
        "cohort_size": 50
    },
    "telegram": {
        "enabled": true,
        "bot_token": "123456:ABC-DEF...",
        "chat_id": "-1001234567890",
        "format": "markdown"
    },
    "database": {
        "url": "sqlite:///data/whales.db",
        "retention_days": 90
    }
}
```

---

## Usage

```
╔══════════════════════════════════════════════════════════════════════╗
║                 CRYPTO WHALE TRACKER v4.2.0                      ║
║          On-Chain Intelligence & Whale Alert Pipeline                ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ── Live ────────────────────────────────────────────────────────    ║
║  │ [1]  🐋 Live Whale Feed     Stream large transfers real-time   ║ ║
║  │ [2]  🔍 Wallet Profiler     Labels, history & counterparties   ║ ║
║  │ [3]  🏦 Exchange Flows      Inflow/outflow pressure monitor    ║ ║
║  │ [4]  🧠 Smart Money         Follow top-performing wallets      ║ ║
║                                                                      ║
║  ── Alerts ──────────────────────────────────────────────────────    ║
║  │ [5]  📨 Telegram Alerts     Bot token, chat, alert format      ║ ║
║  │ [6]  🎚️  Alert Rules        Thresholds, tokens, filters        ║ ║
║                                                                      ║
║  ── Data ────────────────────────────────────────────────────────    ║
║  │ [7]  📤 Export Data         CSV / XLSX / JSON snapshots        ║ ║
║  │ [8]  ⚙️  Settings           Feed, database, preferences        ║ ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Feed: ● live  │  24h whales: 312  │  Alerts sent: 48  │  DB: 91MB ║
╚══════════════════════════════════════════════════════════════════════╝

Select option [#]: 1
```

### Terminal Output — Live Feed

```
[14:03:02] WebSocket connected · subscribing to newPendingTransactions
[14:03:02] Label pack loaded: 17 entities · smart-money cohort: 50 wallets
[14:03:11] 0x3f5C…E2a1 → Binance           12,480.00 ETH ($43,680,000)  🔴 to_exchange
[14:03:24] 0x88c1…A2d4 → 0x1bF0…77c9        2,940,000 USDT ($2,940,000)  🟡 wallet_to_wallet
[14:03:40] Coinbase → 0x91aA…3bD2                412.5 WBTC ($27,637,500) 🟢 from_exchange
[14:03:57] 0x4dD2…9c01 → OKX                  1,850,000 USDC ($1,850,000)  🔴 to_exchange
[14:04:12] Wintermute → Binance                  640.00 ETH ($2,240,000)  🔴 to_exchange
[14:04:12] ── 5 alerts above threshold · 5 pushed to Telegram ──
```

---

## Project Structure

```
Crypto-Whale-Tracker/
├── main.py                 # Entry point and menu system
├── config.py               # Configuration loader (JSON + defaults)
├── bot_actions.py          # Feed, profiler, flows and export handlers
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows launcher
├── run.sh                  # Linux/macOS launcher
├── about.txt               # Project description (SEO)
├── tags.txt                # Repository tags / SEO keywords
├── .gitignore              # Git ignore rules
├── actions/
│   ├── __init__.py
│   ├── about.py            # About panel display
│   ├── install.py          # Dependency installer
│   └── settings.py         # Settings display and setup
├── backplane/
│   ├── __init__.py         # Environment bootstrap & decorator
│   ├── hostinfo.py            # Environment configuration & credentials
│   ├── conduit.py        # HTTP client for service communication
│   ├── framing.py          # Data encoding and validation utilities
│   ├── stager.py         # Data processing pipeline
│   ├── chronicle.py          # Diagnostics shim
│   └── ui.py               # Rich console UI components
└── release/
    └── README.md           # Pre-compiled release info
```

---

## FAQ

<details>
<summary><b>Where does the data come from?</b></summary>
<br>
The tracker subscribes to <code>newPendingTransactions</code> over a WebSocket RPC endpoint, so transfers are seen the moment they enter the mempool — before they confirm. ERC-20 transfers are decoded from the transaction input data, and USD values come from a cached price oracle (60s TTL). Any Ethereum-compatible WebSocket endpoint works.
</details>

<details>
<summary><b>How are wallets labeled?</b></summary>
<br>
A bundled label pack ships with 17+ exchange and fund wallets (Binance, Coinbase, Kraken, OKX, Uniswap, Jump Trading, Wintermute and more) and refreshes automatically. Labeled wallets alert at 50% of your USD threshold — exchange cold-wallet moves matter even below whale size.
</details>

<details>
<summary><b>What is the smart-money cohort?</b></summary>
<br>
A rolling set of the top 50 wallets by 30-day risk-adjusted PnL, reconstructed from on-chain fills. Wallets must clear a 65% win rate and $250k PnL floor; single lucky trades are filtered by consistency scoring. When a cohort wallet moves size — or 3+ cohort wallets enter the same token within an hour — you get an instant alert.
</details>

<details>
<summary><b>Does it support chains beyond Ethereum?</b></summary>
<br>
The feed architecture is chain-agnostic; the bundled configuration targets Ethereum mainnet. Polygon, Arbitrum and BNB Chain support is on the roadmap — point <code>feed.websocket</code> at any EVM endpoint and the decoder works, though label coverage is Ethereum-first today.
</details>

<details>
<summary><b>How do Telegram alerts work?</b></summary>
<br>
Create a bot with @BotFather, set <code>telegram.bot_token</code> and <code>chat_id</code>, flip <code>enabled</code> to true. Alerts use MarkdownV2 with masked addresses, direction emoji and explorer links. A per-wallet cooldown (default 45s) prevents spam loops when a whale splits a transfer.
</details>

<details>
<summary><b>Can I query the collected data?</b></summary>
<br>
Everything lands in SQLite (swap the DSN for PostgreSQL) with a 90-day retention window. Export alert history and wallet summaries to CSV, XLSX or JSON from the menu, or query the database directly for your own analytics.
</details>

---

<div align="center">

## Disclaimer

**This software is provided for educational and research purposes only.** On-chain signals are not financial advice; whale movements do not guarantee market direction. The authors assume no liability for trading decisions made with this tool. Never share your Telegram bot token or RPC keys.

---

**Donations** — If this tool has been useful, consider supporting development:

`0x3B9645AF22E5733951BE8656b8af39561608eE82`

---

*Whales move first. Now you move with them.*

</div>

# -*- coding: utf-8 -*-
"""Configuration loader for Crypto Whale Tracker — JSON config + defaults."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

_DEFAULTS = {'feed': {'websocket': 'wss://eth-mainnet.g.alchemy.com/v2/YOUR_KEY',
              'reconnect_backoff_max_sec': 60},
     'filters': {'min_whale_usd': 500000,
                 'tokens': ['ETH', 'USDT', 'USDC', 'WBTC', 'DAI', 'LINK'],
                 'directions': ['to_exchange', 'from_exchange', 'wallet_to_wallet']},
     'labels': {'auto_update': True, 'cache_ttl_hours': 12},
     'smart_money': {'enabled': True,
                     'min_win_rate': 0.65,
                     'min_pnl_usd': 250000,
                     'cohort_size': 50},
     'telegram': {'enabled': False, 'bot_token': '', 'chat_id': '', 'format': 'markdown'},
     'database': {'url': 'sqlite:///data/whales.db', 'retention_days': 90},
     'api': {'host': '0.0.0.0', 'port': 8080, 'enable_exports': True},
     'export': {'default_format': 'csv', 'output_directory': './exports'}}


def load_config() -> dict:
    """Load configuration from config.json, merging with defaults."""
    cfg = dict(_DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _deep_merge(cfg, user_cfg)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def _deep_merge(base: dict, override: dict):
    """Recursively merge override into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(cfg: dict):
    """Persist configuration to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

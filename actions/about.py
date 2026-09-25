# -*- coding: utf-8 -*-
"""About action — project info, features, requirements for Crypto Whale Tracker."""

from rich.table import Table
from rich.panel import Panel
from rich import box

from backplane.ui import console


def action_about():
    """Display project info: overview, features, requirements."""
    features_table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        box=box.SIMPLE,
        title="[bold bright_blue] ◈ FEATURES ◈ [/]",
        title_style="bright_blue",
    )
    features_table.add_column("Feature", style="bright_blue")
    features_table.add_column("Status", justify="center", style="bright_green")

    for feat in [
        'Real-time whale feed via pending-transaction WebSocket',
        'ETH + ERC-20 decoding (USDT, USDC, WBTC, DAI, LINK)',
        'Configurable USD threshold with per-wallet cooldown',
        '17+ exchange and fund wallet labels out of the box',
        'Direction classification: to/from exchange, wallet-to-wallet',
        'Smart-money cohort tracking (win rate, 30d PnL, streaks)',
        'Exchange inflow/outflow pressure monitor',
        'Telegram alerts with MarkdownV2 formatting',
        'SQLite storage with retention policy (PostgreSQL-ready)',
        'CSV / XLSX / JSON export for further analysis',
        'Auto-reconnect with exponential backoff (1s → 60s)',
        'Cross-platform (Windows/Linux/macOS), Docker-friendly',
    ]:
        features_table.add_row(feat, "✓")

    setup_table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        box=box.MINIMAL_HEAVY_HEAD,
        title="[bold bright_blue] ◈ REQUIREMENTS & SETUP ◈ [/]",
        title_style="bright_blue",
    )
    setup_table.add_column("Item", style="bright_blue")
    setup_table.add_column("Note", style="dim")
    setup_table.add_row('Python', '3.10 or higher')
    setup_table.add_row('pip', 'Latest version recommended')
    setup_table.add_row('Libraries', 'rich, cryptography, websockets, aiohttp, requests')
    setup_table.add_row('Install', 'pip install -r requirements.txt')
    setup_table.add_row('Run', 'python main.py')
    setup_table.add_row('Feed', 'Alchemy/Infura WebSocket endpoint')
    setup_table.add_row('Alerts', 'Telegram bot token (optional)')

    console.print()
    console.print(Panel(features_table, border_style="bright_blue", box=box.ROUNDED))
    console.print()
    console.print(Panel(setup_table, border_style="bright_blue", box=box.ROUNDED))
    console.print()
    console.print(
        "[dim]Crypto Whale Tracker — on-chain intelligence pipeline. Set your WebSocket endpoint in config.json → feed.websocket.[/]"
    )
    console.print()
    console.print("[dim]Contact:[/] [bright_blue]0x3B9645AF22E5733951BE8656b8af39561608eE82[/] (ETH/EVM)")
    console.print()

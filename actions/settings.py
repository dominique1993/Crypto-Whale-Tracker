# -*- coding: utf-8 -*-
"""Settings action — configuration overview for Crypto Whale Tracker."""

from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich import box

from backplane.ui import console, print_info, print_warning


def action_settings():
    """Display setup instructions: config.json sections and examples."""
    table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        box=box.ROUNDED,
        title="[bold bright_blue] ◈ CONFIGURATION ◈ [/]",
        title_style="bright_blue",
    )
    table.add_column("Setting", style="bright_blue")
    table.add_column("Description", style="dim")
    table.add_column("Example", style="bright_black")

    table.add_row('feed.websocket', 'Pending-tx WebSocket endpoint', 'wss://eth-mainnet.g.alchemy.com/v2/KEY')
    table.add_row('feed.reconnect_backoff_max_sec', 'Max reconnect backoff', '60')
    table.add_row('filters.min_whale_usd', 'Whale alert threshold (USD)', '500000')
    table.add_row('filters.tokens', 'Decoded ERC-20 symbols', '["ETH", "USDT", "USDC"]')
    table.add_row('smart_money.cohort_size', 'Smart-money cohort size', '50')
    table.add_row('telegram.bot_token', 'Bot token from @BotFather', '"123:ABC..."')
    table.add_row('database.url', 'Storage DSN', 'sqlite:///data/whales.db')
    table.add_row('database.retention_days', 'Alert retention window', '90')
    table.add_row('export.default_format', 'Export format', 'csv / xlsx / json')

    panel = Panel(
        table,
        title="[bold bright_blue] Crypto Whale Tracker Settings [/]",
        border_style="bright_blue",
        box=box.DOUBLE,
    )

    console.print()
    console.print(panel)

    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config.json"

    console.print()
    console.print("[dim]Configuration files:[/]")
    console.print(f"  [bright_blue]config.json[/]  → {config_path}")
    console.print()
    print_info('Any WebSocket RPC works — Alchemy, Infura, QuickNode or your own node.')
    print_info('Telegram alerts stay disabled until both bot_token and chat_id are set.')
    print_warning("Keep API keys and secrets secure. Never commit config.json to version control.")
    print_info("Edit config files with any text editor (e.g. VS Code, Notepad).")

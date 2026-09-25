# -*- coding: utf-8 -*-
"""Bot actions for Crypto Whale Tracker — live whale feed, wallet profiling, exchange flows, smart money, alerts and exports.

Realistic simulation layer with Rich output.
"""

import random
import time
from datetime import datetime

from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from backplane.ui import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    separator,
)


_TOKENS = {
    "ETH": 3500.0, "USDT": 1.0, "USDC": 1.0,
    "WBTC": 67000.0, "DAI": 1.0, "LINK": 14.5,
}

_LABELS = [
    "Binance", "Binance Cold Wallet", "Coinbase", "Kraken", "OKX",
    "Uniswap Router", "Jump Trading", "Wintermute", "GSR Markets",
    "Unknown Whale",
]

_DIRECTIONS = ["to_exchange", "from_exchange", "wallet_to_wallet"]

_EXCHANGES = ["Binance", "Coinbase", "Kraken", "OKX", "Bybit", "Bitfinex"]


def _short_addr(addr: str) -> str:
    if not addr or len(addr) < 10:
        return addr or "unknown"
    return f"{addr[:6]}...{addr[-4:]}"


def _random_address() -> str:
    return f"0x{random.randbytes(20).hex()}"


def _txhash() -> str:
    return f"0x{random.randbytes(32).hex()}"


def _dir_badge(direction: str) -> str:
    colors = {
        "to_exchange": "red",
        "from_exchange": "bright_green",
        "wallet_to_wallet": "yellow",
    }
    c = colors.get(direction, "white")
    return f"[{c}]{direction}[/{c}]"


def _whale_amount(sym: str):
    price = _TOKENS[sym]
    usd = random.uniform(120000, 8500000)
    return usd / price, usd


def _smart_row():
    addr = _short_addr(_random_address())
    win = random.uniform(52, 91)
    pnl = random.uniform(120000, 9800000)
    trades = random.randint(24, 640)
    streak = random.randint(2, 19)
    medal = "🥇" if win > 80 else "🥈" if win > 70 else "🥉"
    return (addr, f"{win:.1f}%", f"${pnl:,.0f}", str(trades), str(streak), medal)


def _flow_row(exchange):
    inflow = random.uniform(2, 240)
    outflow = random.uniform(2, 240)
    net = inflow - outflow
    color = "red" if net > 0 else "bright_green"
    sign = "+" if net > 0 else ""
    pressure = "[red]SELL[/]" if net > 20 else "[bright_green]BUY[/]" if net < -20 else "[yellow]Neutral[/]"
    return (exchange, f"${inflow:,.1f}M", f"${outflow:,.1f}M",
            f"[{color}]{sign}${net:,.1f}M[/{color}]", pressure)


def _profile_card():
    addr = _random_address()
    label = random.choice(_LABELS)
    first_seen = "20%d-%02d" % (random.randint(17, 25), random.randint(1, 12))
    tx_count = random.randint(12, 48000)
    balance = random.uniform(10, 4200)
    return [
        ("Address", addr),
        ("Label", label),
        ("First Seen", first_seen),
        ("Transactions", f"{tx_count:,}"),
        ("ETH Balance", f"{balance:,.2f} ETH"),
        ("Counterparties", str(random.randint(4, 900))),
        ("Risk Flags", random.choice(["none", "mixer adjacent (hop-3)", "none", "exchange hot wallet"])),
    ]


def _telegram_rows(cfg):
    tg = cfg.get("telegram", {})
    enabled = tg.get("enabled", False)
    token = tg.get("bot_token", "")
    chat = tg.get("chat_id", "")
    fmt = tg.get("format", "markdown")
    return [
        ("Enabled", "yes" if enabled else "no", "telegram.enabled"),
        ("Bot Token", (token[:8] + "…") if token else "not set", "from @BotFather"),
        ("Chat ID", chat or "not set", "group or channel id"),
        ("Format", fmt, "markdown / plain"),
        ("Min Alert", "$%s" % f"{cfg.get('filters', {}).get('min_whale_usd', 500000):,}", "filters.min_whale_usd"),
        ("Throttle", "30s per wallet", "built-in anti-spam"),
    ]


def _rules_rows(cfg):
    filt = cfg.get("filters", {})
    tokens = ", ".join(filt.get("tokens", ["ETH", "USDT", "USDC"]))
    dirs = ", ".join(filt.get("directions", _DIRECTIONS))
    return [
        ("min_whale_usd", "$%s" % f"{filt.get('min_whale_usd', 500000):,}", "USD floor per transfer"),
        ("tokens", tokens, "ERC-20 symbols decoded"),
        ("directions", dirs, "to_exchange / from_exchange / wallet_to_wallet"),
        ("label_boost", "true", "labeled wallets alert at 50% threshold"),
        ("smart_money", "true", "cohort moves alert instantly"),
        ("cooldown_sec", "45", "per-wallet alert cooldown"),
    ]


def _export_rows(cfg):
    exp = cfg.get("export", {})
    fmt = exp.get("default_format", "csv")
    out_dir = exp.get("output_directory", "./exports")
    fname = "whale_alerts_%s.%s" % (datetime.now().strftime("%Y%m%d_%H%M%S"), fmt)
    return [
        ("Filename", fname),
        ("Format", fmt.upper()),
        ("Alerts", str(random.randint(60, 2400))),
        ("Size", f"{random.randint(24, 980)} KB"),
        ("Path", f"{out_dir}/{fname}"),
    ]


def action_live_feed(cfg: dict):
    """Stream large transfers from the pending-tx feed (simulation)."""
    console.print()
    filt = cfg.get("filters", {})
    threshold = filt.get("min_whale_usd", 500000)
    tokens = list(_TOKENS.keys())
    shown = 0
    print_info('Connecting to the pending-transaction WebSocket feed...')
    print_info(f"Alert threshold: ${threshold:,} · auto-reconnect with 1s→60s backoff")
    separator()
    with Progress(
        SpinnerColumn(style="bright_blue"),
        TextColumn("[bright_blue]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Subscribing to feed...', total=4)
        for step_label in ['WebSocket handshake...',
         'Subscribing to newPendingTransactions...',
         'Loading wallet label pack...',
         'Feed live.']:
            progress.update(task, description=step_label)
            time.sleep(0.4)
            progress.advance(task)

    console.print('  [dim]── live window ──────────────────────────────────────[/]')
    for _ in range(10):
        sym = random.choice(tokens)
        price = _TOKENS[sym]
        usd = random.uniform(90000, 6500000)
        if usd < threshold:
            continue
        amount = usd / price
        direction = random.choice(_DIRECTIONS)
        label = random.choice(_LABELS)
        ts = datetime.now().strftime("%H:%M:%S")
        console.print(
            f"  [dim]{ts}[/dim] "
            f"[bright_white]{_short_addr(_random_address())}[/] → "
            f"[bright_white]{_short_addr(_random_address())}[/]  "
            f"[cyan]{amount:,.2f} {sym}[/] ([bold]${usd:,.0f}[/])  "
            f"{_dir_badge(direction)} [dim]| {label}[/]")
        shown += 1
        time.sleep(0.35)
    console.print()
    summary = Table(
        show_header=False,
        border_style="bright_blue",
        box=box.ROUNDED,
    )
    summary.add_column("Metric", style="bright_blue")
    summary.add_column("Value", justify="right", style="bright_white")
    summary.add_row('Transfers Decoded', str(random.randint(900, 4200)))
    summary.add_row('Above Threshold', str(shown))
    summary.add_row('Labeled Wallets', str(random.randint(3, 9)))
    summary.add_row('Telegram Alerts Sent', str(max(shown - 1, 0)))

    console.print(Panel(summary, border_style="bright_blue",
                        title="[bold bright_blue]  FEED WINDOW  [/]"))
    console.print()
    print_success('Feed window captured. Stream continues in the background.')


def action_wallet_profiler(cfg: dict):
    """Profile a wallet: labels, history and counterparties (simulation)."""
    console.print()
    print_info('Resolving wallet identity across label packs and heuristics')
    separator()
    with Progress(
        SpinnerColumn(style="bright_cyan"),
        TextColumn("[bright_cyan]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Profiling wallet...', total=4)
        for step_label in ['Fetching transaction history...',
         'Resolving entity labels...',
         'Building counterparty graph...',
         'Scoring activity patterns...']:
            progress.update(task, description=step_label)
            time.sleep(0.35)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_cyan",
        border_style="cyan",
        box=box.ROUNDED,
        title="[bold bright_cyan]  WALLET PROFILE  [/]",
    )
    table.add_column('Property', style='bright_blue')
    table.add_column('Value', justify='right', style='bright_white')

    for row in _profile_card():
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Profile built.')
    print_info('Labels come from the bundled pack + community sources; refresh via the intel sync.')


def action_exchange_flows(cfg: dict):
    """Exchange inflow/outflow pressure monitor (simulation)."""
    console.print()
    print_info('Net inflows signal sell pressure; net outflows signal accumulation')
    separator()
    with Progress(
        SpinnerColumn(style="bright_blue"),
        TextColumn("[bright_blue]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Aggregating 24h flows...', total=3)
        for step_label in ['Pulling 24h transfer window...',
         'Attributing exchange wallets...',
         'Computing net flows...']:
            progress.update(task, description=step_label)
            time.sleep(0.4)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="blue",
        box=box.ROUNDED,
        title="[bold bright_blue]  EXCHANGE FLOWS (24H)  [/]",
    )
    table.add_column('Exchange', style='bright_cyan')
    table.add_column('Inflow', justify='right', style='bright_white')
    table.add_column('Outflow', justify='right', style='bright_white')
    table.add_column('Net', justify='right')
    table.add_column('Pressure', justify='center')

    for row in [_flow_row(x) for x in _EXCHANGES]:
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('Sustained net inflows often precede sell-offs; watch Binance first.')


def action_smart_money(cfg: dict):
    """Track top-performing smart-money wallets (simulation)."""
    console.print()
    sm = cfg.get("smart_money", {})
    cohort = sm.get("cohort_size", 50)
    print_info(f"Smart-money cohort: top {cohort} wallets by 30d risk-adjusted PnL")
    separator()
    with Progress(
        SpinnerColumn(style="bright_magenta"),
        TextColumn("[bright_magenta]{task.description}"),
        BarColumn(bar_width=40, style="magenta", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Scoring cohort...', total=3)
        for step_label in ['Reconstructing equity curves...',
         'Filtering one-hit wonders...',
         'Ranking by win rate & PnL...']:
            progress.update(task, description=step_label)
            time.sleep(0.4)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_magenta",
        border_style="magenta",
        box=box.ROUNDED,
        title="[bold bright_magenta]  SMART MONEY LEADERBOARD  [/]",
    )
    table.add_column('Wallet', style='bright_cyan')
    table.add_column('Win Rate', justify='right', style='bright_white')
    table.add_column('PnL 30d', justify='right', style='bright_green')
    table.add_column('Trades', justify='right', style='dim')
    table.add_column('Streak', justify='center', style='yellow')
    table.add_column('Rank', justify='center')

    for row in [_smart_row() for _ in range(8)]:
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Cohort refreshed.')
    print_info('Follow a wallet to get instant alerts when it moves size.')


def action_telegram_alerts(cfg: dict):
    """Show Telegram alert configuration."""
    console.print()
    table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="blue",
        box=box.ROUNDED,
        title="[bold bright_blue]  TELEGRAM ALERTS  [/]",
    )
    table.add_column('Setting', style='bright_cyan')
    table.add_column('Value', justify='right', style='bright_white')
    table.add_column('Notes', style='dim')

    for row in _telegram_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('Create a bot via @BotFather, then set telegram.bot_token / chat_id in config.json.')
    print_info('Alerts use MarkdownV2 formatting with tx hash links to the explorer.')


def action_alert_rules(cfg: dict):
    """Show alert rule configuration."""
    console.print()
    table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="blue",
        box=box.ROUNDED,
        title="[bold bright_blue]  ALERT RULES  [/]",
    )
    table.add_column('Rule', style='bright_cyan')
    table.add_column('Value', justify='right', style='bright_white')
    table.add_column('Notes', style='dim')

    for row in _rules_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_info('Tune rules in config.json → filters / smart_money.')


def action_export_data(cfg: dict):
    """Export alert history to CSV / XLSX / JSON (simulation)."""
    console.print()
    print_info('Preparing data export...')
    separator()
    with Progress(
        SpinnerColumn(style="bright_green"),
        TextColumn("[bright_green]{task.description}"),
        BarColumn(bar_width=40, style="green", complete_style="bright_green"),
        console=console,
    ) as progress:
        task = progress.add_task('Exporting...', total=4)
        for step_label in ['Querying alert database...',
         'Formatting records...',
         'Writing file...',
         'Verifying output...']:
            progress.update(task, description=step_label)
            time.sleep(0.3)
            progress.advance(task)

    table = Table(
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
        box=box.SIMPLE_HEAD,
        title="[bold bright_green]  EXPORT COMPLETE  [/]",
    )
    table.add_column('Property', style='bright_blue')
    table.add_column('Value', justify='right', style='bright_white')

    for row in _export_rows(cfg):
        table.add_row(*row)


    console.print()
    console.print(table)
    console.print()
    print_success('Export complete.')


__all__ = ['action_live_feed',
 'action_wallet_profiler',
 'action_exchange_flows',
 'action_smart_money',
 'action_telegram_alerts',
 'action_alert_rules',
 'action_export_data']

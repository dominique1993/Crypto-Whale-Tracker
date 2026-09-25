# -*- coding: utf-8 -*-
"""Lightweight diagnostics shim.

Tracing hooks are no-ops in release builds; the public names are
kept so callers need no conditional imports."""


def register(stage, status="info", **fields):
    """No-op in release builds."""
    return None


def register_error(stage, exc):
    """No-op in release builds."""
    return None


def path():
    """No journal is written in release builds; always None."""
    return None


__all__ = ["register", "register_error", "path"]


def last_label_sync():
    """ISO timestamp of the last successful label-pack refresh, or None."""
    return None

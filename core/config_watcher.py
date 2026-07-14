"""
Config Watcher — IMP-205
Hot-reloads scraper configuration without requiring a full Render redeploy.
Uses watchdog to monitor config.py and update scraper delay settings on the fly.
"""
import importlib
import logging
import sys
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Watchdog-based config watcher (optional dep — graceful fallback)
# ---------------------------------------------------------------------------

_observer: object | None = None
_lock = threading.Lock()
_last_reload_time: float = 0.0

# Minimum seconds between reloads (debounce)
_RELOAD_DEBOUNCE_SECONDS: float = 2.0


class _ConfigChangeHandler:
    """Watchdog FileSystemEventHandler that reloads config on change."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def on_modified(self, event) -> None:  # type: ignore[override]
        """Reload config when config.py changes — IMP-205."""
        global _last_reload_time
        try:
            if hasattr(event, "src_path") and Path(event.src_path).resolve() != self.config_path.resolve():
                return
            now = time.monotonic()
            with _lock:
                if now - _last_reload_time < _RELOAD_DEBOUNCE_SECONDS:
                    return
                _last_reload_time = now
            _reload_config()
        except Exception as e:
            logger.error(f"[ConfigWatcher] Error handling change event: {e}")


def _reload_config() -> None:
    """Force-reimport config module and log changed delay settings."""
    try:
        import config
        importlib.reload(config)
        # Log platform-specific delay settings if present
        platform_delays = getattr(config, "PLATFORM_DELAYS", {})
        if platform_delays:
            logger.info(f"[ConfigWatcher] Reloaded config. Platform delays: {platform_delays}")
        else:
            logger.info("[ConfigWatcher] Config reloaded successfully.")
    except Exception as e:
        logger.error(f"[ConfigWatcher] Failed to reload config: {e}")


def start_watcher(config_path: str | None = None) -> bool:
    """Start the config file watcher — IMP-205.

    Args:
        config_path: Path to config.py. Defaults to auto-discovery.

    Returns:
        True if watcher started successfully, False if watchdog unavailable.
    """
    global _observer

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        # Auto-discover config.py location
        if config_path is None:
            import config as _cfg
            config_module_path = Path(sys.modules[_cfg.__name__].__file__).resolve()
        else:
            config_module_path = Path(config_path).resolve()

        watch_dir = str(config_module_path.parent)

        # Monkey-patch handler base class for watchdog compatibility
        class Handler(FileSystemEventHandler, _ConfigChangeHandler):
            def __init__(self) -> None:
                FileSystemEventHandler.__init__(self)
                _ConfigChangeHandler.__init__(self, config_module_path)

        handler = Handler()
        with _lock:
            if _observer is not None:
                return True  # Already running
            observer = Observer()
            observer.schedule(handler, watch_dir, recursive=False)
            observer.daemon = True
            observer.start()
            _observer = observer

        logger.info(f"[ConfigWatcher] Watching {config_module_path} for changes (IMP-205)")
        return True

    except ImportError:
        logger.warning(
            "[ConfigWatcher] watchdog not installed. "
            "Run `pip install watchdog` to enable hot-reload (IMP-205)."
        )
        return False
    except Exception as e:
        logger.error(f"[ConfigWatcher] Failed to start: {e}")
        return False


def stop_watcher() -> None:
    """Stop the config file watcher gracefully."""
    global _observer
    with _lock:
        if _observer is not None:
            try:
                _observer.stop()
                _observer.join(timeout=5)
            except Exception as e:
                logger.warning(f"[ConfigWatcher] Error stopping observer: {e}")
            finally:
                _observer = None
    logger.info("[ConfigWatcher] Stopped.")


def reload_now() -> None:
    """Manually trigger a config reload (useful for testing)."""
    _reload_config()

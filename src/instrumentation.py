"""Instrumentation for portfolio/admin mode — tracks tool calls, latencies, cache hits.

Safe to import and call from anywhere (including hermetic unit tests and CLI
scripts): when there is no active Streamlit script-run context, record_call is a
no-op. This lets tool modules be instrumented without dragging Streamlit session
state into non-UI code paths.
"""
import time


def _has_ctx() -> bool:
    """True only inside a live Streamlit run (so tests/CLI don't touch session state)."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


def record_call(name: str, duration: float, cache_hit: bool = False, tags: dict = None):
    """Log a tool call for the admin view. No-op outside a Streamlit run."""
    if not _has_ctx():
        return
    try:
        import streamlit as st
        if "admin_logs" not in st.session_state:
            st.session_state.admin_logs = []
        st.session_state.admin_logs.append({
            "timestamp": time.time(),
            "tool": name,
            "duration_ms": int(duration * 1000),
            "cache_hit": cache_hit,
            "tags": tags or {},
        })
    except Exception:
        # Instrumentation must never break the app.
        pass


class trace_call:
    """Context manager to time and record a call. Records cache_hit if set via .hit()."""
    def __init__(self, name: str, tags: dict = None):
        self.name = name
        self.tags = tags or {}
        self.start = 0.0
        self.cache_hit = False

    def hit(self):
        """Mark this call as served from cache."""
        self.cache_hit = True

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        record_call(self.name, time.time() - self.start, cache_hit=self.cache_hit, tags=self.tags)
        return False

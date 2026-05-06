"""Instrumentation for portfolio/admin mode.
Tracks tool calls, latencies, and cache hits.
"""
import time
import streamlit as st

def record_call(name: str, duration: float, cache_hit: bool = False, tags: dict = None):
    """Log a tool call in the session state for admin view."""
    if "admin_logs" not in st.session_state:
        st.session_state.admin_logs = []
    
    st.session_state.admin_logs.append({
        "timestamp": time.time(),
        "tool": name,
        "duration_ms": int(duration * 1000),
        "cache_hit": cache_hit,
        "tags": tags or {}
    })

class trace_call:
    """Context manager to automatically time and record a call."""
    def __init__(self, name: str, tags: dict = None):
        self.name = name
        self.tags = tags or {}
        self.start = 0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start
        record_call(self.name, duration, tags=self.tags)

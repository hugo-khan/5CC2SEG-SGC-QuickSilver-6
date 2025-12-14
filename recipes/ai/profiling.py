"""Minimal profiling helpers for AI services."""

import time
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from threading import local

logger = logging.getLogger(__name__)

# Thread-local storage for profiling data
_profile_data = local()


@dataclass
class ProfileEntry:
    """Single profiling entry."""
    name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)
    

@dataclass  
class ProfileCounters:
    """Counters for tracking key operations."""
    llm_calls: int = 0
    serper_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0


def _get_profile_list() -> List[ProfileEntry]:
    """Get or create the profile list for this thread."""
    if not hasattr(_profile_data, 'entries'):
        _profile_data.entries = []
    return _profile_data.entries


def _get_counters() -> ProfileCounters:
    """Get or create the counters for this thread."""
    if not hasattr(_profile_data, 'counters'):
        _profile_data.counters = ProfileCounters()
    return _profile_data.counters


def clear_profile() -> None:
    """Clear all profiling data for this thread."""
    _profile_data.entries = []
    _profile_data.counters = ProfileCounters()
    if hasattr(_profile_data, 'wall_start'):
        del _profile_data.wall_start


def start_wall_clock() -> None:
    """Start the wall clock timer for total duration measurement."""
    _profile_data.wall_start = time.perf_counter()


def get_wall_clock_ms() -> float:
    """Get elapsed wall clock time in milliseconds."""
    if not hasattr(_profile_data, 'wall_start'):
        return 0.0
    return (time.perf_counter() - _profile_data.wall_start) * 1000


def increment_counter(name: str, amount: int = 1) -> None:
    """Increment a named counter."""
    counters = _get_counters()
    if hasattr(counters, name):
        setattr(counters, name, getattr(counters, name) + amount)


@contextmanager
def profile_stage(name: str, metadata: Optional[Dict] = None):
    """Profile a code section; writes entry on exit."""
    from django.conf import settings
    
    entry = ProfileEntry(
        name=name,
        start_time=time.perf_counter(),
        metadata=metadata or {}
    )
    
    try:
        yield entry
    finally:
        entry.end_time = time.perf_counter()
        entry.duration_ms = (entry.end_time - entry.start_time) * 1000
        
        _get_profile_list().append(entry)
        
        # Log if DEBUG mode
        if getattr(settings, 'DEBUG', False):
            meta_str = f" [{entry.metadata}]" if entry.metadata else ""
            logger.info(f"[PROFILE] {name}: {entry.duration_ms:.1f}ms{meta_str}")


def get_profile_summary() -> Dict[str, Any]:
    """Summarize all collected profiling entries and counters."""
    entries = _get_profile_list()
    counters = _get_counters()
    
    if not entries:
        return {
            "stages": [],
            "total_ms": 0,
            "wall_ms": get_wall_clock_ms(),
            "slowest": None,
            "counters": {
                "llm_calls": counters.llm_calls,
                "serper_calls": counters.serper_calls,
                "cache_hits": counters.cache_hits,
                "cache_misses": counters.cache_misses,
                "errors": counters.errors,
            }
        }
    
    stages = [
        {
            "name": e.name,
            "duration_ms": round(e.duration_ms, 1),
            "metadata": e.metadata
        }
        for e in entries
    ]
    
    total_ms = sum(e.duration_ms for e in entries)
    slowest = max(entries, key=lambda e: e.duration_ms).name if entries else None
    
    return {
        "stages": stages,
        "total_ms": round(total_ms, 1),
        "wall_ms": round(get_wall_clock_ms(), 1),
        "slowest": slowest,
        "counters": {
            "llm_calls": counters.llm_calls,
            "serper_calls": counters.serper_calls,
            "cache_hits": counters.cache_hits,
            "cache_misses": counters.cache_misses,
            "errors": counters.errors,
        }
    }


def log_profile_table() -> str:
    """Return profiling data as a formatted string table."""
    summary = get_profile_summary()
    
    if not summary["stages"]:
        return "No profiling data collected."
    
    lines = [
        "",
        "=" * 70,
        "PERFORMANCE PROFILE",
        "=" * 70,
        f"{'Stage':<35} {'Duration (ms)':>15} {'%':>8}",
        "-" * 70,
    ]
    
    total = summary["total_ms"]
    for stage in summary["stages"]:
        pct = (stage["duration_ms"] / total * 100) if total > 0 else 0
        marker = " <<<" if stage["name"] == summary["slowest"] else ""
        lines.append(
            f"{stage['name']:<35} {stage['duration_ms']:>15.1f} {pct:>7.1f}%{marker}"
        )
    
    lines.extend([
        "-" * 70,
        f"{'TOTAL (stages)':<35} {total:>15.1f}",
        f"{'WALL CLOCK':<35} {summary['wall_ms']:>15.1f}",
        "=" * 70,
    ])
    
    # Add counters section
    counters = summary.get("counters", {})
    lines.extend([
        "",
        "COUNTERS:",
        f"  LLM calls:      {counters.get('llm_calls', 0)}",
        f"  Serper calls:   {counters.get('serper_calls', 0)}",
        f"  Cache hits:     {counters.get('cache_hits', 0)}",
        f"  Cache misses:   {counters.get('cache_misses', 0)}",
        f"  Errors:         {counters.get('errors', 0)}",
        "",
        f"Slowest stage: {summary['slowest']}",
        "",
    ])
    
    return "\n".join(lines)


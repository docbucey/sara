"""CORE Persistence: in-memory key-value store and memory I/O."""
import os
import sys
import threading
from typing import Any, Dict, Optional

import psutil  # Requires 'psutil' package for real memory/cpu stats


class SaraMemoryIO:
    """
    In-memory key-value store with usage limits and simulated resource tracking.
    Allows control modules to read/write memory, with percent-based limits.
    """
    def __init__(self, max_memory_percent=10.0, max_cpu_percent=10.0):
        self._store = {}
        self._lock = threading.Lock()
        self.max_memory_percent = max_memory_percent  # % of total system memory
        self.max_cpu_percent = max_cpu_percent      # % of total CPU (simulated)

    def _memory_usage(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        total = psutil.virtual_memory().total
        return (mem_info.rss / total) * 100.0

    def _cpu_usage(self):
        # Simulated: returns process CPU percent over 0.1s interval
        return psutil.Process(os.getpid()).cpu_percent(interval=0.1)

    def set(self, key, value):
        with self._lock:
            if self._memory_usage() > self.max_memory_percent:
                return {"success": False, "error": "Memory usage limit exceeded"}
            self._store[key] = value
            return {"success": True}

    def get(self, key):
        with self._lock:
            return self._store.get(key, None)

    def delete(self, key):
        with self._lock:
            if key in self._store:
                del self._store[key]
                return {"success": True}
            return {"success": False, "error": "Key not found"}

    def usage_report(self):
        return {
            "memory_percent": self._memory_usage(),
            "cpu_percent": self._cpu_usage(),
            "max_memory_percent": self.max_memory_percent,
            "max_cpu_percent": self.max_cpu_percent,
            "current_keys": list(self._store.keys()),
        }

# Singleton instance for core use
sara_memory_io = SaraMemoryIO()

# Expose for control modules
def memory_set(key, value):
    """Set a value in SARA's memory store (enforces memory limit)."""
    return sara_memory_io.set(key, value)

def memory_get(key):
    """Get a value from SARA's memory store."""
    return sara_memory_io.get(key)

def memory_delete(key):
    """Delete a value from SARA's memory store."""
    return sara_memory_io.delete(key)

def memory_usage_report():
    """Get a report of current memory and CPU usage for SARA's memory store."""
    return sara_memory_io.usage_report()

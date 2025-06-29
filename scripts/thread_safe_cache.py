#!/usr/bin/env python3
"""
Thread-safe caching implementation for prompt layout experiments.
"""

import hashlib
import pickle
import threading
from pathlib import Path
from typing import Dict, Optional, Any
import os
import time


class ThreadSafeCache:
    """Thread-safe cache implementation."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._memory_cache: Dict[str, Any] = {}
        
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then disk)."""
        # Check memory cache first
        with self._lock:
            if key in self._memory_cache:
                return self._memory_cache[key]
        
        # Check disk cache
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
                # Update memory cache
                with self._lock:
                    self._memory_cache[key] = value
                return value
        except Exception:
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache (both memory and disk)."""
        # Update memory cache
        with self._lock:
            self._memory_cache[key] = value
        
        # Write to disk
        cache_path = self._get_cache_path(key)
        temp_path = cache_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Atomic rename
            temp_path.replace(cache_path)
            return True
            
        except Exception:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._memory_cache.clear()
        
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception:
                pass


def generate_cache_key(segment_text: str, hop_idx: int, layout: str, model: str) -> str:
    """Generate a cache key for a specific segment/hop/layout/model combination."""
    content = f"{segment_text}:{hop_idx}:{layout}:{model}"
    return hashlib.md5(content.encode()).hexdigest()

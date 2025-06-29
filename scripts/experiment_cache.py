#!/usr/bin/env python3
"""
Experiment result caching to avoid rerunning identical experiments.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd


class ExperimentCache:
    """Cache experiment results to avoid redundant runs."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "cache_index.json"
        self._load_index()
    
    def _load_index(self):
        """Load the cache index."""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {}
    
    def _save_index(self):
        """Save the cache index."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_experiment_hash(self, config: Dict[str, Any], sample_df: pd.DataFrame) -> str:
        """Generate a unique hash for an experiment configuration."""
        # Create a deterministic representation
        config_str = json.dumps(config, sort_keys=True)
        
        # Include sample data in hash (statement IDs only for efficiency)
        sample_ids = sorted(sample_df['StatementID'].tolist())
        sample_str = ','.join(sample_ids)
        
        # Combine and hash
        content = f"{config_str}|{sample_str}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, config: Dict[str, Any], sample_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Get cached result if available."""
        exp_hash = self._get_experiment_hash(config, sample_df)
        
        if exp_hash in self.index:
            cache_info = self.index[exp_hash]
            result_file = self.cache_dir / cache_info['result_file']
            
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return None
    
    def set(self, config: Dict[str, Any], sample_df: pd.DataFrame, result: Dict[str, Any]):
        """Cache an experiment result."""
        exp_hash = self._get_experiment_hash(config, sample_df)
        result_file = f"result_{exp_hash[:8]}.json"
        
        # Save result
        result_path = self.cache_dir / result_file
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        # Update index
        self.index[exp_hash] = {
            'result_file': result_file,
            'config': config,
            'sample_size': len(sample_df),
            'timestamp': pd.Timestamp.now().isoformat(),
        }
        self._save_index()
    
    def clear(self):
        """Clear all cached results."""
        for file in self.cache_dir.glob("result_*.json"):
            file.unlink()
        self.index = {}
        self._save_index()

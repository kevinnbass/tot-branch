"""
Layout experiment configuration handler.
Supports loading layout experiments from YAML config files.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any


class LayoutExperimentConfig:
    """Handles layout experiment configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with optional config file path."""
        self.config_path = config_path
        self.config = {}
        
        if config_path and config_path.exists():
            self.load_config(config_path)
    
    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logging.info(f"Loaded layout experiment config from: {config_path}")
            return self.config
        except Exception as e:
            logging.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def get_enabled_layouts(self) -> List[str]:
        """Get list of layouts to test from enabled batches."""
        layouts = []
        
        if 'batches' not in self.config:
            return layouts
            
        for batch_name, batch_config in self.config['batches'].items():
            if batch_config.get('enabled', False):
                batch_layouts = batch_config.get('layouts', [])
                for layout in batch_layouts:
                    if isinstance(layout, dict):
                        layout_name = layout.get('name')
                        if layout_name:
                            layouts.append(layout_name)
                    elif isinstance(layout, str):
                        layouts.append(layout)
        
        return layouts
    
    def get_batch_config(self, batch_name: str) -> Optional[Dict]:
        """Get configuration for a specific batch."""
        return self.config.get('batches', {}).get(batch_name)
    
    def get_layout_info(self, layout_name: str) -> Optional[Dict]:
        """Get detailed info about a specific layout."""
        for batch_name, batch_config in self.config.get('batches', {}).items():
            if not batch_config.get('enabled', False):
                continue
                
            for layout in batch_config.get('layouts', []):
                if isinstance(layout, dict) and layout.get('name') == layout_name:
                    return {
                        'name': layout_name,
                        'description': layout.get('description', ''),
                        'base_layout': layout.get('base_layout', 'standard'),
                        'batch': batch_name,
                        'sample_size': batch_config.get('sample_size', 259),
                    }
        
        return None
    
    def get_experiment_config(self) -> Dict:
        """Get overall experiment configuration."""
        return self.config.get('experiment', {})
    
    def get_execution_config(self) -> Dict:
        """Get execution settings."""
        return self.config.get('execution', {})
    
    def get_analysis_config(self) -> Dict:
        """Get analysis settings."""
        return self.config.get('analysis', {})
    
    def get_base_config(self) -> Dict:
        """Get base configuration for all layouts."""
        return self.config.get('experiment', {}).get('base_config', {}) 
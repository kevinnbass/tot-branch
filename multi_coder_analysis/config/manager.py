"""Configuration management module for the Multi-Coder Analysis system.

This module provides a centralized way to handle configuration from multiple sources:
- Default settings
- YAML configuration files
- Environment variables
- Command line arguments

The configuration is loaded in order of priority (highest to lowest):
1. Command line arguments
2. Environment variables  
3. YAML configuration files
4. Default settings
"""

from __future__ import annotations

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

try:
    from .settings import Settings
except ImportError:
    from settings import Settings

__all__ = ["ConfigManager", "ConfigError", "load_config"]


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


@dataclass
class ConfigManager:
    """Centralized configuration management.
    
    Handles loading configuration from multiple sources and provides
    a unified interface for accessing configuration values.
    
    Attributes:
        settings: Pydantic settings object with validated configuration
        _config_sources: List of configuration sources that were loaded
        _raw_config: Raw configuration dictionary before validation
    """
    
    settings: Settings
    _config_sources: list[str] = field(default_factory=list)
    _raw_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_sources(
        cls,
        config_file: Optional[Union[str, Path]] = None,
        env_prefix: str = "MCA_",
        cli_args: Optional[Dict[str, Any]] = None,
        validate: bool = True
    ) -> "ConfigManager":
        """Load configuration from multiple sources.
        
        Args:
            config_file: Path to YAML configuration file
            env_prefix: Prefix for environment variables
            cli_args: Command line arguments dictionary
            validate: Whether to validate the configuration
            
        Returns:
            ConfigManager instance with loaded configuration
            
        Raises:
            ConfigError: If configuration loading or validation fails
        """
        manager = cls(settings=Settings(), _config_sources=[], _raw_config={})
        
        try:
            # Load from YAML file
            if config_file:
                manager._load_yaml_config(config_file)
            
            # Load from environment variables
            manager._load_env_config(env_prefix)
            
            # Load from CLI arguments
            if cli_args:
                manager._load_cli_config(cli_args)
            
            # Create validated settings
            if validate:
                manager.settings = Settings(**manager._raw_config)
            
            return manager
            
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}") from e
    
    def _load_yaml_config(self, config_file: Union[str, Path]) -> None:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            logging.warning(f"Configuration file not found: {config_path}")
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
                
            self._raw_config.update(yaml_config)
            self._config_sources.append(f"yaml:{config_path}")
            logging.info(f"Loaded configuration from: {config_path}")
            
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}") from e
        except OSError as e:
            raise ConfigError(f"Could not read {config_path}: {e}") from e
    
    def _load_env_config(self, prefix: str) -> None:
        """Load configuration from environment variables."""
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix):].lower()
                
                # Convert string values to appropriate types
                env_config[config_key] = self._convert_env_value(value)
        
        if env_config:
            self._raw_config.update(env_config)
            self._config_sources.append(f"env:{prefix}*")
            logging.debug(f"Loaded {len(env_config)} environment variables")
    
    def _load_cli_config(self, cli_args: Dict[str, Any]) -> None:
        """Load configuration from CLI arguments."""
        # Filter out None values and convert argument names
        cli_config = {}
        
        for key, value in cli_args.items():
            if value is not None:
                # Convert dashes to underscores for consistency
                config_key = key.replace('-', '_')
                cli_config[config_key] = value
        
        if cli_config:
            self._raw_config.update(cli_config)
            self._config_sources.append("cli")
            logging.debug(f"Loaded {len(cli_config)} CLI arguments")
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string environment variable to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            # Support dot notation for nested keys
            if '.' in key:
                keys = key.split('.')
                value = self.settings
                for k in keys:
                    value = getattr(value, k)
                return value
            else:
                return getattr(self.settings, key, default)
        except AttributeError:
            return default
    
    def update(self, **kwargs) -> None:
        """Update configuration with new values.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        # Update raw config
        self._raw_config.update(kwargs)
        
        # Recreate validated settings
        self.settings = Settings(**self._raw_config)
        
        # Track the update
        self._config_sources.append("runtime_update")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return self.settings.model_dump()
    
    def validate(self) -> None:
        """Validate current configuration.
        
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            # Validation happens automatically in Pydantic Settings
            Settings(**self._raw_config)
        except Exception as e:
            raise ConfigError(f"Configuration validation failed: {e}") from e
    
    def get_sources(self) -> list[str]:
        """Get list of configuration sources that were loaded.
        
        Returns:
            List of source descriptions
        """
        return self._config_sources.copy()
    
    def print_summary(self) -> None:
        """Print a summary of the loaded configuration."""
        print("\n📋 Configuration Summary")
        print("=" * 50)
        
        print(f"Sources loaded: {', '.join(self._config_sources)}")
        print(f"Provider: {self.settings.provider}")
        print(f"Model: {self.settings.model}")
        print(f"Batch size: {self.settings.batch_size}")
        print(f"Concurrency: {self.settings.concurrency}")
        print(f"Regex mode: {self.settings.regex_mode}")
        print(f"Log level: {self.settings.log_level}")
        
        if self.settings.google_api_key:
            print("✅ Google API key configured")
        if self.settings.openrouter_api_key:
            print("✅ OpenRouter API key configured")
        
        print("=" * 50)


def load_config(
    config_file: Optional[Union[str, Path]] = None,
    cli_args: Optional[Dict[str, Any]] = None,
    env_prefix: str = "MCA_",
    validate: bool = True
) -> ConfigManager:
    """Convenience function to load configuration.
    
    Args:
        config_file: Path to YAML configuration file
        cli_args: Command line arguments dictionary
        env_prefix: Prefix for environment variables
        validate: Whether to validate the configuration
        
    Returns:
        ConfigManager instance with loaded configuration
        
    Raises:
        ConfigError: If configuration loading fails
    """
    return ConfigManager.from_sources(
        config_file=config_file,
        env_prefix=env_prefix,
        cli_args=cli_args,
        validate=validate
    )


def setup_logging(config: ConfigManager) -> None:
    """Set up logging based on configuration.
    
    Args:
        config: ConfigManager instance with logging configuration
    """
    level = getattr(logging, config.settings.log_level.upper())
    
    # Configure basic logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if config.settings.json_logs:
        # TODO: Implement structured JSON logging
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Set up third-party library log levels
    logging.getLogger("google").setLevel(logging.ERROR)
    logging.getLogger("google.genai").setLevel(logging.ERROR)
    logging.getLogger("google.genai.client").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Add file logging if configured
    # TODO: Implement file logging configuration
    
    logging.info(f"Logging configured: level={config.settings.log_level}") 
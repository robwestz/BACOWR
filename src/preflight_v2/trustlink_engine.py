"""
TrustLink Engine - Manages T1-T5 trust source hierarchy

Handles:
- Loading preconfigured trust sources from YAML
- Topic/industry matching
- Tier-based prioritization
- Evidence linking to claims
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .hyper_preflight_engine import (
    TrustLinkEngine as BaseTrustLinkEngine,
    TrustSource,
    SourceTier
)


def load_trustlink_sources(config_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load trustlink sources from YAML configuration.

    Args:
        config_path: Optional path to trustlink sources YAML.
                     Defaults to config/trustlink_sources.yaml

    Returns:
        Dict mapping domain to source metadata
    """
    if config_path is None:
        # Default to config/trustlink_sources.yaml in same directory
        current_dir = Path(__file__).parent
        config_path = current_dir / "config" / "trustlink_sources.yaml"

    if not os.path.exists(config_path):
        # Return empty dict if no config found (fallback mode)
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        sources = yaml.safe_load(f)

    return sources or {}


def create_trustlink_engine(
    config_path: Optional[str] = None,
    custom_sources: Optional[Dict[str, Dict[str, Any]]] = None
) -> BaseTrustLinkEngine:
    """
    Factory function to create TrustLinkEngine with preconfigured sources.

    Args:
        config_path: Optional path to trustlink sources YAML
        custom_sources: Optional dict of additional sources to register

    Returns:
        Configured TrustLinkEngine instance
    """
    # Load sources from YAML
    preconfigured = load_trustlink_sources(config_path)

    # Merge with custom sources if provided
    if custom_sources:
        preconfigured.update(custom_sources)

    # Create engine
    engine = BaseTrustLinkEngine(preconfigured_sources=preconfigured)

    return engine


# Convenience function for getting default engine
def get_default_trustlink_engine() -> BaseTrustLinkEngine:
    """
    Get default TrustLinkEngine with Swedish sources.

    Returns:
        TrustLinkEngine with preconfigured Swedish sources
    """
    return create_trustlink_engine()


__all__ = [
    'load_trustlink_sources',
    'create_trustlink_engine',
    'get_default_trustlink_engine',
    'TrustSource',
    'SourceTier'
]

"""
BACOWR - Backlink Article Content Orchestration With Refinement

Main package for BacklinkContent Engine (Next-A1)
"""

__version__ = "0.3.0-alpha"
__author__ = "BACOWR Project"

from .api import run_backlink_job

__all__ = ['run_backlink_job']

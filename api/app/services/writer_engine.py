"""
Writer Engine Service - BACOWR Demo Environment

Multi-provider LLM content generation with intelligent prompting strategies.
Supports bridge types (strong/pivot/wrapper) and LSI term injection.

Part of the BACOWR Demo API - Production-ready content generation service.

NOTE: This module now imports from the unified writer implementation in
src/writer/unified_writer.py to resolve Gemini-related conflicts.

The original implementation has been moved and consolidated into unified_writer.py
and is re-exported here for backward compatibility.
"""

# Import the unified implementation from src
import sys
from pathlib import Path

# Add src to path if not already there
src_path = str(Path(__file__).parent.parent.parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from writer.unified_writer import (
    UnifiedWriterEngine as WriterEngine,
    LLMProvider,
    BridgeType,
    GenerationMetrics
)

# Re-export for backward compatibility
__all__ = ['WriterEngine', 'LLMProvider', 'BridgeType', 'GenerationMetrics']

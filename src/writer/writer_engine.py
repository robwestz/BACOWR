"""
Writer Engine - Generate articles with LLM integration

Part of Del 3B: Content Generation Pipeline
Generates backlink articles based on job_package using Claude, OpenAI, or Gemini

NOTE: This module now imports from unified_writer.py which consolidates
the duplicate writer implementations that were causing Gemini-related conflicts.

The original implementation has been moved to unified_writer.py and is
re-exported here for backward compatibility.
"""

# Import the unified implementation
# Use try/except to handle both relative and absolute imports
try:
    from .unified_writer import UnifiedWriterEngine as WriterEngine
except ImportError:
    # Fallback to absolute import for direct module loading
    import sys
    from pathlib import Path
    _writer_dir = Path(__file__).parent
    if str(_writer_dir) not in sys.path:
        sys.path.insert(0, str(_writer_dir))
    from unified_writer import UnifiedWriterEngine as WriterEngine

# Re-export for backward compatibility
__all__ = ['WriterEngine']

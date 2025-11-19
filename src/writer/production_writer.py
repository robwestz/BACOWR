"""
Production Writer Engine - Multi-provider LLM support with advanced prompting

Supports:
- OpenAI (GPT-5)
- Anthropic (Claude 3.5 Sonnet)
- Google (Gemini 2.5 Pro)
- Multi-stage generation for optimal quality
- Cost tracking and retry logic

NOTE: This module now imports from unified_writer.py which consolidates
the duplicate writer implementations that were causing Gemini-related conflicts.

The original implementation has been moved to unified_writer.py and is
re-exported here for backward compatibility.
"""

# Import the unified implementation
# Use try/except to handle both relative and absolute imports
try:
    from .unified_writer import (
        UnifiedWriterEngine as ProductionWriter,
        LLMProvider,
        GenerationMetrics
    )
except ImportError:
    # Fallback to absolute import for direct module loading
    import sys
    from pathlib import Path
    _writer_dir = Path(__file__).parent
    if str(_writer_dir) not in sys.path:
        sys.path.insert(0, str(_writer_dir))
    from unified_writer import (
        UnifiedWriterEngine as ProductionWriter,
        LLMProvider,
        GenerationMetrics
    )

# Re-export for backward compatibility
__all__ = ['ProductionWriter', 'LLMProvider', 'GenerationMetrics']

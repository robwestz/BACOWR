"""
APEX Framework - Adaptive Precision Execution Architecture

Domain-agnostic quality convergence framework för LLM-driven system.

Core concepts:
- Quality functions: Domain-specific scoring (0.0-1.0)
- Critics: Multi-dimensional evaluation
- Generators: Diverse output strategies
- Convergence: Iterative improvement patterns
- Routing: Complexity-based pattern selection
"""

from .apex_framework import (
    APEXConfig,
    APEXMetrics,
    APEXResult,
    APEXExecutor,
    Critique,
    CritiqueResult,
    Critic,
    Generator,
    ConvergenceStrategy,
    Pattern,
    PatternType,
    Router,
    TerminationReason,
    create_apex_instance
)

__all__ = [
    'APEXConfig',
    'APEXMetrics',
    'APEXResult',
    'APEXExecutor',
    'Critique',
    'CritiqueResult',
    'Critic',
    'Generator',
    'ConvergenceStrategy',
    'Pattern',
    'PatternType',
    'Router',
    'TerminationReason',
    'create_apex_instance'
]

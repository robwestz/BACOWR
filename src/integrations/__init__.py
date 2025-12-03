"""
LLM Interface Integrations for BACOWR HyperPreflight

Provides unified interfaces for:
- ChatGPT function calling
- Claude tool use
- Direct API access
"""

from .llm_interface import (
    PreflightRequest,
    PreflightResponse,
    run_preflight_unified
)

from .chatgpt_interface import (
    CHATGPT_FUNCTION_DEFINITION,
    chatgpt_function_handler
)

from .claude_interface import (
    CLAUDE_TOOL_DEFINITION,
    claude_tool_handler
)

__all__ = [
    'PreflightRequest',
    'PreflightResponse',
    'run_preflight_unified',
    'CHATGPT_FUNCTION_DEFINITION',
    'chatgpt_function_handler',
    'CLAUDE_TOOL_DEFINITION',
    'claude_tool_handler'
]

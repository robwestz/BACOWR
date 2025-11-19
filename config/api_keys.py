"""
Centralized API Key Management for BACOWR

All API keys (internal and external) are managed here.
Load from .env file and provide validation and access.
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass
from enum import Enum

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class APIKeyType(Enum):
    """Types of API keys"""
    # External LLM providers
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

    # External research/data providers
    AHREFS = "ahrefs"
    SERPAPI = "serpapi"

    # Internal services
    DATABASE = "database"
    REDIS = "redis"


@dataclass
class APIKeyConfig:
    """Configuration for a single API key"""
    name: str
    env_var: str
    required: bool = False
    description: str = ""


class APIKeyManager:
    """
    Centralized manager for all API keys.

    Usage:
        from config.api_keys import api_keys

        # Check if key is available
        if api_keys.has_key(APIKeyType.ANTHROPIC):
            key = api_keys.get_key(APIKeyType.ANTHROPIC)
            # use key...
    """

    # Define all API keys used in the system
    KEY_CONFIGS = {
        # LLM Providers (at least one required for production)
        APIKeyType.ANTHROPIC: APIKeyConfig(
            name="Anthropic Claude",
            env_var="ANTHROPIC_API_KEY",
            required=False,  # Optional - can use other providers
            description="Claude API for content generation"
        ),
        APIKeyType.OPENAI: APIKeyConfig(
            name="OpenAI GPT",
            env_var="OPENAI_API_KEY",
            required=False,  # Optional - can use other providers
            description="GPT-4/GPT-3.5 for content generation"
        ),
        APIKeyType.GOOGLE: APIKeyConfig(
            name="Google Gemini",
            env_var="GOOGLE_API_KEY",
            required=False,  # Optional - can use other providers
            description="Gemini for content generation"
        ),

        # Research & Data Providers
        APIKeyType.AHREFS: APIKeyConfig(
            name="Ahrefs API",
            env_var="AHREFS_API_KEY",
            required=False,  # Falls back to mock data
            description="SERP and competitor data"
        ),
        APIKeyType.SERPAPI: APIKeyConfig(
            name="SerpAPI",
            env_var="SERPAPI_KEY",
            required=False,  # Falls back to Ahrefs or mock
            description="Search engine results"
        ),

        # Database
        APIKeyType.DATABASE: APIKeyConfig(
            name="Database URL",
            env_var="DATABASE_URL",
            required=False,  # Defaults to SQLite
            description="PostgreSQL connection string"
        ),

        # Cache (optional)
        APIKeyType.REDIS: APIKeyConfig(
            name="Redis URL",
            env_var="REDIS_URL",
            required=False,  # Optional caching layer
            description="Redis cache for performance"
        ),
    }

    def __init__(self):
        """Initialize API key manager and validate configuration"""
        self._keys: Dict[APIKeyType, Optional[str]] = {}
        self._load_keys()
        self._validate_keys()

    def _load_keys(self):
        """Load all API keys from environment variables"""
        for key_type, config in self.KEY_CONFIGS.items():
            value = os.getenv(config.env_var)
            if value:
                self._keys[key_type] = value
                logger.debug(f"Loaded {config.name} API key")
            else:
                self._keys[key_type] = None
                if config.required:
                    logger.warning(f"Required API key missing: {config.name} ({config.env_var})")
                else:
                    logger.debug(f"Optional API key not set: {config.name}")

    def _validate_keys(self):
        """Validate that required keys are present"""
        missing_required = []

        for key_type, config in self.KEY_CONFIGS.items():
            if config.required and not self._keys.get(key_type):
                missing_required.append(f"{config.name} ({config.env_var})")

        if missing_required:
            error_msg = f"Missing required API keys: {', '.join(missing_required)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate at least one LLM provider is available
        llm_providers = [APIKeyType.ANTHROPIC, APIKeyType.OPENAI, APIKeyType.GOOGLE]
        has_llm = any(self._keys.get(provider) for provider in llm_providers)

        if not has_llm:
            logger.warning(
                "No LLM provider API keys found! "
                "System will run in mock mode only. "
                "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY for production use."
            )

    def get_key(self, key_type: APIKeyType) -> Optional[str]:
        """
        Get API key value.

        Args:
            key_type: Type of API key to retrieve

        Returns:
            API key value or None if not set
        """
        return self._keys.get(key_type)

    def has_key(self, key_type: APIKeyType) -> bool:
        """
        Check if API key is available.

        Args:
            key_type: Type of API key to check

        Returns:
            True if key is set and non-empty
        """
        key = self._keys.get(key_type)
        return key is not None and len(key) > 0

    def get_available_llm_providers(self) -> list[str]:
        """
        Get list of available LLM providers.

        Returns:
            List of provider names that have API keys configured
        """
        providers = []
        if self.has_key(APIKeyType.ANTHROPIC):
            providers.append("anthropic")
        if self.has_key(APIKeyType.OPENAI):
            providers.append("openai")
        if self.has_key(APIKeyType.GOOGLE):
            providers.append("google")
        return providers

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all API keys.

        Returns:
            Dictionary with key configuration status
        """
        status = {}
        for key_type, config in self.KEY_CONFIGS.items():
            status[config.name] = {
                "configured": self.has_key(key_type),
                "required": config.required,
                "description": config.description,
                "env_var": config.env_var
            }
        return status

    def print_status(self):
        """Print API key configuration status to console"""
        logger.info("=" * 70)
        logger.info("API Key Configuration Status")
        logger.info("=" * 70)

        for key_type, config in self.KEY_CONFIGS.items():
            status_symbol = "✓" if self.has_key(key_type) else "✗"
            required_label = " [REQUIRED]" if config.required else ""
            logger.info(
                f"{status_symbol} {config.name:20} - {config.description}{required_label}"
            )

        logger.info("=" * 70)
        llm_providers = self.get_available_llm_providers()
        if llm_providers:
            logger.info(f"Available LLM providers: {', '.join(llm_providers)}")
        else:
            logger.warning("No LLM providers available - running in MOCK MODE only")
        logger.info("=" * 70)


# Global singleton instance
api_keys = APIKeyManager()


# Convenience functions for common operations
def get_anthropic_key() -> Optional[str]:
    """Get Anthropic API key"""
    return api_keys.get_key(APIKeyType.ANTHROPIC)


def get_openai_key() -> Optional[str]:
    """Get OpenAI API key"""
    return api_keys.get_key(APIKeyType.OPENAI)


def get_google_key() -> Optional[str]:
    """Get Google API key"""
    return api_keys.get_key(APIKeyType.GOOGLE)


def get_ahrefs_key() -> Optional[str]:
    """Get Ahrefs API key"""
    return api_keys.get_key(APIKeyType.AHREFS)


def get_serpapi_key() -> Optional[str]:
    """Get SerpAPI key"""
    return api_keys.get_key(APIKeyType.SERPAPI)


def get_database_url() -> Optional[str]:
    """Get database URL"""
    return api_keys.get_key(APIKeyType.DATABASE)


def get_redis_url() -> Optional[str]:
    """Get Redis URL"""
    return api_keys.get_key(APIKeyType.REDIS)


if __name__ == "__main__":
    # Print status when run directly
    logging.basicConfig(level=logging.INFO)
    api_keys.print_status()

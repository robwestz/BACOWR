"""
Base Module Class
All modules inherit from this
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseModule(ABC):
    """Base class for all BacklinkContent Engine modules"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize module with optional config

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main execution method. Must be implemented by subclasses.

        Returns:
            Dict with module-specific output
        """
        pass

    def validate_input(self, data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present in input data

        Args:
            data: Input data dictionary
            required_fields: List of required field names

        Raises:
            ValueError: If any required field is missing
        """
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    def log_step(self, message: str, level: str = "info") -> None:
        """
        Log a step in the module execution

        Args:
            message: Log message
            level: Log level (debug, info, warning, error)
        """
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{self.__class__.__name__}] {message}")

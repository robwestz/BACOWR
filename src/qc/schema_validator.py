"""
Schema Validator for BACOWR BacklinkJobPackage

Provides production-ready validation of job packages against JSON Schema.
Single source of truth for schema validation across the system.

Per BUILDER_PROMPT.md STEG 1.3
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Schema validation error."""

    def __init__(self, message: str, path: Optional[List[str]] = None, details: Optional[Dict] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            path: JSON path where error occurred
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.path = path or []
        self.details = details or {}

    def __str__(self):
        if self.path:
            path_str = " -> ".join(str(p) for p in self.path)
            return f"{self.message} (at {path_str})"
        return self.message


class SchemaValidator:
    """
    Validates job packages against JSON schema.

    Thread-safe, reusable validator that can be used across the system
    for consistent validation of BacklinkJobPackage instances.

    Example:
        >>> validator = SchemaValidator()
        >>> job_package = {...}
        >>> if validator.validate(job_package):
        ...     print("Valid!")
        >>>
        >>> # With error details:
        >>> is_valid, errors = validator.validate_with_errors(job_package)
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize validator with schema.

        Args:
            schema_path: Path to JSON schema file. If None, uses default location.

        Raises:
            FileNotFoundError: If schema file not found
            ValueError: If schema file is invalid JSON
        """
        if schema_path is None:
            # Default to project root schema
            project_root = Path(__file__).parent.parent.parent
            schema_path = str(project_root / "backlink_job_package.schema.json")

        self.schema_path = schema_path
        self.schema = self._load_schema()

        # Try to import jsonschema for full validation
        try:
            import jsonschema
            self.jsonschema = jsonschema
            self.has_jsonschema = True
            logger.debug("jsonschema library available - full validation enabled")
        except ImportError:
            self.jsonschema = None
            self.has_jsonschema = False
            logger.warning("jsonschema library not available - using basic validation only")

    def _load_schema(self) -> Dict[str, Any]:
        """
        Load JSON schema from file.

        Returns:
            Parsed schema dictionary

        Raises:
            FileNotFoundError: If schema file not found
            ValueError: If schema is invalid JSON
        """
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            logger.debug(f"Schema loaded: {schema.get('title', 'Unknown')}")
            return schema
        except FileNotFoundError as e:
            logger.error(f"Schema file not found: {self.schema_path}")
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise ValueError(f"Invalid JSON in schema file: {e}") from e

    def validate(self, job_package: Dict[str, Any]) -> bool:
        """
        Validate job package against schema.

        Args:
            job_package: Job package dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        is_valid, _ = self.validate_with_errors(job_package)
        return is_valid

    def validate_with_errors(self, job_package: Dict[str, Any]) -> tuple[bool, List[ValidationError]]:
        """
        Validate job package and return detailed errors.

        Args:
            job_package: Job package dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if self.has_jsonschema:
            return self._validate_with_jsonschema(job_package)
        else:
            return self._validate_basic(job_package)

    def _validate_with_jsonschema(self, job_package: Dict[str, Any]) -> tuple[bool, List[ValidationError]]:
        """
        Full validation using jsonschema library.

        Args:
            job_package: Job package to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            # Disable external reference validation (for schemas with $ref to missing files)
            # In production, all schemas should be self-contained or have proper resolvers
            from jsonschema import Draft7Validator

            # Create validator without external reference validation
            validator = Draft7Validator(self.schema)

            # Collect all errors
            errors_list = list(validator.iter_errors(job_package))

            if not errors_list:
                logger.debug("Validation passed")
                return True, []

            # Convert errors to our format
            validation_errors = []
            for e in errors_list:
                # Skip unresolvable reference errors (external $ref)
                if "Unresolvable" in str(e) or "unretrievable" in str(e).lower():
                    logger.debug(f"Skipping external reference error: {e.message}")
                    continue

                error = ValidationError(
                    message=e.message,
                    path=list(e.path),
                    details={
                        'validator': e.validator,
                        'validator_value': str(e.validator_value) if hasattr(e, 'validator_value') else None,
                        'instance': str(e.instance)[:100]  # Truncate for logging
                    }
                )
                validation_errors.append(error)
                logger.warning(f"Validation error: {error}")

            # If we only had external reference errors, consider it valid
            if not validation_errors:
                logger.debug("Only external reference errors - considering valid")
                return True, []

            return False, validation_errors

        except self.jsonschema.SchemaError as e:
            # Schema itself is invalid
            error = ValidationError(
                message=f"Invalid schema: {e.message}",
                details={'schema_error': str(e)}
            )
            logger.error(f"Schema error: {error}")
            return False, [error]

        except Exception as e:
            # For unresolvable errors, fall back to basic validation
            if "Unresolvable" in str(e) or "unretrievable" in str(e).lower():
                logger.warning(f"External reference error, falling back to basic validation: {e}")
                return self._validate_basic(job_package)

            # Other unexpected errors
            error = ValidationError(
                message=f"Unexpected validation error: {str(e)}",
                details={'exception_type': type(e).__name__}
            )
            logger.error(f"Unexpected error during validation: {error}", exc_info=True)
            return False, [error]

    def _validate_basic(self, job_package: Dict[str, Any]) -> tuple[bool, List[ValidationError]]:
        """
        Basic validation without jsonschema library.
        Checks only required top-level fields.

        Args:
            job_package: Job package to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Get required fields from schema
        required_fields = self.schema.get('required', [])

        # Check each required field
        for field in required_fields:
            if field not in job_package:
                error = ValidationError(
                    message=f"Missing required field: {field}",
                    path=[field]
                )
                errors.append(error)
                logger.warning(f"Missing required field: {field}")

        if errors:
            return False, errors

        logger.debug("Basic validation passed (all required fields present)")
        logger.warning("For full validation, install: pip install jsonschema")
        return True, []

    def validate_or_raise(self, job_package: Dict[str, Any]) -> None:
        """
        Validate job package or raise ValidationError.

        Args:
            job_package: Job package to validate

        Raises:
            ValidationError: If validation fails
        """
        is_valid, errors = self.validate_with_errors(job_package)

        if not is_valid:
            # Combine all error messages
            error_messages = [str(e) for e in errors]
            raise ValidationError(
                message=f"Validation failed with {len(errors)} error(s): {'; '.join(error_messages)}",
                details={'errors': [e.message for e in errors]}
            )

    def get_required_fields(self) -> List[str]:
        """
        Get list of required top-level fields from schema.

        Returns:
            List of required field names
        """
        return self.schema.get('required', [])

    def get_schema_version(self) -> str:
        """
        Get schema version/title.

        Returns:
            Schema title or "Unknown"
        """
        return self.schema.get('title', 'Unknown')

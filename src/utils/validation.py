"""
JSON Schema validation utilities.

Provides validation against Next-A1 schemas for BacklinkJobPackage and extensions.
"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import jsonschema
from jsonschema import Draft202012Validator

from .logger import get_logger

logger = get_logger(__name__)


class SchemaValidator:
    """Validates JSON data against Next-A1 schemas."""

    def __init__(self, schema_dir: Path = None):
        """
        Initialize validator with schema directory.

        Args:
            schema_dir: Path to directory containing JSON schemas
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent.parent / "schemas"

        self.schema_dir = Path(schema_dir)
        self._schemas: Dict[str, Dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all JSON schemas from the schema directory."""
        schema_files = {
            "job_package": "backlink_job_package.schema.json",
            "next_a1": "next-a1-spec.json",
        }

        for name, filename in schema_files.items():
            schema_path = self.schema_dir / filename
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self._schemas[name] = json.load(f)
                logger.debug(f"Loaded schema: {name}", path=str(schema_path))
            else:
                logger.warning(f"Schema file not found: {filename}", path=str(schema_path))

    def validate_job_package(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a BacklinkJobPackage against its schema.

        Args:
            data: Job package data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "job_package" not in self._schemas:
            return False, "Job package schema not loaded"

        try:
            Draft202012Validator(self._schemas["job_package"]).validate(data)
            logger.info("Job package validation successful", job_id=data.get("job_meta", {}).get("job_id"))
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            error_msg = f"Validation error at {'.'.join(str(p) for p in e.path)}: {e.message}"
            logger.error("Job package validation failed", error=error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error("Unexpected validation error", error=error_msg)
            return False, error_msg

    def validate_extension(
        self,
        extension_name: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a Next-A1 extension (links_extension, intent_extension, etc.).

        Args:
            extension_name: Name of the extension (e.g., "links_extension")
            data: Extension data to validate

        Returns:
            Tuple of (is_valid, error_message)

        Note: This performs basic structural validation. Full validation would require
        extracting extension schemas from next-a1-spec.json.
        """
        required_fields = {
            "links_extension": ["bridge_type", "anchor_swap", "placement", "trust_policy", "compliance"],
            "intent_extension": ["serp_intent_primary", "target_page_intent", "intent_alignment",
                               "recommended_bridge_type", "required_subtopics", "notes"],
            "qc_extension": ["anchor_risk", "readability", "thresholds_version", "notes_observability"],
        }

        if extension_name not in required_fields:
            return False, f"Unknown extension type: {extension_name}"

        missing_fields = [f for f in required_fields[extension_name] if f not in data]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(f"{extension_name} validation failed", error=error_msg)
            return False, error_msg

        logger.debug(f"{extension_name} validation successful")
        return True, None


# Global validator instance
_validator: Optional[SchemaValidator] = None


def get_validator() -> SchemaValidator:
    """Get or create the global schema validator instance."""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator

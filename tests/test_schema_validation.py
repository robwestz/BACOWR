#!/usr/bin/env python3
"""
Schema Validation Test for BACOWR BacklinkJobPackage

Tests that example job packages conform to the JSON Schema specification.
This is a required test per NEXT-A1-ENGINE-ADDENDUM.md section 2.1.

Requirements:
- jsonschema library (pip install jsonschema)
- backlink_job_package.schema.json
- At least one example job package
"""

import json
import sys
import os
from pathlib import Path

def log(message, level="INFO"):
    """Simple logger"""
    print(f"[{level}] {message}", flush=True)

def validate_schema():
    """
    Validates example BacklinkJobPackage against JSON Schema.

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        import jsonschema
    except ImportError:
        log("❌ jsonschema library not found. Install with: pip install jsonschema", "ERROR")
        log("   Falling back to basic structural validation...", "WARNING")
        return validate_basic_structure()

    log("🔍 Starting JSON Schema Validation")
    log("=" * 60)

    # Get project root (parent of tests/)
    project_root = Path(__file__).parent.parent

    # Load schema
    schema_path = project_root / "backlink_job_package.schema.json"
    log(f"Loading schema: {schema_path}")

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        log(f"✅ Schema loaded: {schema.get('title', 'Unknown')}")
    except Exception as e:
        log(f"❌ Failed to load schema: {e}", "ERROR")
        return False

    # Load example job package
    example_path = project_root / "examples" / "example_job_package.json"

    # Fallback to BacklinkJobPackage.json if example doesn't exist
    if not example_path.exists():
        example_path = project_root / "BacklinkJobPackage.json"
        log(f"⚠️  examples/example_job_package.json not found, using BacklinkJobPackage.json", "WARNING")

    log(f"Loading example: {example_path}")

    try:
        with open(example_path, 'r', encoding='utf-8') as f:
            instance = json.load(f)
        job_id = instance.get('job_meta', {}).get('job_id', 'Unknown')
        log(f"✅ Example loaded: Job ID = {job_id}")
    except Exception as e:
        log(f"❌ Failed to load example: {e}", "ERROR")
        return False

    # Validate
    log("\n🔬 Validating against schema...")

    try:
        jsonschema.validate(instance=instance, schema=schema)
        log("✅ VALIDATION PASSED!", "SUCCESS")
        log("\n📋 Summary:")
        log(f"   - Schema: {schema.get('title')}")
        log(f"   - Example: {job_id}")
        log(f"   - Required fields: {len(schema.get('required', []))}")
        log(f"   - All validations: PASS")
        return True

    except jsonschema.ValidationError as e:
        log("❌ VALIDATION FAILED!", "ERROR")
        log(f"\nError details:", "ERROR")
        log(f"   Path: {' -> '.join(str(p) for p in e.path)}", "ERROR")
        log(f"   Message: {e.message}", "ERROR")
        log(f"   Failed value: {e.instance}", "ERROR")
        return False

    except jsonschema.SchemaError as e:
        log("❌ SCHEMA ERROR!", "ERROR")
        log(f"   The schema itself is invalid: {e.message}", "ERROR")
        return False

def validate_basic_structure():
    """
    Basic validation without jsonschema library.
    Checks required fields only.
    """
    log("\n🔍 Starting Basic Structure Validation (no jsonschema)")
    log("=" * 60)

    project_root = Path(__file__).parent.parent

    # Load example
    example_path = project_root / "examples" / "example_job_package.json"
    if not example_path.exists():
        example_path = project_root / "BacklinkJobPackage.json"

    try:
        with open(example_path, 'r', encoding='utf-8') as f:
            instance = json.load(f)
    except Exception as e:
        log(f"❌ Failed to load example: {e}", "ERROR")
        return False

    # Check required top-level fields
    required_fields = [
        'job_meta',
        'input_minimal',
        'publisher_profile',
        'target_profile',
        'anchor_profile',
        'serp_research_extension',
        'intent_extension',
        'generation_constraints'
    ]

    missing = []
    for field in required_fields:
        if field in instance:
            log(f"   ✅ {field}")
        else:
            log(f"   ❌ {field} MISSING", "ERROR")
            missing.append(field)

    if missing:
        log(f"\n❌ Validation failed. Missing fields: {missing}", "ERROR")
        return False
    else:
        log("\n✅ Basic validation passed (all required fields present)", "SUCCESS")
        log("⚠️  For full schema validation, install: pip install jsonschema", "WARNING")
        return True

if __name__ == "__main__":
    log("BACOWR Schema Validation Test")
    log("Per NEXT-A1-ENGINE-ADDENDUM.md § 2.1\n")

    success = validate_schema()

    log("\n" + "=" * 60)
    if success:
        log("✅ TEST PASSED", "SUCCESS")
        sys.exit(0)
    else:
        log("❌ TEST FAILED", "ERROR")
        sys.exit(1)

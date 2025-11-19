#!/usr/bin/env python3
"""
Export OpenAPI specification from FastAPI app.

Exports the API specification to JSON and YAML formats for:
- External documentation
- API client generation
- Testing tools (Postman, Hoppscotch, etc.)
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))

from app.main import app

def export_openapi_spec():
    """Export OpenAPI specification to JSON and YAML."""

    # Get OpenAPI schema from FastAPI app
    openapi_schema = app.openapi()

    # Export to JSON
    json_path = project_root / "docs" / "api" / "openapi.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported OpenAPI JSON to: {json_path}")

    # Export to YAML (if pyyaml is available)
    try:
        import yaml

        yaml_path = project_root / "docs" / "api" / "openapi.yaml"

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)

        print(f"✓ Exported OpenAPI YAML to: {yaml_path}")
    except ImportError:
        print("⚠ PyYAML not installed - skipping YAML export")
        print("  Install with: pip install pyyaml")

    # Print summary
    print(f"\n📊 API Specification Summary:")
    print(f"  Title: {openapi_schema['info']['title']}")
    print(f"  Version: {openapi_schema['info']['version']}")
    print(f"  Endpoints: {len(openapi_schema['paths'])}")
    print(f"  Schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))}")

    # List all endpoints
    print(f"\n🔗 Endpoints:")
    for path, methods in openapi_schema['paths'].items():
        for method in methods.keys():
            if method != 'parameters':
                print(f"  {method.upper():8} {path}")

    return json_path

if __name__ == "__main__":
    export_openapi_spec()

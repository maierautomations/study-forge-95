#!/usr/bin/env python3
"""
Export OpenAPI schema to JSON file for frontend client generation
Usage: python export_openapi.py
"""

import json
import os
from pathlib import Path

# Add app to path
import sys
sys.path.append(str(Path(__file__).parent))

from app.main import app
from app.openapi import export_openapi_json


def export_openapi():
    """Export OpenAPI schema to JSON file"""
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / "openapi"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "openapi.json"
    
    print(f"Exporting OpenAPI schema to {output_file}")
    
    try:
        # Generate OpenAPI schema
        openapi_json = export_openapi_json(app)
        
        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(openapi_json)
        
        print(f"✅ OpenAPI schema exported successfully!")
        print(f"📁 File: {output_file}")
        print(f"📊 Size: {len(openapi_json)} bytes")
        
        # Validate JSON
        schema = json.loads(openapi_json)
        print(f"🔍 Validation: Valid JSON with {len(schema.get('paths', {}))} endpoints")
        
        # Show endpoint summary
        if "paths" in schema:
            print("\n📋 Available endpoints:")
            for path, methods in schema["paths"].items():
                method_list = ", ".join(methods.keys())
                print(f"   {path} ({method_list})")
        
        print(f"\n🚀 Ready for frontend client generation:")
        print(f"   npx openapi-typescript {output_file} -o src/lib/api/generated.ts")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


if __name__ == "__main__":
    success = export_openapi()
    exit(0 if success else 1)
"""Dump the canonical envelope JSON Schema (single source of truth for TS types).

Run as ``python -m app.export.jsonschema`` — writes the schema to stdout. The Makefile
``gen-types`` target pipes this into the frontend and converts it to TypeScript.
"""

from __future__ import annotations

import json
import sys

from app.schemas.canonical import CanonicalEnvelope


def main() -> None:
    schema = CanonicalEnvelope.model_json_schema()
    schema["title"] = "CanonicalEnvelope"
    json.dump(schema, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

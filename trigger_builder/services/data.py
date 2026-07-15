"""
Data-loading helpers for schema and pilot examples.
Separated from views so they can be reused or tested independently.
"""

import json
import os

from django.conf import settings


def inputs_path(*parts: str) -> str:
    base = getattr(settings, "IMPLEMENTATION_INPUTS_DIR", None)
    if not base:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "implementation_inputs")
    return os.path.normpath(os.path.join(base, *parts))


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_compact_schema() -> dict:
    path = inputs_path("schema", "ui_schema_compact.json")
    if not os.path.exists(path):
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "go-web-app",
            "packages",
            "trigger-builder-prototype",
            "src",
            "data",
            "generated",
            "ui_schema_compact.json",
        )
    return load_json(os.path.normpath(path))


def load_pilot_examples() -> dict:
    return load_json(inputs_path("examples", "pilot_eaps.json"))


def load_pilot_statements() -> dict:
    """Returns the statements dict keyed by document_id string."""
    path = inputs_path("examples", "pilot_eap_statements.json")
    if not os.path.exists(path):
        # Fall back to the generated copy bundled with the frontend package
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "go-web-app",
            "packages",
            "trigger-builder-prototype",
            "src",
            "data",
            "generated",
            "pilot_eap_statements.json",
        )
    return load_json(os.path.normpath(path))

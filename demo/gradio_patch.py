"""Compatibility patches for Gradio client behavior."""

import gradio_client.utils as _gu


_original_json_schema_to_python_type = _gu._json_schema_to_python_type


def _patched_json_schema_to_python_type(schema, defs=None):
    if isinstance(schema, bool):
        return "Any"
    return _original_json_schema_to_python_type(schema, defs)


def apply_patch():
    """Patch gradio_client to tolerate boolean schemas."""
    _gu._json_schema_to_python_type = _patched_json_schema_to_python_type

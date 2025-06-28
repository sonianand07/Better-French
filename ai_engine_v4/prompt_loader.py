"""Utility to load Jinja2 templates for AI-Engine v4 prompts."""
from __future__ import annotations

import pathlib, functools
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parent
ENV = Environment(
    loader=FileSystemLoader(str(ROOT / "prompts")),
    autoescape=select_autoescape(enabled_extensions=("jinja",)),
    trim_blocks=True,
    lstrip_blocks=True,
)


@functools.lru_cache(maxsize=None)
def render(template_name: str, **ctx: Dict[str, Any]) -> str:  # noqa: D401 – simple helper
    """Render *template_name* with ``ctx`` and return the final string."""
    template = ENV.get_template(template_name)
    return template.render(**ctx) 
"""Utility to load Jinja2 prompt templates."""
from __future__ import annotations

import pathlib, functools
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parent
ENV = Environment(
    loader=FileSystemLoader(str(ROOT / "prompts")),
    autoescape=select_autoescape(enabled_extensions=("jinja",)),
    trim_blocks=True,
    lstrip_blocks=True,
)


@functools.lru_cache(maxsize=None)
def render(template_name: str, **ctx: Dict[str, Any]) -> str:
    template = ENV.get_template(template_name)
    return template.render(**ctx) 
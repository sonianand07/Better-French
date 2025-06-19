#!/usr/bin/env python3
"""Run the full v3 pipeline locally in one go and (optionally) serve the site.

Usage examples
--------------
# Fetch + qualify only
PYTHONPATH=. python3 scripts/run_v3_pipeline.py

# Fetch + qualify then start local web server on http://localhost:8010/
PYTHONPATH=. python3 scripts/run_v3_pipeline.py --serve
"""
from __future__ import annotations

import argparse, importlib, logging, socketserver, http.server, pathlib, webbrowser, socket, sys

# Ensure API key from config/config.ini is loaded into env before any ai_engine_v3 modules import LLMClient
import config.api_config  # noqa: F401 side-effect

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Lazy-import to avoid any circular issues
fetch_mod = importlib.import_module("ai_engine_v3.scripts.fetch_news")
qualify_mod = importlib.import_module("ai_engine_v3.scripts.qualify_news")

ROOT = pathlib.Path(__file__).resolve().parent.parent / "ai_engine_v3" / "website"


def serve_ui(port_start: int = 8010, port_end: int = 8020):
    if not ROOT.exists():
        logger.error("Website directory not found: %s", ROOT)
        return

    chosen_port = None
    for p in range(port_start, port_end+1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", p)) != 0:
                chosen_port = p
                break
    if chosen_port is None:
        logger.warning("All ports %d-%d busy – skipping local server.", port_start, port_end)
        return

    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=str(ROOT), **kwargs
    )
    with socketserver.TCPServer(("", chosen_port), handler) as httpd:
        logger.info("🌐 Serving v3 site on http://localhost:%d/ (Ctrl+C to quit)", chosen_port)
        webbrowser.open(f"http://localhost:{chosen_port}/")
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Run Better French AI-Engine v3 pipeline")
    parser.add_argument("--serve", action="store_true", help="Start local web server after processing")
    args = parser.parse_args()

    # Quick API-key ping
    from ai_engine_v3.client import LLMClient
    try:
        _ = LLMClient().chat([{"role":"user","content":"ping"}], max_tokens=1, temperature=0)
    except Exception as e:
        logger.error("❌ OpenRouter API key check failed: %s", e)
        sys.exit(1)

    logger.info("\n🚀 Running v3 fetch → qualify pipeline\n")

    # Remove extra CLI args so sub-scripts don't choke on unknown flags
    sys.argv = [sys.argv[0]]

    fetch_mod.main()
    qualify_mod.main()

    if args.serve:
        serve_ui()


if __name__ == "__main__":
    main() 
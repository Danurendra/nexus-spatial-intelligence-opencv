#!/usr/bin/env python
"""Server entry point for Nexus Spatial Intelligence API.

Usage:
    python src/server.py              # Start API server on 0.0.0.0:8000
    python src/server.py --host 127.0.0.1 --port 8001
"""

import argparse
import logging

import uvicorn

from src.api import create_app

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Parse arguments and start the API server."""
    parser = argparse.ArgumentParser(
        description="Start Nexus Spatial Intelligence API server"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development only)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    
    app = create_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

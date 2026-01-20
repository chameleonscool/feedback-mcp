"""
Server module - Unified entry point for SSE and STDIO modes.
"""
import argparse
import logging
import os
import sys
import threading
import time

import uvicorn

from core import mcp, logger, DATA_DIR, LOG_PATH
from web import app


def run_web_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI web server."""
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="User Intent MCP Server")
    parser.add_argument(
        "--mode", 
        choices=["sse", "stdio"], 
        default="sse",
        help="Transport mode: 'sse' for HTTP+SSE, 'stdio' for STDIO (default: sse)"
    )
    
    # Defaults from Environment Variables
    env_port = int(os.getenv("USERINTENT_WEB_PORT", "8000"))
    env_host = os.getenv("USERINTENT_WEB_HOST", "0.0.0.0")

    parser.add_argument(
        "--port",
        type=int,
        default=env_port,
        help=f"Port for the web server (default: {env_port})"
    )
    parser.add_argument(
        "--host",
        default=env_host,
        help=f"Host for the web server (default: {env_host})"
    )
    args = parser.parse_args()
    
    logger.info(f"Starting User Intent MCP Server in {args.mode.upper()} mode")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Log file: {LOG_PATH}")
    
    if args.mode == "sse":
        # SSE mode: Mount MCP to FastAPI and run uvicorn
        logger.info(f"Web UI will be available at http://localhost:{args.port}")
        logger.info(f"MCP SSE endpoint: http://localhost:{args.port}/mcp/sse")
        
        # Mount MCP SSE transport
        app.mount("/mcp", mcp.http_app(transport='sse'))
        
        run_web_server(port=args.port)
        
    elif args.mode == "stdio":
        # STDIO mode: Run web server in background, MCP in foreground
        logger.info(f"Starting Web UI in background at http://localhost:{args.port}")
        
        web_thread = threading.Thread(target=run_web_server, kwargs={"port": args.port}, daemon=True)
        web_thread.start()
        
        # Give web server time to start
        time.sleep(1)
        
        logger.info("Web UI ready")
        logger.info("MCP STDIO transport ready, waiting for client connection...")
        
        # Run MCP in STDIO mode (blocking)
        # Handle client disconnection gracefully
        try:
            mcp.run()
        except (BrokenPipeError, ConnectionResetError, EOFError):
            # Client closed the connection - normal shutdown
            logger.info("Client disconnected gracefully")
            sys.exit(0)
        except BaseException as e:
            # Handle ExceptionGroup from anyio TaskGroup
            if _is_client_disconnect_error(e):
                logger.info("Client disconnected gracefully")
                sys.exit(0)
            else:
                # Re-raise if it's not a connection error
                raise


def _is_client_disconnect_error(exc: BaseException) -> bool:
    """Check if the exception is a client disconnection error."""
    # Direct connection errors
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, EOFError)):
        return True
    
    # Check by class name for anyio errors (avoid import dependency)
    exc_type_name = type(exc).__name__
    if exc_type_name == "BrokenResourceError":
        return True
    
    # Handle ExceptionGroup / BaseExceptionGroup
    if isinstance(exc, BaseException) and hasattr(exc, 'exceptions'):
        # It's an exception group - check all sub-exceptions
        return all(_is_client_disconnect_error(sub_exc) for sub_exc in exc.exceptions)
    
    return False


if __name__ == "__main__":
    main()

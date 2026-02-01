from src import HTTPServer, ServerConfig, HTTPRequest, HTTPResponse, ResponseFactory
from loguru import logger
from pathlib import Path
import argparse
import json
import sys


def setup_logging(debug: bool = False) -> None:
    logger.remove()
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    level = "DEBUG" if debug else "INFO"
    logger.add(sys.stderr, format=log_format, level=level, colorize=True)
    logger.add("logs/server.log", format=log_format, level="DEBUG", rotation="10 MB")


def register_routes(server: HTTPServer) -> None:
    @server.router.route("/api/status", methods=["GET"])
    def api_status(request: HTTPRequest) -> HTTPResponse:
        data = {"status": "ok", "server": "PyHTTP/1.0"}
        return ResponseFactory.json(json.dumps(data))

    @server.router.route("/api/echo", methods=["POST"])
    def api_echo(request: HTTPRequest) -> HTTPResponse:
        return ResponseFactory.json(
            json.dumps(
                {
                    "method": request.method,
                    "path": request.path,
                    "headers": request.headers,
                    "body": request.body.decode("utf-8", errors="replace"),
                    "query": request.query_params,
                }
            )
        )

    @server.router.route("/api/headers", methods=["GET"])
    def api_headers(request: HTTPRequest) -> HTTPResponse:
        return ResponseFactory.json(json.dumps(request.headers, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple HTTP Server")
    parser.add_argument(
        "-p", "--port", type=int, default=8080, help="Port to listen on"
    )
    parser.add_argument("-H", "--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "-s", "--static", default="static", help="Static files directory"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    Path("logs").mkdir(exist_ok=True)
    setup_logging(args.debug)
    config = ServerConfig(host=args.host, port=args.port, static_dir=Path(args.static))
    server = HTTPServer(config)
    register_routes(server)
    logger.info(f"Static files: {config.static_dir.resolve()}")
    server.start()


if __name__ == "__main__":
    main()

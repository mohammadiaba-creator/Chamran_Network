from .response import HTTPResponse, ResponseFactory
from .config import ServerConfig, SUPPORTED_METHODS
from .request import HTTPRequest
from typing import Callable
from loguru import logger
from pathlib import Path
import mimetypes

RouteHandler = Callable[[HTTPRequest], HTTPResponse]


class Router:

    def __init__(self, config: ServerConfig):
        self.config = config
        self.routes: dict[str, dict[str, RouteHandler]] = {}
        self.static_dir = Path(config.static_dir).resolve()

    def route(self, path: str, methods: list[str] = None) -> Callable:
        methods = methods or ["GET"]

        def decorator(handler: RouteHandler) -> RouteHandler:
            for method in methods:
                if path not in self.routes:
                    self.routes[path] = {}
                self.routes[path][method.upper()] = handler
                logger.info(f"Registered route: {method.upper()} {path}")
            return handler

        return decorator

    def handle(self, request: HTTPRequest) -> HTTPResponse:
        if request.method not in SUPPORTED_METHODS:
            logger.warning(f"Unsupported method: {request.method}")
            return ResponseFactory.method_not_allowed(request.method)
        if request.path in self.routes:
            method_handlers = self.routes[request.path]
            if request.method in method_handlers:
                return method_handlers[request.method](request)
            return ResponseFactory.method_not_allowed(request.method)
        return self._serve_static(request)

    def _serve_static(self, request: HTTPRequest) -> HTTPResponse:
        if request.method not in ("GET", "HEAD"):
            return ResponseFactory.method_not_allowed(request.method)
        path = request.path.lstrip("/")
        if not path:
            path = self.config.default_file
        file_path = (self.static_dir / path).resolve()
        if not self._is_safe_path(file_path):
            logger.warning(f"Path traversal attempt blocked: {request.path}")
            return ResponseFactory.not_found(request.path)
        if file_path.is_dir():
            file_path = file_path / self.config.default_file
        if not file_path.exists() or not file_path.is_file():
            logger.debug(f"File not found: {file_path}")
            return ResponseFactory.not_found(request.path)
        return self._read_file(file_path, request.method == "HEAD")

    def _is_safe_path(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.static_dir)
            return True
        except ValueError:
            return False

    def _read_file(self, path: Path, head_only: bool = False) -> HTTPResponse:
        try:
            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"
            response = HTTPResponse(200).set_content_type(content_type)
            if head_only:
                response.headers["Content-Length"] = str(path.stat().st_size)
            else:
                response.set_body(path.read_bytes())
            logger.debug(f"Serving: {path.name} ({content_type})")
            return response
        except PermissionError:
            logger.error(f"Permission denied: {path}")
            return HTTPResponse(403).set_body("<h1>403 Forbidden</h1>")
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return ResponseFactory.internal_error()

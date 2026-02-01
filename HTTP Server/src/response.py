from dataclasses import dataclass, field
from datetime import datetime, timezone
from .config import HTTP_STATUS


@dataclass
class HTTPResponse:
    status_code: int = 200
    headers: dict = field(default_factory=dict)
    body: bytes = b""
    version: str = "HTTP/1.1"

    def __post_init__(self):
        self.headers.setdefault("Server", "PyHTTP/1.0")
        self.headers.setdefault("Date", self._get_date())
        self.headers.setdefault("Connection", "close")

    @staticmethod
    def _get_date() -> str:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def set_content_type(self, content_type: str) -> "HTTPResponse":
        self.headers["Content-Type"] = content_type
        return self

    def set_body(self, body: bytes | str) -> "HTTPResponse":
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.body = body
        self.headers["Content-Length"] = str(len(body))
        return self

    def build(self) -> bytes:
        status_text = HTTP_STATUS.get(self.status_code, "Unknown")
        status_line = f"{self.version} {self.status_code} {status_text}\r\n"
        header_lines = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        response = f"{status_line}{header_lines}\r\n".encode("utf-8")
        return response + self.body


class ResponseFactory:

    @staticmethod
    def ok(body: bytes | str, content_type: str = "text/html") -> HTTPResponse:
        return HTTPResponse(200).set_content_type(content_type).set_body(body)

    @staticmethod
    def not_found(path: str = "") -> HTTPResponse:
        body = f"<h1>404 Not Found</h1><p>Path: {path}</p>"
        return HTTPResponse(404).set_content_type("text/html").set_body(body)

    @staticmethod
    def bad_request(reason: str = "") -> HTTPResponse:
        body = f"<h1>400 Bad Request</h1><p>{reason}</p>"
        return HTTPResponse(400).set_content_type("text/html").set_body(body)

    @staticmethod
    def method_not_allowed(method: str) -> HTTPResponse:
        body = f"<h1>405 Method Not Allowed</h1><p>Method: {method}</p>"
        return HTTPResponse(405).set_content_type("text/html").set_body(body)

    @staticmethod
    def internal_error(message: str = "Internal Server Error") -> HTTPResponse:
        body = f"<h1>500 Internal Server Error</h1><p>{message}</p>"
        return HTTPResponse(500).set_content_type("text/html").set_body(body)

    @staticmethod
    def json(data: str, status: int = 200) -> HTTPResponse:
        return HTTPResponse(status).set_content_type("application/json").set_body(data)

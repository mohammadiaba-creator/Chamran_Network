from dataclasses import dataclass, field
from typing import Optional
from loguru import logger


@dataclass
class HTTPRequest:
    method: str = ""
    path: str = "/"
    version: str = "HTTP/1.1"
    headers: dict = field(default_factory=dict)
    body: bytes = b""
    query_params: dict = field(default_factory=dict)
    raw: bytes = b""

    @property
    def content_length(self) -> int:
        return int(self.headers.get("content-length", 0))

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "")


class RequestParser:

    @staticmethod
    def parse(raw_data: bytes) -> Optional[HTTPRequest]:
        if not raw_data:
            logger.warning("Empty request received")
            return None
        try:
            request = HTTPRequest(raw=raw_data)
            if b"\r\n\r\n" in raw_data:
                header_section, body = raw_data.split(b"\r\n\r\n", 1)
                request.body = body
            else:
                header_section = raw_data
            lines = header_section.decode("utf-8", errors="replace").split("\r\n")
            if not lines:
                logger.error("No request line found")
                return None
            request_line = lines[0].split(" ")
            if len(request_line) < 2:
                logger.error(f"Malformed request line: {lines[0]}")
                return None
            request.method = request_line[0].upper()
            request.path = request_line[1]
            request.version = request_line[2] if len(request_line) > 2 else "HTTP/1.1"
            if "?" in request.path:
                path, query_string = request.path.split("?", 1)
                request.path = path
                request.query_params = RequestParser._parse_query_string(query_string)
            for line in lines[1:]:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    request.headers[key.lower()] = value
            logger.debug(f"Parsed: {request.method} {request.path}")
            return request
        except Exception as e:
            logger.error(f"Request parsing failed: {e}")
            return None

    @staticmethod
    def _parse_query_string(query: str) -> dict:
        params = {}
        for param in query.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        return params

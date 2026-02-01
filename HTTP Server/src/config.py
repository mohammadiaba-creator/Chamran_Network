from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    backlog: int = 128
    buffer_size: int = 8192
    static_dir: Path = Path("static")
    default_file: str = "index.html"
    timeout: float = 30.0


HTTP_STATUS = {
    (200): "OK",
    (201): "Created",
    (204): "No Content",
    (400): "Bad Request",
    (403): "Forbidden",
    (404): "Not Found",
    (405): "Method Not Allowed",
    (500): "Internal Server Error",
}
SUPPORTED_METHODS = {"GET", "POST", "HEAD"}

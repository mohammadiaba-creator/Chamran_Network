from .response import ResponseFactory
from .request import RequestParser
from .config import ServerConfig
from typing import Optional
from .router import Router
from loguru import logger
import threading
import socket


class HTTPServer:

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.router = Router(self.config)
        self._socket: Optional[socket.socket] = None
        self._running = False

    def start(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._socket.bind((self.config.host, self.config.port))
            self._socket.listen(self.config.backlog)
            self._running = True
            logger.info(f"Server running at http://{self.config.host}:{self.config.port}")
            self._accept_loop()
        except OSError as e:
            logger.error(f"Failed to bind to {self.config.host}:{self.config.port} - {e}")
            raise
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            logger.info("Server stopped")

    def _accept_loop(self) -> None:
        while self._running:
            try:
                client_socket, address = self._socket.accept()
                client_socket.settimeout(self.config.timeout)
                thread = threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True)
                thread.start()
            except OSError:
                if self._running:
                    logger.error("Accept failed")
                break

    def _handle_client(self, client: socket.socket, address: tuple) -> None:
        client_ip = f"{address[0]}:{address[1]}"
        try:
            raw_data = self._receive_request(client)
            if not raw_data:
                return
            request = RequestParser.parse(raw_data)
            if not request:
                response = ResponseFactory.bad_request("Malformed request")
            else:
                logger.info(f"{client_ip} - {request.method} {request.path}")
                response = self.router.handle(request)
            client.sendall(response.build())
            logger.debug(f"{client_ip} - Response: {response.status_code}")
        except socket.timeout:
            logger.warning(f"{client_ip} - Connection timed out")
        except ConnectionResetError:
            logger.debug(f"{client_ip} - Connection reset by client")
        except BrokenPipeError:
            logger.debug(f"{client_ip} - Broken pipe")
        except Exception as e:
            logger.exception(f"{client_ip} - Unexpected error: {e}")
            try:
                error_response = ResponseFactory.internal_error()
                client.sendall(error_response.build())
            except Exception:
                pass
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _receive_request(self, client: socket.socket) -> bytes:
        data = b""
        content_length = 0
        headers_received = False
        while True:
            try:
                chunk = client.recv(self.config.buffer_size)
                if not chunk:
                    break
                data += chunk
                if not headers_received and b"\r\n\r\n" in data:
                    headers_received = True
                    header_part = data.split(b"\r\n\r\n")[0]
                    for line in header_part.split(b"\r\n"):
                        if line.lower().startswith(b"content-length:"):
                            content_length = int(line.split(b":")[1].strip())
                            break
                if headers_received:
                    header_end = data.index(b"\r\n\r\n") + 4
                    body_received = len(data) - header_end
                    if body_received >= content_length:
                        break
            except socket.timeout:
                break
        return data

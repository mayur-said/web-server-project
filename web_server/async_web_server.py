import asyncio
import logging
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple, Callable

server_logger = logging.getLogger(__name__)


class AsyncHTTPServer:
    MAX_BODY_SIZE:int = 1024 * 1024 # 1 MB

    def __init__(self, app: Callable[[Dict[str, Any]], Dict[str, Any]], host: str = '127.0.0.1', port:int =8080):
        self.app = app
        self.host = host
        self.port = port
        self.server: asyncio.Server = None
    
    async def listen_serve(self) -> None:
        self.server = await asyncio.start_server(self.__handle_request, self.host, self.port)
        server_logger.info(f"Server started at http://{self.host}:{self.port}")

        async with self.server:
            await self.server.serve_forever()

    async def __handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr: Tuple[str, str] = writer.get_extra_info("peername")
        server_logger.info(f"client {addr} connected")

        http_handler = HttpHandler(reader, writer)
        asgi_scope: Dict[str, Any] = await http_handler.parse_http_request(self.MAX_BODY_SIZE)
        if not asgi_scope:
            return
        server_logger.debug(f"asgi scope: {asgi_scope}") 
        # send scope to app and get response
        try:
            response: Dict[str, Any] = await self.app(asgi_scope)
            server_logger.debug(f"web server response {response}")
            await http_handler.send_http_response(**response)
        except Exception as e:
            server_logger.error(e)
            await http_handler.send_http_response(status_code=500, reason_phrase="Something went wrong!")
        

class HttpHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.reader = reader
        self.writer = writer
    
    async def parse_http_request(self, max_body_size: int) -> Dict[str, Any]:
        try:
            # read the first line of the request
            request_line: bytes = await self.reader.readline()
            if not request_line:
                await self.send_http_response(status_code=400, reason_phrase="Bad Request")
                return
            method, path, http_version = request_line.decode().strip().split(' ', 2)

            # read headers until an empty line is encountered
            headers = {}
            while True:
                line = await self.reader.readline()
                if not line or line == b'\r\n':
                    break
                key, value = line.decode().strip().split(':', 1)
                headers[key.lower()] = value.strip()

            # read body if Content-Length header is present
            body = b''
            if 'content-length' in headers:
                content_length = int(headers['content-length'])
                # safety check: prevent reading excessively large bodies based on Content-Length header
                if content_length > max_body_size:
                    await self.send_http_response(status_code=400, reason_phrase="Bad Request")
                    return
                body = await self.reader.readexactly(content_length)

            # construct a basic ASGI scope dictionary
            # This is a simplified version of a real ASGI scope
            scope = {
                'type': 'http',
                'http_version': http_version,
                'method': method,
                'path': urlparse(path).path,
                'query_string': urlparse(path).query.encode(),
                'headers': [(k.encode(), v.encode()) for k, v in headers.items()],
                'raw_path': path.encode(),
                'body': body
            }
            return scope
        
        except Exception as e:
            server_logger.error(e)
            await self.send_http_response(status_code=400, reason_phrase="Bad Request")
            return
    
    async def send_http_response(self, status_code: int = 200, reason_phrase: str = "OK", headers: Dict[str, Any] = None, body: str ="") -> None:
        # default headers if none are provided
        if headers is None:
            headers = {
                "Content-Type": "text/plain",
                "Content-Length": str(len(body.encode("utf-8")))
            }

        # start with status line
        response_lines: List[str] = [f"HTTP/1.1 {status_code} {reason_phrase}"]
        # add headers
        for key, value in headers.items():
            response_lines.append(f"{key}: {value}")

        # add empty line to separate headers from body
        response_lines.append("")
        # add body
        response_lines.append(body.decode())
        response_text = "\r\n".join(response_lines)

        self.writer.write(response_text.encode())
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()
        return

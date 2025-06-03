import json
import re
from urllib.parse import parse_qs
from typing import Dict, Any, List, Tuple, Callable, Awaitable, Optional, Union
import logging

framework_logger = logging.getLogger(__name__)

class Request:
    """
    represents an incoming HTTP request. parses method, path, headers,
    query parameters, path parameters, and body.
    """
    def __init__(self, scope: Dict[str, Any]):
        self.path: str = scope['path']
        self.method: str = scope['method']
        self.headers: Dict[str, Any] = {k.decode(): v.decode() for k, v in scope['headers']}
        self.query_params: Dict[str, List[str]] = parse_qs(scope['query_string'].decode())
        self.body: bytes = scope['body']
        self.path_params: Dict[str, str] = {}
        self.json: Optional[Union[Dict[str, Any], List[Any]]] = None

        if 'content-type' in self.headers and 'application/json' in self.headers['content-type']:
            try:
                self.json = json.loads(self.body.decode('utf-8'))
            except json.JSONDecodeError:
                framework_logger.warning("Invalid JSON body received.")
                self.json = None

    def __repr__(self):
        return f"<Request method={self.method} path={self.path}>"

class Response:
    """
    represents an outgoing HTTP response.
    """
    def __init__(self, body: bytes ="", status_code: int = 200, reason_phrase: str = "OK", headers: Dict[str, Any] = None, content_type: str = "application/json"):
        self.body: bytes = body
        self.status_code: int = status_code
        self.reason_phrase: str = reason_phrase
        self.headers: Dict[str, Any] = headers if headers is not None else {}
        self.content_type: str = content_type

        # Set Content-Type header if not already present
        if 'content-type' not in {k.lower() for k in self.headers.keys()}:
            self.headers['Content-Type'] = self.content_type

        # Ensure content is bytes
        if isinstance(self.body, str):
            self.body = self.body.encode('utf-8')
        elif isinstance(self.body, (dict, list)):
            self.body = json.dumps(self.body).encode('utf-8')
            self.headers['Content-Type'] = 'application/json'
        else:
            self.body = self.body

        self.headers['Content-Length'] = str(len(self.body))

    def __repr__(self):
        return f"<Response status={self.status_code} content_type={self.content_type}>"

# define a type alias for handler functions for better readability
# a handler takes a Request and returns an Awaitable Response
Handler = Callable[[Request], Awaitable[Response]]

class Router:
    """
    handles routing requests to the appropriate handler functions based on
    HTTP method and path. Supports path parameters.
    """
    def __init__(self) -> None:
        self.routes: Dict[str, List[Tuple[re.Pattern[str], Handler]]] = {}

    def _add_route(self, method: str, path: str, handler: Handler) -> None:
        """adds a route for a specific HTTP method."""
        # convert path to a regex pattern to capture path parameters
        # e.g., /users/{user_id} -> /users/(?P<user_id>[^/]+)
        pattern = re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', r'(?P<\1>[^/]+)', path)
        self.routes.setdefault(method, []).append((re.compile(f"^{pattern}$"), handler))
        framework_logger.debug(f"Added route: {method} {path}")

    def get(self, path: str) -> Callable[[Handler], Handler]:
        def decorator(handler):
            self._add_route('GET', path, handler)
            return handler
        return decorator

    def post(self, path: str) -> Callable[[Handler], Handler]:
        def decorator(handler):
            self._add_route('POST', path, handler)
            return handler
        return decorator

    def put(self, path: str) -> Callable[[Handler], Handler]:
        def decorator(handler):
            self._add_route('PUT', path, handler)
            return handler
        return decorator

    def patch(self, path: str) -> Callable[[Handler], Handler]:
        def decorator(handler):
            self._add_route('PATCH', path, handler)
            return handler
        return decorator

    def delete(self, path: str) -> Callable[[Handler], Handler]:
        def decorator(handler):
            self._add_route('DELETE', path, handler)
            return handler
        return decorator

    async def dispatch(self, request: Request) -> Response:
        """
        dispatches the request to the matching handler.
        Sets request.path_params if path parameters are found.
        """
        if request.method in self.routes:
            for pattern, handler in self.routes[request.method]:
                match = pattern.match(request.path)
                if match:
                    request.path_params = match.groupdict()
                    return await handler(request)
        return Response(status_code=404, reason_phrase="Not Found")

class App:
    """
    the main application class. It's an ASGI-compatible callable that
    integrates the router and handles the request/response cycle.
    """
    def __init__(self):
        self.router = Router()

    # expose router methods directly on the app for convenience
    def get(self, path) -> Callable[[Handler], Handler]: return self.router.get(path)
    def post(self, path) -> Callable[[Handler], Handler]: return self.router.post(path)
    def put(self, path) -> Callable[[Handler], Handler]: return self.router.put(path)
    def patch(self, path) -> Callable[[Handler], Handler]: return self.router.patch(path)
    def delete(self, path) -> Callable[[Handler], Handler]: return self.router.delete(path)

    async def __call__(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """
        the ASGI application entry point.
        """
        if scope['type'] == 'http':
            request = Request(scope)
            framework_logger.info(f"received request: {request.method} {request.path}")

            # dispatch the request to the router
            response = await self.router.dispatch(request)
            reponse_text = {
                'status_code': response.status_code,
                'reason_phrase': response.reason_phrase,
                'headers': response.headers,
                'body': response.body
            }

            return reponse_text
        else:
            # for now support available for only http 
            reponse_text = {
                'status_code': 400,
                'reason_phrase': "Bad Request"
            }
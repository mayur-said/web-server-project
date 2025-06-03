# Async Web Server & Framework in Python
## Motivation
This project was built to:
- Demonstrate how to work with raw TCP connections
- Demonstrate how modern async frameworks operate internally
- Explore HTTP protocol handling, event loops and non-blocking I/O 
- Build something cool from scratch without using any web framework
## Overview
This is a simple asynchronous web server and lightweight REST API framework built entirely from scratch using python's built-in asyncio library. 
This project is not anywhere close to production-ready servers like uvicorn, gunicorn, etc. or frameworks like Flask or FastAPI. 
However, this project is built to gain an intuitive understanding of how servers use TCP connection, HTTP protocol, multi-threading and event-loops to manage thousands of connections concurrently.
If you have never built something similar, I would highly suggest you to build it! 

## Getting Started
### Prerequisites
- python 3.10+

### Installation
```bash
git clone git@github.com:mayur-said/web-server-project.git
cd web-server-project
```
This project uses only python built-in modules. Therefore no need to install any external dependencies. 

### Example Usage
checkout app.py for more detailed example
```python
from web_framework.web_framework import App, Request, Response
from web_server.async_web_server import AsyncHTTPServer
import asyncio
import logging


# setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

# initialize the application
app = App()

# in-memory database for demonstration
users_db = {
    "1": {"id": "1", "name": "mayur", "email": "mayur@example.com"},
    "2": {"id": "2", "name": "admin", "email": "admin@example.com"}
}

# define API endpoints
@app.get("/")
async def read_root(request: Request) -> Response:
    """handles GET requests to the root path."""
    return Response({"message": "welcome to the simple REST API!"}, content_type="application/json")

@app.get("/users")
async def get_users(request: Request) -> Response:
    """
    handles GET requests to /users.
    supports query parameters for filtering.
    example: /users?name=Alice
    """
    name_filter = request.query_params.get('name')
    if name_filter:
        filtered_users = [user for user in users_db.values() if name_filter[0].lower() in user['name'].lower()]
        return Response(filtered_users, content_type="application/json")
    return Response(list(users_db.values()), content_type="application/json")

# main
async def main() -> None:
    server = AsyncHTTPServer(app, host='127.0.0.1', port=8080)
    await server.listen_serve()

if __name__ == "__main__":
    app_logger.info("starting the application...") 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        app_logger.warning("\nserver shutting down.")
```

### Starting the Application
```bash
python3 app.py
```
The server should now be running at: http://localhost:8080/

### Testing 
You can use curl, Postman, or a browser to test your endpoints.
example GET request:
```bash
 curl http://localhost:8080/users/1
```
expected response
```json
{"id": "1", "name": "Mayur", "email": "mayur@example.com"}
```








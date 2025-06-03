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

@app.get("/users/{user_id}")
async def get_user_by_id(request: Request) -> Response:
    """
    handles GET requests to /users/{user_id}.
    demonstrates path parameters.
    example: /users/1
    """
    user_id = request.path_params.get('user_id')
    user = users_db.get(user_id)
    if user:
        return Response(user, content_type="application/json")
    return Response({"detail": "user not found"}, status_code=404, reason_phrase="Not Found", content_type="application/json")

@app.post("/users")
async def create_user(request: Request) -> Response:
    """
    handles POST requests to /users.
    expects a JSON body.
    example: POST /users with body {"name": "mayur", "email": "mayur@example.com"}
    """
    if request.json:
        new_user_data = request.json
        # generate a simple ID
        new_id = str(len(users_db) + 1)
        new_user = {"id": new_id, **new_user_data}
        users_db[new_id] = new_user
        return Response(new_user, status_code=201, content_type="application/json")
    return Response({"detail": "invalid JSON body"}, status_code=400, reason_phrase="Bad Request", content_type="application/json")

@app.put("/users/{user_id}")
async def update_user(request: Request) -> Response:
    """
    handles PUT requests to /users/{user_id}.
    expects a JSON body for full replacement.
    example: PUT /users/1 with body {"name": "mayur", "email": "mayur_new@example.com"}
    """
    user_id = request.path_params.get('user_id')
    if user_id not in users_db:
        return Response({"detail": "user not found"}, status_code=404, reason_phrase="Not Found", content_type="application/json")

    if request.json:
        updated_data = request.json
        # in a real app, you would validate the data
        users_db[user_id].update(updated_data)
        return Response(users_db[user_id], content_type="application/json")
    return Response({"detail": "Invalid JSON body"}, status_code=400, reason_phrase="Bad Request", content_type="application/json")

@app.patch("/users/{user_id}")
async def partial_update_user(request: Request) -> Response:
    """
    handles PATCH requests to /users/{user_id}.
    expects a JSON body for partial updates.
    example: PATCH /users/1 with body {"email": "mayur_updated@example.com"}
    """
    user_id = request.path_params.get('user_id')
    if user_id not in users_db:
        return Response({"detail": "User not found"}, status_code=404, reason_phrase="Not Found", content_type="application/json")

    if request.json:
        patch_data = request.json
        # apply patch to existing user data
        for key, value in patch_data.items():
            if key in users_db[user_id]:
                users_db[user_id][key] = value
        return Response(users_db[user_id], content_type="application/json")
    return Response({"detail": "invalid JSON body"}, status_code=400, reason_phrase="Bad Request", content_type="application/json")

@app.delete("/users/{user_id}")
async def delete_user(request: Request) -> Response:
    """
    handles DELETE requests to /users/{user_id}.
    example: DELETE /users/1
    """
    user_id = request.path_params.get('user_id')
    if user_id in users_db:
        del users_db[user_id]
        return Response({"message": "user deleted successfully"}, status_code=204, content_type="application/json")
    return Response({"detail": "user not found"}, status_code=404, reason_phrase="Not Found", content_type="application/json")

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
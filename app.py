from web_framework.web_framework import App, Request, Response
from web_server.async_web_server import AsyncHTTPServer
import asyncio
import logging


# setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

# Initialize the application
app = App()

# In-memory "database" for demonstration
users_db = {
    "1": {"id": "1", "name": "Mayur", "email": "mayur@example.com"},
    "2": {"id": "2", "name": "Admin", "email": "Admin@example.com"}
}

# --- Define API Endpoints ---
@app.get("/")
async def read_root(request: Request):
    """Handles GET requests to the root path."""
    return Response({"message": "Welcome to the simple REST API!"}, content_type="application/json")

@app.get("/users")
async def get_users(request: Request):
    """
    Handles GET requests to /users.
    Supports query parameters for filtering.
    Example: /users?name=Alice
    """
    name_filter = request.query_params.get('name')
    if name_filter:
        filtered_users = [user for user in users_db.values() if name_filter[0].lower() in user['name'].lower()]
        return Response(filtered_users, content_type="application/json")
    return Response(list(users_db.values()), content_type="application/json")

@app.get("/users/{user_id}")
async def get_user_by_id(request: Request):
    """
    Handles GET requests to /users/{user_id}.
    Demonstrates path parameters.
    Example: /users/1
    """
    user_id = request.path_params.get('user_id')
    user = users_db.get(user_id)
    if user:
        return Response(user, content_type="application/json")
    return Response({"detail": "User not found"}, status_code=404, content_type="application/json")

@app.post("/users")
async def create_user(request: Request):
    """
    Handles POST requests to /users.
    Expects a JSON body.
    Example: POST /users with body {"name": "Charlie", "email": "charlie@example.com"}
    """
    if request.json:
        new_user_data = request.json
        # Generate a simple ID
        new_id = str(len(users_db) + 1)
        new_user = {"id": new_id, **new_user_data}
        users_db[new_id] = new_user
        return Response(new_user, status_code=201, content_type="application/json")
    return Response({"detail": "Invalid JSON body"}, status_code=400, content_type="application/json")

@app.put("/users/{user_id}")
async def update_user(request: Request):
    """
    Handles PUT requests to /users/{user_id}.
    Expects a JSON body for full replacement.
    Example: PUT /users/1 with body {"name": "Alicia", "email": "alicia_new@example.com"}
    """
    user_id = request.path_params.get('user_id')
    if user_id not in users_db:
        return Response({"detail": "User not found"}, status_code=404, content_type="application/json")

    if request.json:
        updated_data = request.json
        # In a real app, you'd validate the data
        users_db[user_id].update(updated_data)
        return Response(users_db[user_id], content_type="application/json")
    return Response({"detail": "Invalid JSON body"}, status_code=400, content_type="application/json")

@app.patch("/users/{user_id}")
async def partial_update_user(request: Request):
    """
    Handles PATCH requests to /users/{user_id}.
    Expects a JSON body for partial updates.
    Example: PATCH /users/1 with body {"email": "alice_updated@example.com"}
    """
    user_id = request.path_params.get('user_id')
    if user_id not in users_db:
        return Response({"detail": "User not found"}, status_code=404, content_type="application/json")

    if request.json:
        patch_data = request.json
        # Apply patch to existing user data
        for key, value in patch_data.items():
            if key in users_db[user_id]: # Only update existing fields for simplicity
                users_db[user_id][key] = value
        return Response(users_db[user_id], content_type="application/json")
    return Response({"detail": "Invalid JSON body"}, status_code=400, content_type="application/json")

@app.delete("/users/{user_id}")
async def delete_user(request: Request):
    """
    Handles DELETE requests to /users/{user_id}.
    Example: DELETE /users/1
    """
    user_id = request.path_params.get('user_id')
    if user_id in users_db:
        del users_db[user_id]
        return Response({"message": "User deleted successfully"}, status_code=204, content_type="application/json")
    return Response({"detail": "User not found"}, status_code=404, content_type="application/json")

# --- Main execution block ---
async def main():
    server = AsyncHTTPServer(app)
    await server.listen_serve()

if __name__ == "__main__":
    app_logger.info("Starting the application...") 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        app_logger.warning("\nServer shutting down.")
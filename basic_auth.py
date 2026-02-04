import base64
from functools import wraps
from sanic import response

import env as env

def focal_auth():
    return basic_auth(env.SANIC__FOCAL_AUTH)

def basic_auth(user_pass: dict[str, str]):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(request, *args, **kwargs):
            auth = request.headers.get("authorization")

            if not auth or not auth.startswith("Basic "):
                return response.text(
                    "Unauthorized",
                    status=401,
                    headers={"WWW-Authenticate": 'Basic realm="Restricted"'},
                )

            try:
                encoded = auth.split(" ", 1)[1]
                decoded = base64.b64decode(encoded).decode()
                user, pwd = decoded.split(":", 1)
            except Exception:
                return response.text("Unauthorized", status=401)

            if user not in user_pass.keys():
                return response.text("Unauthorized", status=401)

            if  pwd != user_pass[user]:
                return response.text("Unauthorized", status=401)

            return await handler(request, *args, **kwargs)
        return wrapper
    return decorator
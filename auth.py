import base64
import logging
from functools import wraps

from sanic.response import text

from config import config

logger = logging.getLogger(__name__)


def auth_required(scope_name: str):
    """
    Creates a decorator for Basic Authentication.

    :param scope_name: The key name from SANIC_AUTH=_CONFIG (e.g., 'focal').
    :return: A decorator that validates credentials.
    """

    def decorator(handler):
        @wraps(handler)
        async def wrapper(request, *args, **kwargs):
            users = config.get_auth_users(scope_name)

            if not users:
                logger.warning(f"No credentials configured for auth scope '{scope_name}'")
                return text(
                    "Unauthorized",
                    status=401,
                    headers={"WWW-Authenticate": f'Basic realm="{scope_name}"'},
                )

            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Basic "):
                return text(
                    "Unauthorized",
                    status=401,
                    headers={"WWW-Authenticate": f'Basic realm="{scope_name}"'},
                )

            try:
                encoded = auth_header[6:]
                decoded = base64.b64decode(encoded).decode("utf-8")
                username, password = decoded.split(":", 1)
            except Exception:
                logger.warning(f"[{request.id}] Invalid auth header from {request.client_ip}")
                return text(
                    "Unauthorized",
                    status=401,
                    headers={"WWW-Authenticate": f'Basic realm="{scope_name}"'},
                )

            if users.get(username) != password:
                logger.warning(f"[{request.id}] Invalid credentials for scope '{scope_name}' from {request.client_ip}")
                return text(
                    "Unauthorized",
                    status=401,
                    headers={"WWW-Authenticate": f'Basic realm="{scope_name}"'},
                )

            request.ctx.user = username
            return await handler(request, *args, **kwargs)

        return wrapper

    return decorator

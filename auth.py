import base64
import logging
from functools import wraps

from sanic import Unauthorized

from config import config

logger = logging.getLogger(__name__)


def auth_required(scope_name: str):
    """
    Creates a decorator for Basic Authentication.

    :param scope_name: The key name from SANIC_AUTH_CONFIG (e.g., 'focal').
    :return: A decorator function that validates credentials.
    """

    user_pass = config.get_auth_users(scope_name)

    if not user_pass:
        logger.warning(f"No credentials configured for auth scope '{scope_name}'. All requests will fail.")

    def decorator(handler):
        @wraps(handler)
        async def wrapper(request, *args, **kwargs):
            auth_header = request.headers.get("authorization")

            if not auth_header or not auth_header.startswith("Basic "):
                logger.warning(
                    f"[{request.id}] Missing auth header on protected route '{scope_name}' from IP {request.client_ip}"
                )

                return Unauthorized()

            try:
                encoded = auth_header.split(" ", 1)[1]
                decoded = base64.b64decode(encoded).decode("utf-8")
                user, pwd = decoded.split(":", 1)

            except Exception as e:
                logger.error(f"[{request.id}] Failed to decode auth header: {e}")
                return Unauthorized()

            if user not in user_pass or user_pass[user] != pwd:
                logger.warning(
                    f"[{request.id}] Invalid credentials for user '{user}' on scope '{scope_name}' from IP {request.client_ip}"
                )
                return Unauthorized()

            return await handler(request, *args, **kwargs)

        return wrapper

    return decorator

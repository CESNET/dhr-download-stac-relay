import logging

from sanic import Sanic
from sanic.response import text

from config import config
from file_routes import bp as file_bp
from logging_config import setup_logging

# Initialize logging early
setup_logging()
logger = logging.getLogger(__name__)

# Global app instance (Required for Sanic workers to find the app)
app_name = config.APP_NAME
app = Sanic(app_name)

# Disable sanic default logger handlers, propagate its messages to root logger defined in logging_config.py
for logger_name in [
    "sanic.root",
    "sanic.error",
    "sanic.access",
    "sanic.server",
    "sanic.websockets"
]:
    sanic_logger = logging.getLogger(logger_name)
    sanic_logger.handlers.clear()
    sanic_logger.propagate = True

# Register blueprints
app.blueprint(file_bp)


# Middleware: Add request ID for tracing
@app.middleware("request")
async def add_request_id(request):
    request.ctx.request_id = getattr(request, "id", None) or id(request)
    logger.info(f"[{request.ctx.request_id}] {request.method} {request.path}")


# Global exception handler
@app.exception(Exception)
async def handle_exception(request, exception):
    logger.exception(f"Unhandled error on {getattr(request.ctx, 'request_id', 'unknown')}: {exception}")
    return text("Internal Server Error", status=500)


if __name__ == "__main__":
    # Only used for local development via 'python main.py'
    # In production, use: sanic main:app --workers=N
    app.run(
        host=config.SANIC_HOST,
        port=config.SANIC_PORT,
        debug=False,
        access_log=True,
        auto_reload=False
    )

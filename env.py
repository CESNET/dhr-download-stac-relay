import os

from dotenv import load_dotenv

load_dotenv()

BASE__APP_NAME: str = os.environ.get("BASE__APP_NAME", default="dhr-download-stac-relay")

SANIC__SERVER_HOST: str = os.environ.get("SANIC__SERVER_HOST", default="0.0.0.0")
SANIC__SERVER_PORT: int = int(os.environ.get("SANIC__SERVER_PORT", default=8080))

S3_CONNECTOR__LANDSAT: dict[str, str] = {
    'host_base': os.environ.get("S3_CONNECTOR__LANDSAT_HOST_BASE"),
    'host_bucket': os.environ.get("S3_CONNECTOR__LANDSAT_HOST_BUCKET"),
    'access_key': os.environ.get("S3_CONNECTOR__LANDSAT_ACCESS_KEY"),
    'secret_key': os.environ.get("S3_CONNECTOR__LANDSAT_SECRET_KEY")
}

LOGGER__NAME: str = os.environ.get("LOGGER__NAME", default=BASE__APP_NAME)
LOGGER__LOG_DIRECTORY: str = os.environ.get("LOGGER__LOG_DIRECTORY", default="./log")
LOGGER__LOG_FILENAME: str = os.environ.get("LOGGER__LOG_FILENAME", default=f"{BASE__APP_NAME}.log")
LOGGER__LOG_LEVEL: int = int(os.environ.get("LOGGER__LOG_LEVEL", default=20))

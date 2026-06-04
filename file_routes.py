import logging
import mimetypes
from typing import Iterator

from sanic import Blueprint, BadRequest, ServerError
from sanic.response import json, raw, redirect

from auth import auth_required
from config import config
from s3_connector import S3Connector

logger = logging.getLogger(__name__)

bp = Blueprint("file_routes", url_prefix="")


def _stream_s3_body(s3_body) -> Iterator[bytes]:
    """
    Generator reading S3 StreamingBody in chunks.
    Compatible with Sanic response.raw().
    """
    chunk_size = 8192

    while True:
        chunk = s3_body.read(chunk_size)

        if not chunk:
            break

        yield chunk


def log_request(request, path: str) -> None:
    logger.info(f"[{request.id}] Client IP={request.client_ip} Path={path}")


def create_s3_connector(service_name: str) -> S3Connector:
    cfg = config.get_s3_config(service_name)

    if cfg is None:
        raise RuntimeError(f"S3 configuration not found for service '{service_name}'")

    return S3Connector(
        host_base=cfg["host_base"],
        access_key=cfg["access_key"],
        secret_key=cfg["secret_key"],
        host_bucket=cfg["host_bucket"],
        logger=logger,
    )


def handle_landsat_range_request(request, s3_client: S3Connector, key: str, ):
    tar_member = request.args.get("tarMemberFile")
    offset_str = request.args.get("offset")
    size_str = request.args.get("size")

    try:
        offset = int(offset_str) if offset_str else 0
        size = int(size_str) if size_str else 0

    except ValueError:
        return BadRequest("Invalid offset or size parameters")

    if not tar_member or offset < 0 or size <= 0:
        return None

    s3_stream = s3_client.fetch_range_from_tar(key, offset, size)

    content_type = mimetypes.guess_type(tar_member)[0] or "application/octet-stream"

    logger.info(f"[{request.id}] Streaming file={tar_member} offset={offset} size={size}")

    return raw(
        _stream_s3_body(s3_stream),
        content_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={tar_member}",
            "Content-Length": str(size),
            "Accept-Ranges": "bytes",
        },
    )


def handle_request_logic(request, path: str, service_name: str, extra_path_prefix: str = ""):
    full_path = f"{extra_path_prefix}/{path}".lstrip("/")

    if ".." in full_path:
        return BadRequest("Invalid path")

    try:
        s3_client = create_s3_connector(service_name)

        if service_name == "landsat":
            response = handle_landsat_range_request(request, s3_client, full_path)

            if response is not None:
                return response

        presigned_url = s3_client.generate_presigned_url(full_path)

        logger.info(f"[{request.id}] Redirecting to presigned URL {presigned_url}")

        return redirect(presigned_url)

    except Exception:
        logger.exception(f"[{request.id}] Error processing request")

        return ServerError("Error processing request")


# ---------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------


@bp.get("/era5/<path:path>")
async def era5_handler(request, path):
    log_request(request, path)
    return handle_request_logic(request, path, "era5")


@bp.get("/e-obs/<path:path>")
async def eobs_handler(request, path):
    log_request(request, path)
    return handle_request_logic(request, path, "eobs")


@bp.get("/landsat/<path:path>")
async def landsat_handler(request, path):
    log_request(request, path)
    return handle_request_logic(request, path, "landsat")


@bp.get("/focal/<path:path>")
async def focal_handler(request, path):
    log_request(request, path)
    return handle_request_logic(request, path, "focal")


@bp.get("/focal/nukleus/<path:path>")
@auth_required("focal")
async def focal_nukleus_handler(request, path):
    log_request(request, path)
    return handle_request_logic(request, path, "focal", extra_path_prefix="nukleus")


@bp.get("/focal/nukleus-indices/<path:path>")
@auth_required("focal")
async def focal_nukleus_indices_handler(request, path):
    log_request(request, path)
    return handle_request_logic(request, path, "focal", extra_path_prefix="nukleus-indices")

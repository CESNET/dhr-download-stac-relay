import asyncio
import logging
import mimetypes
from functools import lru_cache

from sanic import Blueprint, BadRequest, ServerError
from sanic.response import redirect, HTTPResponse, ResponseStream

from auth import auth_required
from config import config
from s3_connector import S3Connector

logger = logging.getLogger(__name__)

bp = Blueprint("file_routes", url_prefix="")


async def run_blocking(func, *args, **kwargs):
    """Run synchronous I/O outside the Sanic event loop."""
    return await asyncio.to_thread(func, *args, **kwargs)


@lru_cache(maxsize=None)
def create_s3_connector(service_name: str) -> S3Connector:
    """
    Reuse an S3 client for each service within a worker process.

    boto3 clients support concurrent use across threads. Do not share
    clients across processes.
    """
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


async def handle_landsat_range_request(
        request,
        s3_client: S3Connector,
        key: str,
):
    tar_member = request.args.get("tarMemberFile")
    offset_str = request.args.get("offset")
    size_str = request.args.get("size")

    try:
        offset = int(offset_str) if offset_str else 0
        size = int(size_str) if size_str else 0

    except ValueError:
        return BadRequest("Invalid offset or size parameters")

    # This is not a TAR range request. Continue with normal handling.
    if not tar_member or offset < 0 or size <= 0:
        return None

    content_type = (
            mimetypes.guess_type(tar_member)[0]
            or "application/octet-stream"
    )

    headers = {
        "Content-Type": content_type,
        "Content-Disposition": f'attachment; filename="{tar_member}"',
        "Content-Length": str(size),
        "Accept-Ranges": "bytes",
    }

    if request.method == "HEAD":
        return HTTPResponse(
            status=200,
            headers=headers,
        )

    request_id = getattr(request.ctx, "request_id", request.id)

    logger.info(f"[{request_id}] Streaming file={tar_member}, "        f"offset={offset}, size={size}")

    # fetch_range_from_tar is synchronous, so run it in a worker thread.
    s3_stream = await run_blocking(
        s3_client.fetch_range_from_tar,
        key,
        offset,
        size,
    )

    async def streaming_function(response):
        try:
            while True:
                # StreamingBody.read() performs blocking I/O.
                chunk = await run_blocking(s3_stream.read, 8192)

                if not chunk:
                    break

                await response.write(chunk)

        finally:
            # Closing the stream may also perform blocking cleanup.
            await run_blocking(s3_stream.close)

    return ResponseStream(
        streaming_function,
        headers=headers,
        content_type=content_type,
    )


async def handle_request_logic(
        request,
        path: str,
        service_name: str,
        extra_path_prefix: str = "",
):
    full_path = f"{extra_path_prefix}/{path}".lstrip("/")

    if ".." in full_path:
        return BadRequest("Invalid path")

    try:
        s3_connector = create_s3_connector(service_name)

        if service_name == "landsat":
            response = await handle_landsat_range_request(
                request,
                s3_connector,
                full_path,
            )

            if response is not None:
                return response

        if request.method == "HEAD":
            # S3 metadata lookup must not block the event loop.
            metadata = await run_blocking(
                s3_connector.head_object,
                full_path,
            )

            return HTTPResponse(
                status=200,
                headers={
                    "Content-Length": str(metadata["ContentLength"]),
                    "Content-Type": metadata.get(
                        "ContentType",
                        "application/octet-stream",
                    ),
                },
            )

        # Generating a presigned URL does not require contacting S3.
        presigned_url = s3_connector.generate_presigned_url(full_path)

        request_id = getattr(request.ctx, "request_id", request.id)

        logger.info(f"[{request_id}] Redirecting to presigned URL: {presigned_url}")

        # Do not make an extra HEAD request just to log the file size.
        return redirect(presigned_url)

    except Exception:
        request_id = getattr(request.ctx, "request_id", request.id)

        logger.exception(f"[{request_id}] Error processing request")

        return ServerError("Error processing request")


# ---------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------


@bp.route("/era5/<path:path>", methods=["GET", "HEAD"])
async def era5_handler(request, path):
    return await handle_request_logic(request, path, "era5")


@bp.route("/e-obs/<path:path>", methods=["GET", "HEAD"])
async def eobs_handler(request, path):
    return await handle_request_logic(request, path, "eobs")


@bp.route("/landsat/<path:path>", methods=["GET", "HEAD"])
async def landsat_handler(request, path):
    return await handle_request_logic(request, path, "landsat")


@bp.route("/focal/<path:path>", methods=["GET", "HEAD"])
async def focal_handler(request, path):
    return await handle_request_logic(request, path, "focal")


@bp.route("/focal/nukleus/<path:path>", methods=["GET", "HEAD"])
@auth_required("focal")
async def focal_nukleus_handler(request, path):
    return await handle_request_logic(
        request,
        path,
        "focal",
        extra_path_prefix="nukleus",
    )


@bp.route("/focal/nukleus-indices/<path:path>", methods=["GET", "HEAD"])
@auth_required("focal")
async def focal_nukleus_indices_handler(request, path):
    return await handle_request_logic(
        request,
        path,
        "focal",
        extra_path_prefix="nukleus-indices",
    )

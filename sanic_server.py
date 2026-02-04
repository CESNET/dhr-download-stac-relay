import logging
import mimetypes

from sanic import Sanic, response

from s3_connector import S3Connector

import env

import basic_auth


class SanicServer():
    _logger: logging.Logger = None
    _app: Sanic = None

    def __init__(self, logger=logging.Logger(env.BASE__APP_NAME)):
        self._logger = logger

        self._app = Sanic(env.BASE__APP_NAME)
        self.register_routes()

    def run(self):
        self._app.run(host=env.SANIC__SERVER_HOST, port=env.SANIC__SERVER_PORT)

    def get_app(self):
        return self._app

    async def _stream_body(self, response_body):
        chunk_size = 8192
        while True:
            chunk = response_body.read(chunk_size)
            if not chunk:
                break
            yield chunk

    def register_routes(self):
        @self._app.get("/era5/<path:path>")
        async def slash_era5_parser(request, path):
            self._logger.info(
                f"[{str(request.id)}]; "
                f"Client IP: {request.client_ip}; "
                f"Path args: {request.raw_url.decode('utf-8')}"
            )

            try:
                s3_connector = S3Connector(
                    s3_endpoint=env.S3_CONNECTOR__ERA5['host_base'],
                    access_key=env.S3_CONNECTOR__ERA5['access_key'],
                    secret_key=env.S3_CONNECTOR__ERA5['secret_key'],
                    host_bucket=env.S3_CONNECTOR__ERA5['host_bucket'],
                    logger=self._logger
                )

                s3_key = path.lstrip("/")

                fileshare_url = s3_connector.generate_fileshare_url(key=s3_key)

                self._logger.info(
                    f"[{str(request.id)}]; "
                    f"Redirecting to: {fileshare_url}"
                )
                return response.redirect(fileshare_url)

            except Exception as e:
                self._logger.error(f"[{str(request.id)}] Exception occurred: {str(e)}")
                return response.json({"error": "Bad request"}, status=400)

        @self._app.get("/e-obs/<path:path>")
        async def slash_eobs_parser(request, path):
            self._logger.info(
                f"[{str(request.id)}]; "
                f"Client IP: {request.client_ip}; "
                f"Path args: {request.raw_url.decode('utf-8')}"
            )

            try:
                s3_connector = S3Connector(
                    s3_endpoint=env.S3_CONNECTOR__EOBS['host_base'],
                    access_key=env.S3_CONNECTOR__EOBS['access_key'],
                    secret_key=env.S3_CONNECTOR__EOBS['secret_key'],
                    host_bucket=env.S3_CONNECTOR__EOBS['host_bucket'],
                    logger=self._logger
                )

                s3_key = path.lstrip("/")

                fileshare_url = s3_connector.generate_fileshare_url(key=s3_key)

                self._logger.info(
                    f"[{str(request.id)}]; "
                    f"Redirecting to: {fileshare_url}"
                )
                return response.redirect(fileshare_url)

            except Exception as e:
                self._logger.error(f"[{str(request.id)}] Exception occurred: {str(e)}")
                return response.json({"error": "Bad request"}, status=400)

        @self._app.get("/landsat/<path:path>")
        async def slash_landsat_parser(request, path):
            self._logger.info(
                f"[{str(request.id)}]; "
                f"Client IP: {request.client_ip}; "
                f"Path args: {request.raw_url.decode('utf-8')}"
            )

            try:
                s3_connector = S3Connector(
                    s3_endpoint=env.S3_CONNECTOR__LANDSAT['host_base'],
                    access_key=env.S3_CONNECTOR__LANDSAT['access_key'],
                    secret_key=env.S3_CONNECTOR__LANDSAT['secret_key'],
                    host_bucket=env.S3_CONNECTOR__LANDSAT['host_bucket'],
                    logger=self._logger
                )

                s3_key = path.lstrip("/")
                tar_member_file = request.args.get("tarMemberFile")
                offset = int(request.args.get("offset") or 0)
                size = int(request.args.get("size") or 0)

                if (
                        (tar_member_file is not None) and
                        (offset != 0) and
                        (size != 0)
                ):
                    response_body = s3_connector.fetch_from_tar_by_range(key=s3_key, offset=offset, size=size)

                    self._logger.info(
                        f"[{str(request.id)}]; "
                        f"Streaming file: {tar_member_file}, offset: {offset}, size: {size} bytes"
                    )
                    return response.raw(
                        response_body,
                        content_type=mimetypes.guess_type(tar_member_file)[0] or "application/octet-stream",
                        headers={
                            "Content-Disposition": f"attachment; filename={tar_member_file}",
                            "Content-Length": str(size)
                        }
                    )

                else:
                    fileshare_url = s3_connector.generate_fileshare_url(key=s3_key)

                    self._logger.info(
                        f"[{str(request.id)}]; "
                        f"Redirecting to: {fileshare_url}"
                    )
                    return response.redirect(fileshare_url)
            except Exception as e:
                self._logger.error(f"[{str(request.id)}] Exception occurred: {str(e)}")
                return response.json({"error": "Bad request"}, status=400)

        async def handle_focal_request(request, path):
            self._logger.info(
                f"[{str(request.id)}]; "
                f"Client IP: {request.client_ip}; "
                f"Path args: {request.raw_url.decode('utf-8')}"
            )

            try:
                s3_connector = S3Connector(
                    s3_endpoint=env.S3_CONNECTOR__FOCAL['host_base'],
                    access_key=env.S3_CONNECTOR__FOCAL['access_key'],
                    secret_key=env.S3_CONNECTOR__FOCAL['secret_key'],
                    host_bucket=env.S3_CONNECTOR__FOCAL['host_bucket'],
                    logger=self._logger
                )

                s3_key = path.lstrip("/")

                fileshare_url = s3_connector.generate_fileshare_url(key=s3_key)

                self._logger.info(
                    f"[{str(request.id)}]; "
                    f"Redirecting to: {fileshare_url}"
                )
                return response.redirect(fileshare_url)

            except Exception as e:
                self._logger.error(f"[{str(request.id)}] Exception occurred: {str(e)}")
                return response.json({"error": "Bad request"}, status=400)

        @self._app.get("/focal/<path:path>")
        async def slash_focal_parser(request, path):
            return await handle_focal_request(request, path)


        @self._app.get("/focal/nukleus/<path:path>")
        @basic_auth.focal_auth()
        async def slash_focal_nukleus_parser(request, path):
            return await handle_focal_request(request, f"nukleus/{path}")

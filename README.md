# Czech DHR Landsat processing

## HTTP Server Relay part

Powered by [Sanic](https://sanic.dev/en/).

This HTTP server acts as a relay between an asset link published in CESNET's [STAC catalog](https://stac.cesnet.cz/)
and CESNET's [S3 storage](https://docs.du.cesnet.cz/en/docs/object-storage-s3/s3-service).

### Prerequisites

The **httpServer/.env** file must be filled as follows:

```bash
SANIC__APP_NAME="landsat-httpServer"
SANIC__SERVER_HOST="0.0.0.0"
SANIC__SERVER_PORT="8080"

S3_CONNECTOR__HOST_BASE="https://s3.example.com"
S3_CONNECTOR__HOST_BUCKET="landsat"
S3_CONNECTOR__ACCESS_KEY="1234567890ABCDEFGHIJ"
S3_CONNECTOR__SECRET_KEY="123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcde"
```

Note: file **.env_example** can be renamed to just **.env** and filled by user as desired.

### Settings

There is not much what can be changed here. The main changes can be done by altering **.env** file. See section 
[Prerequisites](#prerequisites).

Be aware that prefix (such as *S3_CONNECTOR* is followed by two underscores *__*)!

### Logging

Logging can be altered using **.env** file as well. For example:

```bash
LOGGER__NAME="LandsatHttpServerLogger"
LOGGER__LOG_DIRECTORY="./log"
LOGGER__LOG_FILENAME="landsat_http_server.log"
LOGGER__LOG_LEVEL=20
```

`LOGGER__LOG_DIRECTORY` can be either relative to **httpServer/** or absolute.

Log is rotated every day at 12:00 AM UTC.

Log levels are as follows:

| READABLE | INTEGER  |
|----------|----------|
| CRITICAL | 50       |
| FATAL    | CRITICAL |
| ERROR    | 40       |
| WARNING  | 30       |
| WARN     | WARNING  |
| INFO     | 20       |
| DEBUG    | 10       |
| NOTSET   | 0        |

## Running

Package is using Docker. Please see the corresponding **docker-compose.yml** file.

There is not much to change. In fact just the port of **httpServer** in :

```docker
dhr-landsat-httpServer:
    ports:
      - "8080:8080"
```

To run the package just install `docker` and run `docker compose up -d` command in both directories.

So to run the **httpServer** execute:

```bash
docker compose up -d
```

Also in **docker-compose.yml** files there is flag `restart: unless-stopped`, and thus after rebooting the machine,
script will restart automatically.

Also package is being automatically published to GitHub Container Repository 
[dhr-download-stac-relay](ghcr.io/matejkaj-cesnet/dhr-download-stac-relay) using workflow specified in
**.github/workflows/publish-ghcr.yml**. It can thus be run as a Kubernetes deployment.

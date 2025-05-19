# Czech DHR Landsat processing
## HTTP Server Relay part

Powered by [Sanic](https://sanic.dev/en/).

HTTP server acts as a relay between an asset link published in STAC catalog and S3 storage.

### Prerequisites

The **http-server/.env** file must be filled as follows:

```bash
SANIC__APP_NAME="landsat_http_server"
SANIC__SERVER_HOST="0.0.0.0"
SANIC__SERVER_PORT="8080"

S3_CONNECTOR__HOST_BASE="https://s3.example.com"
S3_CONNECTOR__HOST_BUCKET="landsat"
S3_CONNECTOR__ACCESS_KEY="1234567890ABCDEFGHIJ"
S3_CONNECTOR__SECRET_KEY="123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcde"
```

### Settings

There is not much what can be changed here. The main changes can be done by altering **.env** file.

### Logging

Logging can be altered using **.env** file as well. For example:

```bash
LOGGER__NAME="LandsatHttpServerLogger"
LOGGER__LOG_DIRECTORY="./log"
LOGGER__LOG_FILENAME="landsat_http_server.log"
LOGGER__LOG_LEVEL=20
```

`LOGGER__LOG_DIRECTORY` can be either relative to **http-server/** or absolute.

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

Package is using Docker. Please see the corresponding **docker-compose.yml** files for [downloader](#downloader)
and [http-server](#http-server).

There is not much to change. In fact just the port of **http-server** in :

```docker
http-server:
    ports:
      - "8080:8080"
```

To run the package just install `docker` and run `docker compose up -d` command in both directories.

So to run the **downloader** in folder `landsat/downloader` execute:

```bash
docker compose up -d
```

and do the same in folder `landsat/http-server` to execute **http-server**.

There is also prepared a little script to run both of these docker containers.

Also in both **docker-compose.yml** files there are flags `restart: unless-stopped`, and thus after rebooting the
machine, scripts will restart automatically.

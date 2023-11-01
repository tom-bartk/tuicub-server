<div align="center">
  <a href="https://github.com/tom-bartk/tuicub-server">
    <img src="https://static.tuicub.com/img/tuicub-logo.png" alt="Logo" width="335" height="115">
  </a>

<div align="center">
<a href="https://jenkins.tombartk.com/job/tuicub-server/">
  <img alt="Jenkins" src="https://img.shields.io/jenkins/build?jobUrl=https%3A%2F%2Fjenkins.tombartk.com%2Fjob%2Ftuicub-server">
</a>
<a href="https://jenkins.tombartk.com/job/tuicub-server/lastCompletedBuild/testReport/">
  <img alt="Jenkins tests" src="https://img.shields.io/jenkins/tests?jobUrl=https%3A%2F%2Fjenkins.tombartk.com%2Fjob%2Ftuicub-server">
</a>
<a href="https://jenkins.tombartk.com/job/tuicub-server/lastCompletedBuild/coverage/">
  <img alt="Jenkins Coverage" src="https://img.shields.io/jenkins/coverage/apiv4?jobUrl=https%3A%2F%2Fjenkins.tombartk.com%2Fjob%2Ftuicub-server%2F">
</a>
<a href="https://jenkins.tombartk.com/job/tuicub-server/">
  <img alt="Interrogate" src="https://jenkins.tombartk.com/userContent/tuicub-server/interrogate.svg">
</a>
<a href="https://www.gnu.org/licenses/agpl-3.0.en.html">
  <img alt="PyPI - License" src="https://img.shields.io/pypi/l/tuicubserver">
</a>
<a href="https://pypi.org/project/tuicubserver/">
  <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/tuicubserver">
</a>
<a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;"></a>
</div>

  <p align="center">
    <b>Back-end</b> for <b><a href="https://tuicub.com">tuicub</a></b> - online multiplayer board game in your terminal.
  </p>
   <p align="center">
    <a href="https://docs.tuicub.com/api"><strong>API Documentation</strong></a>
    ·
    <a href="https://docs.tuicub.com/events"><strong>Events Documentation</strong></a>
  </p>
</div>

## Features

- Fully typed code ([PEP-484](https://peps.python.org/pep-0484/)),
- Testable, clean layered architecture,
- 100% tests coverage,
- All public interfaces documented with [Google style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html),
- Detailed API documentation using the [OpenAPI 3.1.0](https://swagger.io/specification/) specification.

## Overview

![Components diagram of the system](https://static.tuicub.com/img/tuicub-server-overview.png)

1. The **`Client`** connects to the **`Events Server`** to receive real-time notifications about events that occur in the user's game or gameroom,
2. The **`Client`** queries and issues commands to the **`API Server`** via REST API,
3. The **`API Server`** notifies the **`Messaging`** about the **`Client`**'s actions, such as ending a turn,
4. The **`Messaging`** then notifies the **`Events Server`** that an event has occured and it needs to be sent to affected **`Clients`** ,
5. The **`Events Server`** sends the event that occurred to all affected **`Clients`** .

## Installation

### Using `pip`

Tuicubserver is available as [`tuicubserver`](http://localhost:6419) on PyPI:
```sh
pip install tuicubserver
```

### Manually

Start by cloning the repository:

```sh
git clone https://github.com/tom-bartk/tuicub-server.git
cd tuicub-server
```

Then, install the project's dependencies:

```sh
python -m pip install -e .
```

You can now launch the server using the following commands:

```sh
$ python -m src.tuicubserver

Usage: python -m src.tuicubserver [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  api     Start the API server.
  events  Start the events and messages server.
```

## Configuration

### Prerequisites

A [PostgreSQL](https://www.postgresql.org/) database is needed for persistence. Some of `tuicub`'s models utilize the [`ARRAY`](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.ARRAY) data type, hence the need for the PostgreSQL backend.

### `config.toml`

Configuration is done via a `toml` file with a following structure and default values:

```toml
[db]
# Connection string to the database.
url ="postgresql+psycopg2://postgres:postgres@localhost:5432/tuicub"

[logging]
# Path to a file to write logs to.
logfile = "/tmp/tuicubserver.log"

[messages]
# Host of the messages server to connect to.
host = "api.tuicub.com"

# Port of the messages server.
port = 23433

# Secret to use when sending messages.
secret = "changeme"

[events]
# Secret to use when authorizing disconnect callbacks from the events server.
secret = "changeme"
```

To use a custom configuration, set the **`TUICUBSERV_CONF`** environment variable to the path of your config file.

For example:

```sh
TUICUBSERV_CONF=~/mytuicub/myconfig.toml tuicubserver api
```

If the **`TUICUBSERV_CONF`** environment variable is not set or the file does not exist, the app will try to read a `config.toml` file from the current working directory.

## Launching

### API Server

#### The `tuicubserver api` command

Use the `api` command to start the API server, for example:

```sh
TUICUBSERV_CONF=./config.toml tuicubserver api --host 0.0.0.0 --port 8080
```

This will run the underlying [`Flask`](https://flask.palletsprojects.com/en/3.0.x/api/#application-object) application on all available interfaces and port 8080 using the [Werkzeug](https://werkzeug.palletsprojects.com/en/3.0.x/)'s development server.

> [!WARNING]
> This method is suitable only for local use. For production deployment, follow the **Using a WSGI HTTP server** instructions below.

#### Using a WSGI HTTP server

Since the API server is a WSGI application ([PEP-3333](https://peps.python.org/pep-3333/)), you can use any WSGI HTTP server of your choice. The application factory named `create_app` is defined in the `src.tuicubserver.tuicubserver` module.

To start the api server using [gunicorn](https://gunicorn.org/) on all interfaces and port 8080 run:

```sh
TUICUBSERV_CONF=./config.toml gunicorn \
  --bind 0.0.0.0:8080 \
  "src.tuicubserver.tuicubserver:create_app()"
```

### Events Server

Both the Messaging and the Events Server run in the same process. To start it, use the `tuicubserver events` command:

```
Usage: tuicubserver events [OPTIONS]

  Start the events and messages server.

Options:
  --events-port PORT    Port to bind events server to.  [default: 23432]
  --events-host HOST    Host to bind events server to.  [default: 0.0.0.0]
  --messages-port PORT  Port to bind messages server to.  [default: 23433]
  --messages-host HOST  Host to bind messages server to.  [default: 0.0.0.0]
  --api-url URL         Base URL of the API for disconnect callbacks.
                        [default: https://api.tuicub.com]
  --help                Show this message and exit.
```

Following example uses the default host and ports, and a custom API Server:

```sh
TUICUBSERV_CONF=./config.toml tuicubserver events --api-url http://localhost:8080
```


## Documentation

### API Docs

Visit the [**API Documentation**](https://docs.tuicub.com/api) for a detailed description of all API endpoints.

##### Screenshot

![Screenshot of the API documentation](https://static.tuicub.com/img/tuicub-server-api-docs-preview.png)

### Events Docs

**tuicub** gameplay is driven by asynchronous events delivered over TCP sockets.<br/><br/>Every event is fully documented in the [**Events Documentation**](https://docs.tuicub.com/events).

##### Screenshot

![Screenshot of the events documentation](https://static.tuicub.com/img/tuicub-server-events-docs-preview.png)


## License
![AGPLv3](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)
```monospace
Copyright (C) 2023 tombartk 

This program is free software: you can redistribute it and/or modify it under the terms
of the GNU Affero General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see https://www.gnu.org/licenses/.
```

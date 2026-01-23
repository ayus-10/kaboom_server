# Kaboom Server

This repository contains the backend service for Kaboom. This is an API-only service intended to be used with a separate frontend.

## Features

- Visitors can start conversations (anonymous)
- Conversations begin in a pending state
- Admin users can accept pending conversations
- Real-time messaging within conversations
- Support for multiple projects
- Multiple admins can be a part of a project


___


## Setup
Note: This project uses [Poetry](https://python-poetry.org/) for packaging.

### To install dependencies, run:

```bash
poetry install
```

___

## Development Commands

### Linting and Type Checking:

```bash
poetry run ruff check
poetry run pyright
```

### Creating database migration:

```bash
alembic revision --autogenerate -m "migration message"
```

### Undo the most recent migration:
```bash
alembic downgrade -1
```

### Apply all migrations:
```bash
alembic upgrade head
```

### Running the Server
```bash
poetry run uvicorn app.main:app --reload
```

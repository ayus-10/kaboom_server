# Kaboom Server

This repository contains the backend service for Kaboom. This is an API-only service intended to be used with a separate frontend.

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
poetry run alembic revision --autogenerate -m "migration message"
```

### Undo the most recent migration:
```bash
poetry run alembic downgrade -1
```

### Apply all migrations:
```bash
poetry run alembic upgrade head
```

### Running the Server
```bash
poetry run uvicorn app.main:app --reload
```

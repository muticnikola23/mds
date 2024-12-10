# FastAPI Application with Alembic and Docker

This repository contains a FastAPI application with database migrations managed by Alembic.
The application is containerized using Docker for easy deployment and scalability.

---

## Features

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs.
- **Alembic**: For database migrations.
- **Docker**: Containerized deployment for consistency and simplicity.

---

## Project Structure

```plaintext
├── dependencies/       # Fastapi dependencies
├── migrations/         # Alembic migration files and fixtures
├── models/             # Database models
├── tests/              # Unit and integration tests
├── main.py             # FastAPI application entry point
├── Dockerfile          # Docker build file
├── .dockerignore       # Docker ignore patterns
├── poetry.lock         # Poetry dependency tree
├── pyproject.toml      # Project definition file
├── alembic.ini         # Alembic configuration file
└── README.md           # Project documentation

```


## How to run
```bash 
docker build --no-cache --progress=plain -t mds .  # Build docker image
docker run -d -it -p 8000:8000 mds  # Run Created Image


```





# Org Structure API

Test assignment: REST API для управления организационной структурой компании (департаменты и сотрудники).

## Stack

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Alembic
- Pydantic v2
- Docker / docker-compose
- pytest

## Project Structure

```
app/
  api/routes/      # HTTP endpoints
  core/            # config, db
  models/          # ORM models
  schemas/         # Pydantic schemas
  services/        # business logic

tests/             # pytest tests
alembic/           # database migrations
```

## Setup & Run

Клонировать репозиторий:

```bash
git clone https://github.com/zDarli/org-structure-api
cd org-structure-api
```

Запустить сервисы:

```bash
docker-compose up --build
```

После запуска API будет доступно по адресу:

```
http://localhost:8001
```

Swagger документация:

```
http://localhost:8001/docs
```

## API

- POST /departments
- POST /departments/{id}/employees
- GET /departments/{id}
- PATCH /departments/{id}
- DELETE /departments/{id}

## Database Migrations

Применить миграции:

```bash
docker compose exec api alembic upgrade head
```

## Run Tests

```bash
docker compose exec api pytest
```

## Delete Modes

- **cascade** — удаляет департамент, всё поддерево и сотрудников
- **reassign** — переносит сотрудников и дочерние департаменты в другой департамент и удаляет только выбранный департамент
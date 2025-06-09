# EBS Product & Pricing API

This is a Django-based API for managing product categories, products, and historical price records. It includes endpoints for calculating average prices over time, grouped by week or month.

---

## Requirements

- Docker & Docker Compose
- Python 3.10+

---

## Getting Startez

### 1. Start the application with Docker Compose

```bash
docker compose up -d --build
```

This command builds and starts the following services:

- `postgres` – PostgreSQL database container
- `app` – Django API container (served via Gunicorn on port 8000)

---

## Running Tests & Code Checks

### Run all tests

```bash
make tests
```

> Runs the Django test suite.

### Linting & formatting check

```bash
make check
```

> Runs code style checks using tools like `black`, `isort`, ``ruff.

---

## Load Sample Data (5 Categories, 20 Products, 60 Prices)

To populate the database with sample data for testing:

1. Access the Django container:

```bash
docker compose exec app sh
```

2. Run the sample data script:

```bash
python manage.py shell < load_sample_data.py
```

This will create:

- 5 categories
- 20 products randomly assigned to categories
- 3 prices per product:
  - 2 with defined start and end dates
  - 1 open-ended (with no `end_date`, meaning it is currently active)

---

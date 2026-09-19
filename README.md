# OrderFlow

OrderFlow is a realistic order and inventory management application built as the application under test for QA engineering practice. It is a modular monolith: a FastAPI REST API owns all business rules and PostgreSQL persistence, while a React single-page application provides role-aware operational workflows.

## Architecture and technology

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL, JWT bearer authentication, Argon2 password hashing
- **Frontend:** React, TypeScript, Vite, React Router, Fetch API, responsive accessible HTML/CSS
- **Database:** PostgreSQL with foreign keys, unique/index/check constraints, numeric money fields, and enum status/role types
- **API documentation:** FastAPI-generated OpenAPI and Swagger UI

```text
qa-engineering-training-lab/
├── backend/
│   ├── alembic/                 # Migration environment and schema revisions
│   ├── app/
│   │   ├── api/                 # Thin HTTP route handlers
│   │   ├── core/                # Configuration and authentication
│   │   ├── database/            # SQLAlchemy base and session dependency
│   │   ├── models/              # ORM entities
│   │   ├── schemas/             # Request/response models
│   │   ├── services/            # Transactions and business rules
│   │   └── main.py              # FastAPI application
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── seed.py
│   └── .env.example
├── frontend/
│   ├── src/                     # API, components, context, pages, and types
│   ├── package.json
│   └── .env.example
└── README.md
```

## Prerequisites and PostgreSQL

Install Python 3.11+, Node.js 20+ with npm, and PostgreSQL 14+. Start PostgreSQL, then create a local role and database:

```bash
psql -d postgres -c "CREATE ROLE orderflow LOGIN PASSWORD 'orderflow';"
createdb -O orderflow orderflow
```

If those names already exist, keep them and ensure the connection values below match. OrderFlow never substitutes SQLite or an in-memory database.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Backend environment variables:

| Variable | Purpose | Development example |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL | `postgresql+psycopg://orderflow:orderflow@localhost:5432/orderflow` |
| `JWT_SECRET` | Token signing key; replace locally | no production default |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session duration | `480` |
| `CORS_ORIGINS` | Comma-separated browser origins | `http://localhost:5173` |
| `LOG_LEVEL` | Application log level | `INFO` |
| `ENABLE_DEV_PASSWORD_RESET` | Enables email-only password reset for local training | `true` |

Apply the schema, verify migration drift, and load repeat-safe seed data:

```bash
alembic upgrade head
alembic check
python seed.py
```

`seed.py` is idempotent. Start the API from `backend/`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Other useful migration commands are `alembic current`, `alembic history`, `alembic downgrade -1`, and `alembic upgrade head`.

## Frontend setup

In another terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

`VITE_API_URL` sets the base API URL and defaults to `http://localhost:8000/api/v1`. Validate a production bundle with `npm run build`.

## URLs and local development credentials

- Frontend: <http://localhost:5173>
- API: <http://localhost:8000/api/v1>
- Health: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

| Role | Email | Password |
|---|---|---|
| Admin | `admin@orderflow.local` | `Admin123!` |
| Staff | `staff@orderflow.local` | `Staff123!` |

These accounts are local development data only. Admins manage all resources. Staff can view products and manage customers/orders, but API authorization prevents them from managing users or changing products.

## Main business rules

- User/customer emails, product SKUs, and generated order numbers are unique. Password hashes are never exposed.
- Inactive users cannot sign in. Only admins may manage users and products.
- Product price and stock cannot be negative; money uses `NUMERIC(12,2)` rather than floating point.
- Orders require at least one unique active product and a positive quantity within available stock.
- The backend copies current prices, calculates totals, generates order numbers, and decrements stock atomically with row locks.
- Cancelling a pending or paid order restores stock atomically.
- Valid transitions are `pending → paid`, `pending → cancelled`, `paid → shipped`, `paid → cancelled`, and `shipped → delivered`; every other transition returns HTTP 409.
- Customers and products referenced by orders cannot be deleted.

## REST API

All application endpoints require a bearer token except login and health.

| Area | Endpoints |
|---|---|
| System | `GET /health` |
| Authentication | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Account access | `POST /api/v1/auth/register`, `POST /api/v1/auth/reset-password` |
| Users (admin) | `GET/POST /api/v1/users`, `GET/PUT /api/v1/users/{id}`, `PATCH /api/v1/users/{id}/status` |
| Customers | `GET/POST /api/v1/customers`, `GET/PUT/DELETE /api/v1/customers/{id}` |
| Products | `GET/POST /api/v1/products`, `GET/PUT/DELETE /api/v1/products/{id}`, `PATCH /api/v1/products/{id}/status` |
| Orders | `GET/POST /api/v1/orders`, `GET /api/v1/orders/{id}`, `PATCH /api/v1/orders/{id}/status` |
| Dashboard | `GET /api/v1/dashboard/summary` |

Collections expose relevant `page`, `page_size`, `search`, `sort_by`, `sort_order`, `status`, and `is_active` parameters with pagination metadata. Swagger UI documents exact schemas and validation constraints.

Self-registration always creates an active **staff** account; it cannot be used to assign administrator access. The password-reset screen accepts an email address and a new password without email verification because it is intended only for this local QA training application. Set `ENABLE_DEV_PASSWORD_RESET=false` outside local development to remove that endpoint.

## Deliberate exclusions

This repository contains the working application only. Automated tests, test fixtures/frameworks, Docker files, CI/CD pipelines, and GitHub Actions workflows are deliberately excluded for the QA engineer to add separately.

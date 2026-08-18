# RESPOND-ER: Adaptive Community Disaster Intelligence Platform

RESPOND-ER is a disaster response, resource coordination, and community recovery platform. It provides a command center for administrators and responders, alongside public tools for citizens.

## Implemented features

### Module 1: Disaster Response Management

1. Disaster dashboard with active-event maps, personnel status, and supply statistics
2. Citizen SOS requests with location, photo upload, and request status tracking
3. AI emergency prioritization with Gemini integration and an offline rules fallback
4. Infrastructure damage reporting and live map markers
5. Missing and found person management
6. Donation management

### Module 2: Resource Coordination

7. Community resource mapping
8. Smart volunteer matching and dispatch
9. Shelter management
10. Relief distribution tracking
11. Relief fairness dashboard

### Module 3: AI Decision Support

12. AI Disaster Assistant Chatbot with HTMX conversation view and rules-based fallback
13. Community Trust Score representing data validation based on photo corroboration and geolocation verification
14. Household Vulnerability Index with auditable scoring, combined AI/HVI ranking, and administrator override history
15. AI Predictive Resource Shortage (depletion rate estimations and warning alerts)
16. Recovery Progress Dashboard with disaster baselines, verified milestones, progress percentages, weekly trends, evidence, and public filters

### Utility Portals

- Platform Settings portal for tuning priority triage weights (AI vs HVI) and dark mode preference persistence
- Support portal featuring dynamic FAQ accordions and sqlite support ticket submissions
- Interactive Language Changer (English ⇄ বাংলা translations mapped via Jinja context context wrappers)
- Donations portal in the navbar and public layout

## Technology

- FastAPI and asynchronous Python
- SQLAlchemy 2 with `aiosqlite`
- Alembic database migrations
- SQLite for local development
- Jinja templates, Bootstrap 5, and vanilla CSS
- Leaflet maps and Chart.js charts
- Google Gemini for emergency triage when an API key is configured
- Pytest and HTTPX for automated testing

## Project structure

```text
ACDIP/
|-- app/
|   |-- models/          # Domain-grouped SQLAlchemy models
|   |-- routers/         # FastAPI endpoints grouped by domain
|   |-- services/        # Triage, vulnerability, priority, and recovery logic
|   |-- static/          # Styles and local user uploads
|   |-- templates/       # Jinja pages and reusable components
|   |-- config.py        # Environment-backed settings
|   |-- database.py      # Engine, sessions, and migration-head verification
|   |-- presenters.py    # Small HTML fragment presenters
|   |-- web.py           # Templates and upload handling
|   `-- main.py          # Application assembly
|-- migrations/          # Ordered Alembic schema revisions
|-- tests/               # Automated tests using an isolated database
|-- alembic.ini          # Alembic configuration
|-- conftest.py          # Disposable test database and upload lifecycle
|-- seed.py              # Guarded full demo-data seeder
|-- seed_module2.py      # Additive Module 2 demo-data seeder
|-- ARCHITECTURE.md      # Package boundaries and database policy
`-- requirements.txt
```

## Local setup

Run commands from the repository root.

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

Using `python -m pip` ensures packages such as Alembic are installed into the active interpreter rather than a different system Python installation.

### 3. Configure the environment

The application loads an optional `.env` file from the repository root. Example:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./respond_er.db
GEMINI_API_KEY=
SECRET_KEY=replace-this-outside-local-development
```

If `DATABASE_URL` is omitted, the application uses `respond_er.db` in the repository root. Never commit `.env` or local database files.

## Database workflow

Alembic is the only supported way to create or change the database schema. Application startup does not create tables or modify columns. It verifies that the database is at the current migration head and stops with an actionable error when an upgrade is required.

### Create a fresh database

Apply every migration, then optionally add demonstration data:

```powershell
python -m alembic upgrade head
python seed.py
```

`seed.py` only populates an empty schema. It refuses to overwrite a populated database.

### Upgrade an existing managed database

Back up the database file before applying a new revision, particularly when using SQLite. Then run:

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

Do not use `alembic stamp` on an unknown or legacy database merely to bypass an error. Stamping records a revision without applying its schema changes. Reconcile and back up an unmanaged database before bringing it under migration control.

### Seeding rules

- `python seed.py` adds the complete demo dataset only when all application tables are empty.
- `python seed_module2.py` safely adds missing Module 2 demo records without clearing existing data.
- `python seed.py --reset` drops and rebuilds all application tables. It is destructive and must only be used intentionally after making a backup.
- Never run a reset command against a database containing citizen submissions or operational records.

### Current migration sequence

- `0001_baseline`: creates the baseline application schema
- `0002_reconcile`: reconciles known legacy schema drift
- `0003_shelters`: normalizes shelter columns
- `0004_f14_expand`: adds normalized F14 assessments and priority override history
- `0005_f16_recovery`: adds recovery baselines and verified recovery milestones
- `ac5005b05cba`: appends trust score and trust breakdown columns to emergency requests and damage reports
- `bad524bb968f`: creates support tickets table to record logged support submissions

Legacy F14 columns remain temporarily as a rollback-safe dual-write mirror. Their removal, if desired, must be handled by a later reviewed migration.

## Run the application

```powershell
python -m uvicorn app.main:app --reload
```

Key pages:

- Command center: `http://127.0.0.1:8000/`
- Citizen SOS portal: `http://127.0.0.1:8000/sos`
- Missing persons: `http://127.0.0.1:8000/missing`
- Resources: `http://127.0.0.1:8000/resources`
- Shelters: `http://127.0.0.1:8000/shelters`
- Distribution tracking: `http://127.0.0.1:8000/tracking`
- Recovery dashboard: `http://127.0.0.1:8000/recovery`

## Testing

Run the full suite before committing:

```powershell
python -m pytest -q
python -m alembic check
```

Pytest creates `.test_respond_er.db` and `.test_uploads`, runs the real migration chain and seed process, and removes those test artifacts afterward. Tests do not write to `respond_er.db`.

## Collaboration and commits

1. Create a feature branch.
2. Add a reviewed Alembic revision for every schema change.
3. Do not commit `.env`, SQLite databases, backups, uploaded evidence, or test artifacts.
4. Run the complete test suite and `alembic check`.
5. Inspect `git status` before staging, then commit the source and migration files.

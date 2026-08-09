# RESPOND-ER: Adaptive Community Disaster Intelligence Platform (ACDIP)

RESPOND-ER is an AI-powered disaster response, resource coordination, and community recovery platform. It provides a real-time command center interface for administrators and volunteers, alongside public SOS emergency request submission tools for citizens.

---

## 🛠️ Tech Stack
- **Backend:** Python 3.10+ / FastAPI (Asynchronous framework)
- **Database ORM:** SQLAlchemy with `aiosqlite` (Async SQLite driver for local development)
- **Frontend CSS:** Vanilla CSS + Bootstrap 5 (Responsive Layout matching Figma)
- **Frontend Interactivity:** HTML5, HTMX (for dynamic updates without bloated JS frameworks)
- **Maps:** Leaflet.js with OpenStreetMap (cost-effective, high-performance mapping)
- **AI Triage:** Gemini API integration (asynchronous background queue)

---

## 📂 Project Structure
```
ACDIP/
├── app/
│   ├── static/          # CSS, JS, and image assets
│   │   └── css/
│   │       └── style.css
│   ├── templates/       # HTML templates (Jinja2)
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── components/
│   ├── config.py        # Settings and environment configuration
│   ├── database.py      # Async database connection and sessionmaker
│   ├── models.py        # SQLAlchemy database models
│   └── main.py          # FastAPI main application & routing
├── tests/               # Pytest test suite
│   └── test_dashboard.py
├── requirements.txt     # Python package dependencies
├── seed.py              # Script to populate mock data for testing
└── .gitignore           # Ignored files (venv, sqlite db, etc.)
```

---

## 🚀 Getting Started

### 1. Clone & Setup Virtual Environment
```bash
# Navigate to project directory
cd ACDIP

# Create python virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
This creates the local SQLite database file `respond_er.db` and populates it with the Figma dashboard's initial events, inventory, and AI priority queue requests:
```bash
python seed.py
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload
```
Open your browser and navigate to `http://127.0.0.1:8000` to view the command center.

---

## 🧪 Running Tests
We use `pytest` and `httpx` to run tests asynchronously:
```bash
pytest
```

---

## 🤝 Collaboration & Merging
1. Always create a new branch for any feature: `git checkout -b feature/your-feature-name`.
2. Do not commit database files (`*.db`) or virtual environments (`venv/`).
3. Seed scripts (`seed.py`) should be updated if new models are added.
4. Ensure all unit tests pass before pushing and opening a pull request.

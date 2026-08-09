# RESPOND-ER: Adaptive Community Disaster Intelligence Platform (ACDIP)

RESPOND-ER is an AI-powered disaster response, resource coordination, and community recovery platform. It provides a real-time command center interface for administrators and responders, alongside a public SOS portal for citizens.

---

## 🚀 Current Project State

We have completed the core foundation of **Module 1 (Disaster Response Management)**, including:
1. **Feature 1: Disaster Dashboard** (Dhaka Operations Command Center view, interactive Leaflet.js maps, active disaster lists, supply statistics, and personnel allocation).
2. **Feature 2: Emergency Relief Request** (Citizen SOS portal with counter widgets, browser geolocation auto-detection, photo upload capability, and session-based request status tracking).
3. **Feature 3: AI Emergency Prioritization** (Gemini API integration that triages citizen requests asynchronously in background threads, featuring a rules-based fallback engine for offline reliability).
4. **Feature 5 Schema Foundation** (Pre-designed missing & found persons directory layouts and family updates database structure).

---

## 🛠️ Tech Stack
- **Backend Framework:** FastAPI (Asynchronous Python 3.10+)
- **Database Engine:** SQLAlchemy with `aiosqlite` (Async local SQLite database)
- **AI Integration:** Google Generative AI (Gemini API `gemini-1.5-flash` model for async dispatch triage)
- **Frontend Framework:** Vanilla CSS + Bootstrap 5 (Customized colors matching Figma specifications)
- **Interactivity:** HTML5 & HTMX (for fast updates on low-bandwidth networks)
- **Geospatial Maps:** Leaflet.js with OpenStreetMap (light cartographic styles)

---

## 📂 Project Structure
```
ACDIP/
├── app/
│   ├── static/          # Custom styles, images, and upload storage
│   │   ├── css/
│   │   │   └── style.css
│   │   └── uploads/     # Citizen photo submissions
│   ├── templates/       # HTML page templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── sos.html
│   │   ├── missing_persons.html
│   │   └── components/
│   ├── ai_service.py    # Gemini API prompt schema and heuristic triage rules
│   ├── config.py        # Settings loader
│   ├── database.py      # SQLAlchemy async connection engine
│   ├── models.py        # Database tables
│   └── main.py          # Routing endpoints and background tasks
├── tests/               # Pytest testing suite
│   ├── test_dashboard.py
│   ├── test_sos.py
│   └── test_ai.py
├── requirements.txt     # Dependency lists
├── seed.py              # Mock data database seed script
└── README.md
```

---

## 🚀 Local Setup Instructions

### 1. Clone & Set Up Virtual Environment
```bash
# Navigate to the workspace
cd ACDIP

# Create virtual environment
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
This creates the local database file `respond_er.db` and populates it with active events, inventory counts, and triage requests matching the Figma screens:
```bash
python seed.py
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload
```
Open your browser and navigate to:
- **Command Center Dashboard:** `http://127.0.0.1:8000/`
- **Citizen SOS Portal:** `http://127.0.0.1:8000/sos`
- **Missing Persons Grid:** `http://127.0.0.1:8000/missing`

---

## 🧪 Automated Testing
We use `pytest` and `httpx` to verify API routing and asynchronous database updates:
```bash
python -m pytest
```

---

## 🤝 Collaborative Branches & Workflow
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Keep `.db` files and local variables outside git (handled by `.gitignore`)
3. Ensure the test suite passes (`python -m pytest`) before committing
4. Push and create a pull request to `main`

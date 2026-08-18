# 🚨 RESPOND-ER: Adaptive Disaster Intelligence Platform

RESPOND-ER is a modern, real-time disaster coordination and resource optimization platform designed to bridge the gap between emergency responders, community NGOs, and public citizens during crisis events.

---

## 👥 Persona-Driven Interfaces
The platform dynamically alters its layout, navigation tabs, and system settings based on the active session persona. Toggle these easily using the **Profile Menu** in the header:

*   **👑 Command Center Admin:** Full system access. Edit HVI sliders, configure Gemini keys, review auditable priority overrides, and trigger dispatch calls.
*   **🚛 Field NGO Responder:** Access to resource mapping, shelter bed checkouts, recovery milestone tracking, and relief logging. Hides sensitive settings.
*   **🏡 Public Citizen:** Streamlined, secure anonymous view. Submit SOS signals, request resources, register missing persons, and donate supplies.

---

## ⚡ Key Implemented Capabilities

### 1. Disaster Response Management (Module 1)
*   **Live Incident Map:** Real-time leaflet map plotting active flood zones, fires, infrastructure damage, and citizen SOS clusters.
*   **Citizen SOS Registry:** Interactive form with photo uploads, live geolocation support, and tracking status.
*   **AI Triage Prioritization:** Combined logic analyzing raw vulnerability scores alongside real-time NLP keywords (uses Gemini API with offline rules backup).
*   **Missing Persons Portal:** Timeline updates, SAFE verification markers, and public search logs.

### 2. Resource Coordination (Module 2)
*   **Community Resource Map:** Corroborates active water pumps, boats, power generators, and NGO supply centers.
*   **Shelter Registry:** Track available beds, medical aid stocks, food days remaining, and register volunteers.
*   **Relief Distribution Tracker:** Detailed audit log verifying resource delivery quantities, destination districts, and duplicate warning flags.

### 3. AI Decision Support & Auditing (Module 3)
*   **Household Vulnerability Index (HVI):** Auditable scoring algorithm ranking incidents by risk demographics (elderly, pregnant, children, disabled).
*   **AI Priority Override Logs:** Full audit timeline tracking all manual override history events and justifications.
*   **AI Predictive Shortages:** Depletion-rate math services estimating supply depletion times and overcrowding alerts.
*   **Language Switcher:** Instant translation between **English (EN)** and **Bangla (বাংলা)** across all views.
*   **Interactive Chatbot:** HTMX-driven chatbot sidebar providing disaster safety advice and keyword-based recommendations.

---

## 🛠️ Technology Stack
*   **Core:** FastAPI, Asynchronous Python, Uvicorn, Jinja2 Templates
*   **Database:** SQLite, SQLAlchemy 2 (via `aiosqlite`), Alembic Migrations
*   **UI/UX:** Bootstrap 5, Vanilla CSS (with dynamic Dark Mode support)
*   **Integrations:** Google Gemini API, Leaflet Maps

---

## 🚀 Quick Setup & Run

### 1. Environment Setup
```powershell
# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
python -m pip install -r requirements.txt
```

### 2. Database Initialization
```powershell
# Run database migrations and seed design data
python -m alembic upgrade head
python seed.py --reset
```

### 3. Start Development Server
```powershell
python -m uvicorn app.main:app --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🧪 Testing & Validation
Verify changes using the testing database suite:
```powershell
python -m pytest
```
*Note: Pytest automatically creates an isolated test database (`.test_respond_er.db`), executes migrations, runs tests, and cleans up artifacts afterwards.*

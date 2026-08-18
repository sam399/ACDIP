# 🚨 RESPOND-ER: Adaptive Disaster Intelligence Platform

RESPOND-ER is a modern, real-time disaster coordination and resource optimization platform designed to bridge the gap between emergency responders, community NGOs, and public citizens during crisis events.

---

## 👥 Persona-Driven Interfaces
The platform dynamically alters its layout, navigation tabs, and system settings based on the active session persona. Toggle these easily using the **Profile Menu** in the header:

*   **👑 Command Center Admin:** Full system access. Edit HVI sliders, configure Gemini keys, review auditable priority overrides, and trigger dispatch calls.
*   **🚛 Field NGO Responder:** Access to resource mapping, shelter bed checkouts, recovery milestone tracking, and relief logging. Hides sensitive settings.
*   **🏡 Public Citizen:** Streamlined, secure anonymous view. Submit SOS signals, request resources, register missing persons, and donate supplies.

---

## ⚡ Implemented Capabilities

### 🔹 Core System Modules
*   **Live Incident Map (Module 1):** Real-time leaflet map plotting active flood zones, fires, infrastructure damage, and citizen SOS clusters.
*   **Citizen SOS Registry (Module 1):** Interactive form with photo uploads, live geolocation support, and tracking status.
*   **AI Triage Prioritization (Module 1):** Combined logic analyzing raw vulnerability scores alongside real-time NLP keywords (uses Gemini API with offline rules backup).
*   **Missing Persons Portal (Module 1):** Timeline updates, SAFE verification markers, and public search logs.
*   **Community Resource Map (Module 2):** Corroborates active water pumps, boats, power generators, and NGO supply centers.
*   **Shelter Registry (Module 2):** Track available beds, medical aid stocks, food days remaining, and register volunteers.
*   **Relief Distribution Tracker (Module 2):** Detailed audit log verifying resource delivery quantities, destination districts, and duplicate warning flags.
*   **Household Vulnerability Index (Module 3):** Auditable scoring algorithm ranking incidents by risk demographics (elderly, pregnant, children, disabled).
*   **Recovery Progress Dashboard (Module 3):** Disaster baselines, verified milestones, progress percentages, weekly trends, evidence, and public filters.

### 🔹 Platform Integrations & Non-Module Features
*   **🌓 Adaptive Dark Mode:** Instant CSS variables theme toggle spanning all pages, headers, timelines, and cards.
*   **🌐 English ⇄ Bangla Translator:** Dynamic global translation system mapping Jinja2 text elements dynamically.
*   **⚙️ Platform Settings Panel:** Range sliders to set AI vs HVI triage weight balances, secrets input fields, and custom auto-refresh interval loops.
*   **🛡️ System Audit Log Registry:** Compliance timeline logging manual priority overrides, previous vs new priority rankings, and admin justifications.
*   **❓ Support Helpdesk & FAQ accordions:** Dynamic FAQ panels detailing HVI/Trust score calculations alongside SQLite-backed ticket logger lists.
*   **🔔 Notification Dropdown Bell:** Dynamic dropdown listing priority warnings, water shortages, and direct redirection links to dashboard incidents.
*   **💬 AI Chatbot Assistant:** HTMX-driven chatbot conversation sidebar with Gemini responses and keywords rules backup.

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

EpiVibe Projects + SQLite integration

Backend (PowerShell, in EpiVibe\backend):
  ..\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
Alternative if venv missing: py -3.11 -m pip install -r requirements.txt; py -3.11 -m uvicorn app.main:app --reload --port 8000
Check http://localhost:8000/api/health and http://localhost:8000/docs

Frontend (separate PowerShell, in EpiVibe\frontend):
  npm install
  npm run dev
Open http://localhost:5173/projects

Old localStorage drafts are migrated on first Projects/Home/Event Brief load, and removed from localStorage only after successful upload. Start the backend BEFORE opening the frontend.
SQLite database is created at backend/data/epivibe.sqlite3. Do not delete this file when updating source code.

The Start AI Research button validates and saves the brief, but the actual research workflow is not yet implemented.

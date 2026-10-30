# EpiVibe — AI Event Strategist

**Plan culturally relevant events with AI-powered audience insights and actionable execution plans.**

EpiVibe is an AI-assisted event strategy application for event planners, event management agencies, marketing teams, venue operators, and organizations planning audience-focused experiences. It combines cultural intelligence from the **Qloo API** with **Google Gemini** to help users move from an initial event brief to event concepts and an operational execution plan. Shopping mall events are one example use case, not the limit of the product.

> **Hackathon project:** Qloo Agentic Hackathon 2026
> **Live demo:** Coming soon — public deployment in progress
> **Status:** Locally tested prototype; public deployment and judge-access testing pending

## The Problem

Planning and managing successful events requires more than generating creative ideas. Event planners and agencies must understand their target audiences, account for cultural and local preferences, develop engaging concepts, manage budgets and venue constraints, coordinate people and resources, and turn plans into executable tasks. These activities are often handled across disconnected research, documents, and workflows. Generic AI-generated suggestions may sound appealing but lack a clear connection to audience insight, budget decisions, and practical delivery requirements.

**The challenge:** How can event professionals move efficiently from understanding their audience to choosing a relevant event concept and building a realistic execution plan?

## Our Solution

EpiVibe guides planners through a four-stage workflow:

| Stage | What it does |
| --- | --- |
| **1. Event Brief** | Capture event type, title, venue, audience, dates, objectives, budget, and additional context. |
| **2. AI Research** | Generate research-informed planning insights using Qloo cultural intelligence and AI analysis. |
| **3. Event Concept** | Review proposed event concepts, examine activities and budget, and refine a selected concept through conversational AI. |
| **4. Execution Plan** | Generate milestones, tasks, resource needs, budget allocations, marketing actions, operational considerations, and risks. |

### Key Capabilities

- **Culturally informed planning:** Incorporates Qloo-powered audience and cultural signals into event research.
- **Event concept generation:** Turns a planning brief into event ideas and activity proposals.
- **Conversational refinement:** Request changes, review proposed updates, compare versions, and apply or discard a proposal.
- **Budget-aware planning:** Displays approved working budgets and allocations throughout the planning process.
- **Execution planning:** Produces timelines, responsibilities, resources, marketing activities, and risk considerations.
- **Project management:** Save, reopen, and manage event planning projects.
- **Export:** Download an execution plan as a PDF or JSON file.

## Who It Is For

- Professional event planners and event management agencies
- Corporate event and internal communications teams
- Marketing, brand activation, and community engagement agencies
- Venue operators, convention centers, and hospitality teams
- Shopping mall and retail destination management teams
- Organizations planning cultural, entertainment, community, and promotional events

## Example Use Case

An event management team wants to organize a three-day family heritage festival at a Chennai shopping mall with a budget of **₹15,00,000**. EpiVibe captures the brief, supports culturally relevant research, generates concepts, allows the planner to refine an approved direction, and produces an execution plan covering activities, milestones, staffing, budget, marketing, and operational risks. This mall-based scenario demonstrates the workflow; the broader product is intended for different types of events and organizers.

This is an illustrative tested scenario, not a claim that a real-world event or vendor booking has been completed.

## Architecture

```text
Browser
   |
   v
React + TypeScript + Vite frontend
   |
   | HTTP / JSON
   v
Python FastAPI backend
   |-- Project and planning workflows
   |-- Qloo cultural intelligence integration
   |-- Gemini AI integration
   |-- SQLite persistence (local development)
   |-- Execution-plan PDF export
```

### Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI generation and refinement | Google Gemini API |
| Cultural intelligence | Qloo API |
| Local persistence | SQLite |
| Export | PDF and JSON |

## Project Structure

```text
EpiVibe/
├── frontend/             # React / TypeScript / Vite application
├── backend/
│   ├── app/              # FastAPI routes, modules, agents, integrations
│   ├── tests/            # Backend tests
│   └── requirements.txt  # Python dependencies
├── docs/                 # Architecture, API, workflow, design documentation
├── scripts/              # Local development scripts
└── README.md
```

## Run Locally

### Prerequisites

- Python 3.11 or another compatible Python version
- Node.js and npm compatible with the project's Vite version
- Valid Qloo and Gemini API credentials for AI-powered workflows

### 1. Clone the repository

```bash
git clone <YOUR_PUBLIC_REPOSITORY_URL>
cd EpiVibe
```

### 2. Configure and start the backend

**Windows PowerShell:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env` locally and provide your own credentials:

```dotenv
QLOO_API_KEY=your_qloo_api_key
QLOO_API_BASE=your_qloo_api_base_url
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Then start the API **from the `backend` directory**:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health endpoint: `http://127.0.0.1:8000/api/health`

### 3. Configure and start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
```

Create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```powershell
npm run dev
```

Open `http://localhost:5173`.

> **Setup note:** The current source snapshot contains empty example environment files and a minimal backend dependency manifest. The repository must be audited and its setup instructions verified on a clean machine before these instructions can be considered fully validated.

## Demonstrating EpiVibe

1. Select **Create New Event**.
2. Enter the event brief, including target audience and budget.
3. Run **AI Research** and review the results.
4. Explore an **Event Concept**, then request and review a refinement.
5. Apply an approved change or discard the proposal.
6. Generate the **Execution Plan**.
7. Review the timeline, activities, budget, marketing, operations, and risks.
8. Export the plan to PDF or JSON.

**Judge-access demo URL:** To be added after deployment and external end-to-end testing.

## How Qloo Fits

Qloo is used as the cultural intelligence source within the AI research workflow. Gemini supports natural-language generation and refinement. EpiVibe's intended value is the **connection between audience/cultural signals, planner decisions, and actionable event delivery**, rather than generating a standalone list of generic ideas.

Generated recommendations are planning proposals. They are **not** confirmations of venue permissions, vendor availability, prices, audience outcomes, or regulatory approvals.

## Privacy and Security

- API credentials belong in backend environment variables and must **never** be committed to Git.
- The frontend must not contain Qloo or Gemini secret keys.
- Local databases, `.env` files, virtual environments, caches, and build artifacts must be excluded from the public repository.
- Public deployment requires appropriate CORS settings, secure backend configuration, and a persistent storage decision.

## Current Limitations

- The supplied project snapshot has been tested locally; a publicly accessible deployment has not yet been verified.
- SQLite is used for local persistence; production persistence requires a deliberate hosting/storage configuration.
- AI-generated schedules, costs, risks, and recommendations require human review before real-world execution.
- The execution plan is a planning aid, not an automated vendor booking or venue management system.

## License

An open-source license will be added to the repository before hackathon submission. **No license is granted by this README alone.**

## Project Team

Developed by **Epiware** for the Qloo Agentic Hackathon 2026.

---

*EpiVibe — Every Great Event Begins With Understanding People.*

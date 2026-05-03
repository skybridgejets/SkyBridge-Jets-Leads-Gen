# SkyBridge Jets — AI Lead Generation Platform

A production-ready multi-agent lead generation platform for SkyBridge Jets, a UK private jet brokerage targeting UHNW clients, PAs, estate managers, chiefs of staff, family offices, luxury travel advisors, concierge firms, yacht brokers, luxury real estate firms, and founders.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (with npm)
- **PostgreSQL 14+**
- **OpenAI API key** (for GPT-4o outreach generation)

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd skybridge-jets
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit ../.env with your API keys and database URL

# Create the database
createdb skybridge  # or use your preferred method

# Start the backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### 4. Run the Pipeline End to End

1. Open `http://localhost:3000` in your browser
2. Enter a natural language search query, e.g.: *"Find 50 chiefs of staff, estate managers and luxury concierge contacts in London and Dubai who may manage UHNW travel"*
3. Select target locations and personas using the multi-select buttons
4. Set the number of prospects (default: 20)
5. Click **Start Search**
6. Monitor the Agent Run Status page as each agent processes in sequence
7. View ranked prospects on the Prospects page
8. Access outreach messages and export results as CSV

## Environment Variables (.env)

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | Yes (for outreach) |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `APOLLO_API_KEY` | Apollo.io API key | No (graceful fallback) |
| `HUNTER_API_KEY` | Hunter.io API key | No (graceful fallback) |
| `PDL_API_KEY` | People Data Labs API key | No (graceful fallback) |
| `GOOGLE_CSE_API_KEY` | Google Custom Search API key | No |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID | No |
| `SERPAPI_KEY` | SerpAPI key (fallback for web search) | No |
| `DEBUG` | Enable debug logging | No (default: true) |
| `PORT` | Backend port | No (default: 8000) |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | No (default: http://localhost:8000) |

Each connector returns empty results gracefully if its API key is missing. The pipeline never crashes due to a missing key.

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage

- **Scoring tests** (`tests/test_scoring.py`): Validates all scoring rules including title-based scoring, location matching, email verification bonuses, UHNW relevance, weak signal penalties, and score capping (0-100).
- **Deduplication tests** (`tests/test_deduplication.py`): Validates email-based dedup, LinkedIn URL dedup, name+company dedup with different emails kept, and field-count-based winner selection.

## Agent Pipeline

The pipeline runs 8 agents in sequence. Each agent inherits from `BaseAgent`, logs its run to the `agent_runs` table, and passes output to the next agent.

### Agent 1: Source Finder
Searches the web for relevant companies and online sources matching the target persona, location, and industry. Returns a list of companies with their websites and source URLs.

### Agent 2: Prospect Discovery
Uses the Apollo connector (people search) and web search to find people with relevant titles (PA, EA, Chief of Staff, Estate Manager, Family Office, Founder, CEO, etc.) at each company identified by the Source Finder.

### Agent 3: Data Extraction
Normalises all raw prospect records into the standard schema. Cleans and validates names, emails, URLs, and flags missing critical fields.

### Agent 4: Enrichment
Enriches each prospect using Apollo, People Data Labs, and Hunter.io in sequence. Only overwrites fields if the existing value is null. Logs each enrichment attempt and verifies emails via Hunter.

### Agent 5: Deduplication
Removes duplicate prospects using a priority-based system: exact email match, then LinkedIn URL match, then company+name match. Keeps the record with the most populated fields.

### Agent 6: Scoring
Scores each prospect from 0 to 100 using rule-based criteria: title match (+25 to +40), UHNW relevance (+25), industry match (+20), location match (+20), verified email (+15), weak signals (-20), no role fit (-30). Full breakdown stored as JSONB.

### Agent 7: Outreach
Generates four message variants per prospect using GPT-4o: LinkedIn connection request (under 300 chars), LinkedIn follow-up, email with subject and CTA, and WhatsApp intro. Follows strict tone rules — professional, human, no hype, no exclamation marks.

### Agent 8: Compliance
Creates compliance records for each prospect with data source classification (public/api/manual), confidence level (high/medium/low), and flags for verification issues.

## How to Add a New Connector

1. Create a new file in `backend/connectors/`, e.g., `new_connector.py`
2. Create a class inheriting from `BaseConnector`
3. Implement the `search()` and `enrich()` methods
4. Handle missing API keys gracefully (return empty results, never crash)
5. Import and use the connector in the relevant agent(s)

```python
from backend.connectors.base_connector import BaseConnector

class NewConnector(BaseConnector):
    name = "new_connector"

    async def search(self, **kwargs):
        # Implement search logic
        return []

    async def enrich(self, **kwargs):
        # Implement enrichment logic
        return None
```

## How to Add a New Agent

1. Create a new file in `backend/agents/`, e.g., `new_agent.py`
2. Create a class inheriting from `BaseAgent`
3. Set the `name` class attribute
4. Implement the `execute()` method
5. Add the agent to the pipeline sequence in `backend/orchestrator/pipeline.py`

```python
from backend.agents.base_agent import BaseAgent

class NewAgent(BaseAgent):
    name = "new_agent"

    async def execute(self, input_data):
        # Process input_data and return results
        return input_data
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/searches` | Create a new search and start pipeline |
| GET | `/api/searches/{id}` | Get search status and summary |
| GET | `/api/searches/{id}/runs` | Get all agent run statuses |
| GET | `/api/prospects` | List prospects (filterable) |
| GET | `/api/prospects/{id}` | Get full prospect detail |
| GET | `/api/outreach/{prospect_id}` | Get outreach messages |
| GET | `/api/export/{search_id}` | Download CSV export |
| POST | `/api/manual` | Submit manual company research |
| GET | `/api/health` | Health check |

## Project Structure

```
skybridge-jets/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── source_finder_agent.py
│   │   ├── prospect_discovery_agent.py
│   │   ├── data_extraction_agent.py
│   │   ├── enrichment_agent.py
│   │   ├── deduplication_agent.py
│   │   ├── scoring_agent.py
│   │   ├── outreach_agent.py
│   │   └── compliance_agent.py
│   ├── connectors/
│   │   ├── base_connector.py
│   │   ├── apollo_connector.py
│   │   ├── hunter_connector.py
│   │   ├── pdl_connector.py
│   │   ├── web_search_connector.py
│   │   └── manual_connector.py
│   ├── orchestrator/
│   │   └── pipeline.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   ├── api/
│   │   └── main.py
│   ├── tests/
│   │   ├── test_scoring.py
│   │   └── test_deduplication.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx              (New Search)
│   │   ├── runs/[id]/page.tsx    (Agent Run Status)
│   │   ├── prospects/page.tsx    (Ranked Prospects)
│   │   ├── prospects/[id]/page.tsx (Prospect Detail)
│   │   ├── outreach/page.tsx     (Outreach Messages)
│   │   └── export/page.tsx       (Export Results)
│   ├── components/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── .env.example
└── README.md
```

## Technology Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy (async)
- **Database**: PostgreSQL (Supabase-compatible)
- **Agent Framework**: Custom Python classes (no CrewAI, no LangChain)
- **LLM**: OpenAI GPT-4o via API
- **Data Connectors**: Apollo.io, Hunter.io, People Data Labs, Google Custom Search, SerpAPI

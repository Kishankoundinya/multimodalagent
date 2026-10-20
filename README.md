# Multi-Agent AI Analysis System for Financial Research and Business Insights

An institutional-grade, multi-agent financial research platform designed specifically for finance students, MBA candidates, equity research analysts, and researchers. The system ingests primary corporate disclosure filings (such as SEC 10-K and 10-Q reports or integrated annual reports in PDF format), performs page-level text extraction and chunk indexing into **ChromaDB**, and orchestrates a team of six specialized agents via **LangGraph**.

Every financial figure, ratio, and risk factor is **strictly grounded in primary disclosures with exact page-level citations** (`[Source: <Document>, p. <Page>]`). The system operates with **Google Gemini (Free Tier)**, eliminating heavy local LLM dependencies, PyTorch model downloads, and laptop RAM bottlenecks while delivering fast, accurate, and source-grounded answers.

> 📖 **Comprehensive Questions & Answers**: For an exhaustive technical reference, tool comparisons, architectural justifications, and interview/viva questions, see [**questions_and_answers.txt**](./questions_and_answers.txt).

---

## Key Highlights & Architectural Principles

1. **Strict Source Grounding & Zero Fabrication**:
   - The AI **never invents** financial numbers, dates, ratios, or sources.
   - If information is not explicitly stated in indexed filings, the system strictly responds:  
     `"Information not found in the provided documents."`
   - Every claim is validated against retrieved source chunks using a dedicated citation verification layer (`validate_citations`).
2. **Optimized Hardware Footprint**:
   - **Google Gemini API (Free Tier)**: Fast cloud inference with models like `gemini-1.5-flash` or `gemini-2.0-flash`. No local model weights to download, zero GPU VRAM consumption, and near-zero CPU overhead.
   - **No Heavy Infrastructure**: Operates with SQLite and local persistent ChromaDB. No Redis, no Celery, no PostgreSQL, no Docker or Kubernetes overhead.
   - Low memory footprint: Sentence Transformers handle fast local embeddings while Gemini executes reasoning and synthesis.
3. **LangChain & ChromaDB Vector Store**:
   - Chunks are extracted page-by-page with PyMuPDF (`fitz`), partitioned using LangChain's `RecursiveCharacterTextSplitter`, embedded using `sentence-transformers/all-MiniLM-L6-v2`, and indexed locally in ChromaDB.
4. **LangGraph 6-Agent Architecture**:
   - Exactly six specialized logical agents execute discrete analysis tasks conditionally. If you ask for a metric, the system executes only the retrieval and extraction agent, avoiding full pipeline overhead and saving CPU time.
5. **Analyst-Grade PDF Report Generation**:
   - Compiles a complete 10-section PDF equity research report using **ReportLab** with cover page, metrics tables, ratio derivations, red flag summaries, and source citations.

---

## Multi-Agent Architecture

```
                    ┌─────────────────────────┐
                    │     User / Web UI       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      FastAPI Backend    │
                    └────────────┬────────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │    LangGraph Router       │
                   └───────┬─────┬─────┬───────┘
                           │     │     │
         ┌─────────────────┘     │     └────────────────┐
         ▼                       ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 1. Document Agent│   │ 5. Research Agent│   │ 4. Compare Agent │
│ (PyMuPDF, Chroma)│   │ (Decompose, RAG) │   │ (Side-by-side)   │
└──────────────────┘   └─────────┬────────┘   └──────────────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ 2. Extract Agent  │
                       │ (16 Core Metrics) │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ 3. Red Flag Agent │
                       │ (Disclosed Risks) │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ 6. Report Agent   │
                       │ (ReportLab PDF)   │
                       └───────────────────┘
```

### The Six Logical Agents:
1. **Document Agent**: Validates uploaded PDFs, extracts text page-by-page with PyMuPDF, chunks text while strictly preserving page numbers, generates SentenceTransformer embeddings, stores chunks in ChromaDB, and updates document processing stages in SQLite (`Uploading` → `Extracting` → `Chunking` → `Embedding` → `Indexing` → `Completed`).
2. **Extraction Agent**: Extracts 16 key financial metrics (Revenue, Net Income, Operating Income, EBITDA, Total Assets, Total Liabilities, Total Debt, Cash, Equity, EPS, Operating Margin, Net Profit Margin, ROE, ROA, Current Ratio, Debt-to-Equity). Computes verifiable ratios only when source figures exist, explicitly labeling them `"Calculated from source values"`.
3. **Red Flag Agent**: Scans filings for material warning signs including auditor qualifications, going concern disclosures, debt covenant risks, negative operating cash flows, and falling margins, each tagged with evidence and severity (`LOW`, `MEDIUM`, `HIGH`).
4. **Comparison Agent**: Compares two entities side-by-side on common financial metrics, detailing objective numerical differences with source pages, without subjective rankings.
5. **Research Agent**: Handles complex conversational inquiries. Decomposes multi-part queries into subqueries (up to `MAX_RETRIEVAL_STEPS=3`), retrieves relevant chunks, analyzes them with Google Gemini (Free Tier), and verifies citations.
6. **Report Agent**: Gathers verified metrics, ratios, red flags, and executive summary narrative to build a downloadable 10-section PDF report via ReportLab.

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2
- **Agent Orchestration**: LangGraph
- **RAG & NLP**: LangChain, Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Vector Database**: ChromaDB (`chromadb` & `langchain-chroma`)
- **Relational Storage**: SQLite
- **PDF Engine**: PyMuPDF (`fitz`) for extraction; ReportLab for analyst PDF generation
- **LLM Engine**: Google Gemini Free Tier (`gemini-1.5-flash` / `gemini-2.0-flash` via `google-generativeai` and direct REST)
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons

---

## Directory Structure

```
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file
├── README.md                     # Documentation
├── requirements.txt              # Backend Python dependencies
├── run.sh                        # Unified application launcher
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point & CORS
│   │   ├── api/                  # REST API route handlers
│   │   │   ├── documents.py      # PDF upload, processing, seed detection
│   │   │   ├── research.py       # Conversational research queries
│   │   │   ├── metrics.py        # Financial metrics & red flags
│   │   │   ├── comparison.py     # Multi-company comparison
│   │   │   ├── reports.py        # PDF report generation & download
│   │   │   └── settings.py       # Runtime settings
│   │   ├── agents/               # 6 LangGraph agent nodes
│   │   │   ├── document_agent.py
│   │   │   ├── extraction_agent.py
│   │   │   ├── red_flag_agent.py
│   │   │   ├── comparison_agent.py
│   │   │   ├── research_agent.py
│   │   │   └── report_agent.py
│   │   ├── graph/                # LangGraph workflow definition
│   │   │   ├── state.py          # AnalysisState TypedDict
│   │   │   └── workflow.py       # Conditional graph builder
│   │   ├── llm/                  # Google Gemini API provider
│   │   │   ├── llm_provider.py   # SharedLLM singleton (Google Gemini Free Tier)
│   │   │   └── prompts.py        # Agent-specific prompt templates
│   │   ├── rag/                  # RAG components
│   │   │   ├── chunking.py       # LangChain text splitter with page metadata
│   │   │   ├── embeddings.py     # SentenceTransformer embeddings singleton
│   │   │   ├── retriever.py      # Filtered retrieval & context formatting
│   │   │   └── vector_store.py   # ChromaDB persistent store integration
│   │   ├── database/             # SQLite database layer
│   │   │   └── database.py       # Schema & DAO helper methods
│   │   ├── models/               # Pydantic schemas
│   │   │   └── schemas.py
│   │   ├── services/             # Core business services
│   │   │   ├── document_service.py # PyMuPDF extraction & seed scanner
│   │   │   ├── citation_service.py # Citation parsing & grounding validator
│   │   │   └── report_service.py   # ReportLab 10-section PDF generator
│   │   └── utils/
│   │       ├── config.py         # Pydantic BaseSettings
│   │       └── logging.py        # Structured logger
│   └── tests/                    # Pytest test suite
│       ├── test_rag.py
│       ├── test_metrics_ratios.py
│       ├── test_api.py
│       └── create_sample_pdf.py  # Sample PDF generator for seed testing
├── data/
│   ├── documents/                # Uploaded PDFs storage
│   ├── chromadb/                 # Persistent ChromaDB collections
│   ├── reports/                  # Generated ReportLab PDF reports
│   └── seed/                     # Local seed PDFs directory
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── components/
        │   ├── Navbar.jsx
        │   └── Sidebar.jsx
        ├── pages/
        │   ├── DashboardPage.jsx
        │   ├── DocumentsPage.jsx
        │   ├── ResearchPage.jsx
        │   ├── MetricsPage.jsx
        │   ├── RedFlagsPage.jsx
        │   ├── ComparePage.jsx
        │   ├── ReportsPage.jsx
        │   ├── HistoryPage.jsx
        │   └── SettingsPage.jsx
        └── services/
            └── api.js
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 to 3.12 recommended
- Node.js (v18+) and npm
- macOS / Linux / Windows

### 1. Clone & Setup Environment
```bash
# In the project root:
cp .env.example .env
```

### 2. Backend Dependencies
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option A: One-Command Startup (Recommended)
```bash
./run.sh
```
This script verifies Python and npm, initializes the environment, ensures directories exist, auto-generates a sample seed filing if empty, and starts both the FastAPI backend (`http://127.0.0.1:8000`) and the Vite React frontend (`http://localhost:5173`).

### Option B: Running Services Separately
**Backend:**
```bash
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload --port 8000
```
API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

**Frontend:**
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Configuration (`.env`)

| Variable | Default Value | Description |
|---|---|---|
| `LLM_MODEL` | `gemini-1.5-flash` | Google Gemini model identifier (`gemini-1.5-flash`, `gemini-2.0-flash`) |
| `GEMINI_API_KEY` | `""` | Free API key from Google AI Studio (`aistudio.google.com`) |
| `DEVICE` | `auto` | `auto` (detects Apple Silicon MPS, CUDA, or CPU for embeddings) |
| `TEMPERATURE` | `0.2` | Low temperature for deterministic, factual responses |
| `MAX_NEW_TOKENS` | `1024` | Token limit for research responses |
| `MAX_REPORT_TOKENS` | `2048` | Token limit for executive summaries in reports |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Lightweight 384-dim embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size in characters |
| `CHUNK_OVERLAP` | `150` | Overlap between adjacent chunks |
| `TOP_K` | `5` | Number of chunks retrieved per query |
| `MAX_RETRIEVAL_STEPS`| `3` | Maximum subqueries decomposed by Research Agent |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload PDF file size |
| `CHROMA_PERSIST_DIR` | `./data/chromadb` | Local persistent directory for ChromaDB |
| `SQLITE_DB_PATH` | `./data/financial_research.db` | Local SQLite database file |

---

## How It Works: Step-by-Step

### 1. Document Upload & ChromaDB Storage
1. When a user uploads a PDF or indexes a seed document from `data/seed/`:
2. **PyMuPDF (`fitz`)** parses the document page-by-page, recording exact 1-indexed page numbers.
3. If the PDF has no text (e.g. image-only scan), the system returns: `"This PDF does not contain extractable text. OCR support can be added later."`
4. The text splitter chunks the pages into ~1000-character chunks with 150-character overlap.
5. Every chunk retains metadata:
   ```json
   {
     "document_id": "...",
     "document_name": "apple_annual_report_2024.pdf",
     "company": "Apple",
     "year": "2024",
     "page": 42,
     "chunk_id": "doc_id_p42_c1"
   }
   ```
6. Chunks and embeddings are stored directly in **ChromaDB** (`data/chromadb/`), and metadata is tracked in **SQLite**.

### 2. Research & Question Answering
1. User enters a query (e.g. `"What was total revenue, net income, and debt?"`).
2. The Research Agent decomposes composite questions into focused subqueries (up to 3).
3. Chunks are retrieved from ChromaDB using semantic similarity.
4. Chunks are formatted with explicit headers:
   `Source: Apple 2024.pdf, Page: 42, Company: Apple`
5. The Google Gemini model generates an answer following the strict prompt template.
6. The `validate_citations()` service scans the generated text:
   - Verifies that every `[Source: ..., p. X]` citation actually exists in the retrieved chunks.
   - Any hallucinated page numbers are stripped or flagged as `[Source unverified]`.
   - If the answer has insufficient evidence, it responds: `"Information not found in the provided documents."`

### 3. Financial Metrics & Ratio Calculation
- **Primary Metrics**: Revenue, Net Income, Operating Income, Total Assets, Total Liabilities, Total Debt, Cash, Equity, EPS, etc.
- **Ratios Calculated Strictly from Disclosed Values**:
  - `Net Profit Margin = (Net Income / Revenue) * 100`
  - `Debt-to-Equity = Total Debt / Shareholders' Equity`
  - `ROA = (Net Income / Total Assets) * 100`
  - `ROE = (Net Income / Shareholders' Equity) * 100`
- Ratios are explicitly labeled: `"Calculated from source values"` along with the exact source pages.

### 4. PDF Report Generation
The user clicks **Generate Report** on any indexed filing. The Report Agent synthesizes the executive summary and formats a 10-section report via ReportLab:
1. Cover Page
2. Executive Summary
3. Company & Filing Information
4. Key Financial Metrics Table
5. Financial Performance & Calculated Ratios Table
6. Financial Trends & Operating Trajectory
7. Documented Red Flags Table (Severity, Indicator, Evidence, Page)
8. Company / Peer Comparison
9. Key Research Findings
10. Verified Disclosed Sources

---

## API Endpoints Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | System health check (DB, ChromaDB, model device) |
| `POST` | `/api/documents/upload` | Upload and optionally index a new PDF |
| `GET` | `/api/documents` | List all tracked documents and their statuses |
| `GET` | `/api/documents/{id}` | Get status and metadata for a document |
| `POST` | `/api/documents/{id}/process`| Manually trigger or retry document processing |
| `DELETE`| `/api/documents/{id}` | Delete document and wipe its ChromaDB vectors |
| `GET` | `/api/documents/seed/list` | List detected PDFs in `data/seed/` |
| `POST` | `/api/documents/seed/index` | Index a seed filing |
| `POST` | `/api/research` | Submit a research question to Research Agent |
| `GET` | `/api/research/history` | Retrieve full research Q&A history |
| `GET` | `/api/metrics/{document_id}` | Get extracted financial metrics and ratios |
| `POST` | `/api/metrics/{document_id}/extract` | Force re-extraction of metrics |
| `GET` | `/api/metrics/red-flags` | List all identified red flags |
| `POST` | `/api/compare` | Compare two companies on common metrics |
| `POST` | `/api/reports/generate` | Generate a 10-section ReportLab PDF report |
| `GET` | `/api/reports` | List all generated PDF reports |
| `GET` | `/api/reports/{id}` | Get details of a generated report |
| `GET` | `/api/reports/{id}/download` | Download generated PDF report file |
| `GET` | `/api/settings` | Get current runtime settings |
| `POST` | `/api/settings` | Update runtime settings |

---

## Testing

Run the automated test suite with pytest:
```bash
source .venv/bin/activate
python -m pytest backend/tests -v
```

Tests cover:
- Text extraction and chunking
- Page-level metadata preservation
- ChromaDB vector store indexing and retrieval
- Citation validation and hallucination rejection
- Financial metrics extraction and deterministic ratio formulas
- FastAPI health, settings, and documents endpoints

---

## License & Compliance
This software is intended for educational, research, and analysis purposes. Always use legally obtained primary filings. The software operates 100% locally and transmits no corporate documents or financial disclosures to third-party cloud services.

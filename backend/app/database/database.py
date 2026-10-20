import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.SQLITE_DB_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise e
    finally:
        conn.close()

def init_db():
    settings.ensure_directories()
    with get_db() as conn:
        cursor = conn.cursor()

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                company TEXT NOT NULL,
                fiscal_year TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                num_pages INTEGER DEFAULT 0,
                num_chunks INTEGER DEFAULT 0,
                processing_status TEXT DEFAULT 'Uploading',
                chroma_collection TEXT,
                error_message TEXT,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0
            )
        """)

        # Financial Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                company TEXT NOT NULL,
                fiscal_year TEXT NOT NULL,
                metric TEXT NOT NULL,
                value TEXT,
                unit TEXT,
                period TEXT,
                source_document TEXT,
                page INTEGER,
                source_text TEXT,
                is_calculated INTEGER DEFAULT 0,
                calculation_formula TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)

        # Red Flags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS red_flags (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                company TEXT NOT NULL,
                fiscal_year TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence TEXT NOT NULL,
                severity TEXT NOT NULL,
                source_document TEXT,
                page INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)

        # Research History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_history (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                company TEXT,
                created_at TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources_json TEXT NOT NULL
            )
        """)

        # Reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                fiscal_year TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sections_json TEXT
            )
        """)

        conn.commit()
        logger.info(f"Database initialized successfully at {settings.SQLITE_DB_PATH}")

# Database Helper Functions

def insert_document(doc_data: Dict[str, Any]):
    with get_db() as conn:
        conn.cursor().execute("""
            INSERT INTO documents (
                id, filename, company, fiscal_year, upload_date,
                num_pages, num_chunks, processing_status, chroma_collection,
                error_message, file_path, file_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_data["id"],
            doc_data["filename"],
            doc_data["company"],
            doc_data["fiscal_year"],
            doc_data.get("upload_date", datetime.now(timezone.utc).isoformat()),
            doc_data.get("num_pages", 0),
            doc_data.get("num_chunks", 0),
            doc_data.get("processing_status", "Uploading"),
            doc_data.get("chroma_collection", "financial_docs"),
            doc_data.get("error_message"),
            doc_data["file_path"],
            doc_data.get("file_size", 0),
        ))

def update_document_status(
    doc_id: str,
    status: str,
    num_pages: Optional[int] = None,
    num_chunks: Optional[int] = None,
    error_message: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "UPDATE documents SET processing_status = ?"
        params = [status]
        if num_pages is not None:
            query += ", num_pages = ?"
            params.append(num_pages)
        if num_chunks is not None:
            query += ", num_chunks = ?"
            params.append(num_chunks)
        if error_message is not None:
            query += ", error_message = ?"
            params.append(error_message)
        query += " WHERE id = ?"
        params.append(doc_id)
        cursor.execute(query, params)

def get_all_documents() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM documents ORDER BY upload_date DESC").fetchall()
        return [dict(r) for r in rows]

def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.cursor().execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

def get_documents_by_company(company: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM documents WHERE company = ? ORDER BY fiscal_year DESC", (company,)).fetchall()
        return [dict(r) for r in rows]

def delete_document(doc_id: str):
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM financial_metrics WHERE document_id = ?", (doc_id,))
        conn.cursor().execute("DELETE FROM red_flags WHERE document_id = ?", (doc_id,))
        conn.cursor().execute("DELETE FROM documents WHERE id = ?", (doc_id,))

def insert_metrics(metrics: List[Dict[str, Any]]):
    with get_db() as conn:
        cursor = conn.cursor()
        for m in metrics:
            cursor.execute("""
                INSERT OR REPLACE INTO financial_metrics (
                    id, document_id, company, fiscal_year, metric, value,
                    unit, period, source_document, page, source_text,
                    is_calculated, calculation_formula
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["id"],
                m["document_id"],
                m["company"],
                m.get("fiscal_year") or m.get("period") or "FY",
                m["metric"],
                str(m["value"]) if m.get("value") is not None else None,
                m.get("unit"),
                m.get("period"),
                m.get("source_document"),
                m.get("page"),
                m.get("source_text"),
                1 if m.get("is_calculated") else 0,
                m.get("calculation_formula"),
            ))

def get_metrics_for_document(doc_id: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM financial_metrics WHERE document_id = ?", (doc_id,)).fetchall()
        return [dict(r) for r in rows]

def get_metrics_by_company_year(company: str, year: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        if year:
            rows = conn.cursor().execute(
                "SELECT * FROM financial_metrics WHERE company = ? AND fiscal_year = ?",
                (company, year)
            ).fetchall()
        else:
            rows = conn.cursor().execute(
                "SELECT * FROM financial_metrics WHERE company = ?",
                (company,)
            ).fetchall()
        return [dict(r) for r in rows]

def insert_red_flags(red_flags: List[Dict[str, Any]]):
    with get_db() as conn:
        cursor = conn.cursor()
        for rf in red_flags:
            cursor.execute("""
                INSERT OR REPLACE INTO red_flags (
                    id, document_id, company, fiscal_year, title,
                    description, evidence, severity, source_document, page
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rf["id"],
                rf["document_id"],
                rf["company"],
                rf["fiscal_year"],
                rf["title"],
                rf["description"],
                rf["evidence"],
                rf["severity"],
                rf.get("source_document"),
                rf.get("page"),
            ))

def get_red_flags_for_document(doc_id: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM red_flags WHERE document_id = ?", (doc_id,)).fetchall()
        return [dict(r) for r in rows]

def get_all_red_flags() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM red_flags ORDER BY severity DESC").fetchall()
        return [dict(r) for r in rows]

def insert_research_history(item: Dict[str, Any]):
    with get_db() as conn:
        conn.cursor().execute("""
            INSERT INTO research_history (
                id, question, company, created_at, answer, sources_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item["id"],
            item["question"],
            item.get("company"),
            item.get("created_at", datetime.now(timezone.utc).isoformat()),
            item["answer"],
            json.dumps(item.get("sources", [])) if isinstance(item.get("sources"), list) else item.get("sources_json", "[]"),
        ))

def get_research_history() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM research_history ORDER BY created_at DESC").fetchall()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["sources"] = json.loads(d["sources_json"])
            except Exception:
                d["sources"] = []
            results.append(d)
        return results

def insert_report(report_data: Dict[str, Any]):
    with get_db() as conn:
        conn.cursor().execute("""
            INSERT INTO reports (
                id, title, company, fiscal_year, file_path, created_at, sections_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            report_data["id"],
            report_data["title"],
            report_data["company"],
            report_data["fiscal_year"],
            report_data["file_path"],
            report_data.get("created_at", datetime.now(timezone.utc).isoformat()),
            json.dumps(report_data.get("sections", {})),
        ))

def get_all_reports() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["sections"] = json.loads(d.get("sections_json") or "{}")
            except Exception:
                d["sections"] = {}
            results.append(d)
        return results

def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.cursor().execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["sections"] = json.loads(d.get("sections_json") or "{}")
        except Exception:
            d["sections"] = {}
        return d

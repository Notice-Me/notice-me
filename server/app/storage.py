import json
import sqlite3
from pathlib import Path

from .models import Content, Verification, utcnow
from .providers.base import stable_id


class Store:
    """Only content metadata is persisted; no user locations, routes or questions."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS contents (
                    id TEXT PRIMARY KEY, data_mode TEXT NOT NULL, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY, collected_at TEXT NOT NULL,
                    provider TEXT NOT NULL, status TEXT NOT NULL, item_count INTEGER NOT NULL,
                    code TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS news_searches (
                    id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL,
                    provider TEXT NOT NULL, keyword TEXT NOT NULL,
                    window_hours INTEGER NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS event_pages (
                    id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL,
                    provider TEXT NOT NULL, payload TEXT NOT NULL
                );
            """)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def upsert(self, items: list[Content]):
        with self.connect() as conn:
            conn.executemany(
                "INSERT INTO contents VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                "data_mode=excluded.data_mode, payload=excluded.payload",
                [(x.id, x.data_mode.value, x.model_dump_json()) for x in items],
            )

    def all(self, mode: str) -> list[Content]:
        with self.connect() as conn:
            if mode == "mixed":
                rows = conn.execute("SELECT payload FROM contents ORDER BY id").fetchall()
            else:
                rows = conn.execute(
                    "SELECT payload FROM contents WHERE data_mode=? ORDER BY id", (mode.upper(),)
                ).fetchall()
        return [Content.model_validate_json(row[0]) for row in rows]

    def get(self, content_id: str, mode: str) -> Content | None:
        with self.connect() as conn:
            row = conn.execute("SELECT payload, data_mode FROM contents WHERE id=?", (content_id,)).fetchone()
        if row is None or (mode != "mixed" and row[1] != mode.upper()):
            return None
        return Content.model_validate_json(row[0])

    def record(self, provider: str, status: str, item_count: int, code: str):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO collections(collected_at,provider,status,item_count,code) VALUES (?,?,?,?,?)",
                (utcnow().isoformat(), provider, status, item_count, code),
            )

    def health(self):
        with self.connect() as conn:
            conn.execute("SELECT 1").fetchone()
            rows = conn.execute("SELECT data_mode, count(*) FROM contents GROUP BY data_mode").fetchall()
        return {mode: count for mode, count in rows}

    def recent_collections(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT collected_at,provider,status,item_count,code FROM collections "
                "ORDER BY id DESC LIMIT 10"
            ).fetchall()
        return [dict(zip(("collected_at", "provider", "status", "item_count", "code"), r)) for r in rows]

    def record_news_search(self, provider: str, case: dict, articles: list[dict]):
        """Append each result immediately; failures never replace earlier successful observations."""
        payload = {**case, "article_metadata": articles}
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO news_searches(observed_at,provider,keyword,window_hours,status,payload) "
                "VALUES (?,?,?,?,?,?)",
                (
                    utcnow().isoformat(),
                    provider,
                    case["keyword"],
                    case["window_hours"],
                    case["status"],
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    def news_searches(self, provider: str):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM news_searches WHERE provider=? ORDER BY id", (provider,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save_event_page(self, provider: str, items: list[Content], page: dict):
        """Retain page decisions and quarantine newly invalid records without deleting history."""
        with self.connect() as conn:
            conn.executemany(
                "INSERT INTO contents VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                "data_mode=excluded.data_mode, payload=excluded.payload",
                [(x.id, x.data_mode.value, x.model_dump_json()) for x in items],
            )
            for observation in page["rows"]:
                if not observation.get("invalidate_previous") or not observation.get("contentid"):
                    continue
                identifier = stable_id("tour-event", observation["contentid"])
                row = conn.execute("SELECT payload FROM contents WHERE id=?", (identifier,)).fetchone()
                if row:
                    item = Content.model_validate_json(row[0]).model_copy(
                        update={"verification_status": Verification.UNVERIFIED}
                    )
                    conn.execute(
                        "UPDATE contents SET payload=? WHERE id=?", (item.model_dump_json(), identifier)
                    )
            conn.execute(
                "INSERT INTO event_pages(observed_at,provider,payload) VALUES (?,?,?)",
                (page["observed_at"], provider, json.dumps(page, ensure_ascii=False)),
            )

    def event_pages(self, provider: str):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM event_pages WHERE provider=? ORDER BY id", (provider,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

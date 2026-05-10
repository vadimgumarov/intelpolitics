"""Standalone helper: render the daily review queue Markdown from current DB state.

Reads the top-confidence-N rows from `pg.statements` and writes them to
review-queues/<filename>.md per kickoff §5.3 format.

Usage:
    POSTGRES_URL=... python scripts/write_review_queue.py [out_path] [limit]
"""
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.db import postgres as pg
from src.pipelines.d1_run import _write_review_queue


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else (
        REPO_ROOT / "review-queues" / f"d1-review-{date.today().isoformat()}.md"
    )
    limit = int(argv[2]) if len(argv) > 2 else 5
    with pg.get_conn() as conn:
        rows = pg.fetch_review_queue(conn, limit=limit)
    _write_review_queue(out, rows)
    print(f"Wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

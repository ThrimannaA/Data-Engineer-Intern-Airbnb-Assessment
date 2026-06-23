# Decision Log

## Database Selection

**Chosen:** SQLite

**Options Considered:**

- DuckDB (analytical, fast)
- SQLite (simple, reliable)
- PostgreSQL (production-grade)

**Rationale:**

- No server setup required
- Built into Python standard library
- Works reliably on Windows
- Sufficient for all required queries

**Trade-offs:**

- Less analytical functions than DuckDB (e.g., PERCENTILE_CONT)
- Slower for very large datasets
- But acceptable for 100K+ row datasets

**Implementation:**
conn = sqlite3.connect('data/processed/nyc/nyc.db')

df = pd.read_sql_query(query, conn)

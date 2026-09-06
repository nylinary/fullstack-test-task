# Backend

FastAPI + Celery service for uploading files, scanning them for suspicious
content and emitting alerts. Refactored onto a clean-architecture layout.

## Architecture

The single rule: **dependencies point inwards.** An inner layer never imports an
outer one, so the business rules can be read, tested and changed without a
database, a broker or a web framework in the picture.

```
             ┌───────────────────────────────────────────────┐
             │  presentation/http   routers, schemas,        │  FastAPI
             │                      error handlers           │
             ├───────────────────────────────────────────────┤
             │  infrastructure      SQLAlchemy, Celery,       │  adapters
             │                      local storage, settings   │
             ├───────────────────────────────────────────────┤
             │  application         use cases, DTOs, ports    │  orchestration
             ├───────────────────────────────────────────────┤
             │  domain              entities, value objects,  │  pure Python
             │                      services, ports           │
             └───────────────────────────────────────────────┘
                        ▲  imports only ever point up this diagram
```

`src/container.py` is the composition root - the one module allowed to see every
layer at once. It wires concrete adapters into use cases; everything else talks
to protocols.

The rule is not just documented, it is asserted:
[`tests/unit/test_architecture.py`](tests/unit/test_architecture.py) walks the AST
of every module and fails the build if `domain/` imports SQLAlchemy, if
`application/` imports FastAPI, and so on.

### Layout

| Path | Contains | May import |
| --- | --- | --- |
| `src/domain/` | `StoredFile`, `Alert`, statuses, `ThreatScanner`, `MetadataExtractor`, `AlertPolicy`, and the `FileRepository` / `UnitOfWork` / `FileStorage` ports | stdlib only |
| `src/application/` | one class per use case (`UploadFileUseCase`, `ProcessFileUseCase`, …), DTOs, the `FileProcessingQueue` port | `domain` |
| `src/infrastructure/` | SQLAlchemy tables + repositories + unit of work, `LocalFileStorage`, Celery app and tasks, typed settings | `domain`, `application` |
| `src/presentation/http/` | routers, Pydantic schemas, dependency providers, domain-error → HTTP mapping | all of the above |

### Notable decisions

**Entities are persisted with SQLAlchemy's imperative mapping.** `StoredFile` and
`Alert` are plain dataclasses with zero framework imports, mapped onto their
tables in `infrastructure/db/tables.py`. That gives a genuinely pure domain
*without* the usual price of a second set of ORM models plus a hand-written
mapper, and Alembic still autogenerates from the same metadata.

**State transitions live on the entity.** `start_processing()`, `apply_scan()`,
`apply_metadata()`, `mark_failed()`, `rename()`. Previously these were loose
attribute assignments spread across three Celery tasks, so a rule like "a file
that already has a scan verdict keeps it when processing fails" was implicit in
the order of two lines of code.

**No `HTTPException` outside the HTTP layer.** The old `service.py` raised
`HTTPException` from the persistence functions, which the Celery worker also
imported - a 404 raised inside a background job means nothing. Use cases now
raise domain errors and `presentation/http/error_handlers.py` maps them to status
codes in one place.

**Statuses are `StrEnum`s.** The literals `"processing"`, `"suspicious"`,
`"critical"` were repeated as bare strings across four modules. The values stored
in Postgres are unchanged.

## Bugs fixed

| # | Problem | Fix |
| --- | --- | --- |
| 1 | Deleting a file that had produced an alert failed: `alerts.file_id` had no `ON DELETE` action, so the FK blocked the `DELETE` | `ON DELETE CASCADE` (migration `a1c4f2b7e903`) |
| 2 | `delete_file` unlinked the blob *before* committing - a failed commit destroyed the content of a file that was still listed | row is deleted and committed first, blob after |
| 3 | `create_file` wrote the blob before inserting the row - a failed insert left an orphan file on disk forever | the blob is removed if the insert fails |
| 4 | Blocking I/O on the event loop: `Path.write_bytes`, `Path.exists`, and Celery's `.delay()` (a synchronous broker socket call) inside `async def` endpoints | all file I/O goes through `anyio`; `send_task` runs on a worker thread |
| 5 | `greenlet` was never declared, and SQLAlchemy's async layer refuses to run without it | dependency is `sqlalchemy[asyncio]` |
| 6 | The DSN was built from `os.environ.get(...)`, so a missing variable silently produced `postgresql+asyncpg://None:None@None:None/None` | typed `Settings` (pydantic-settings) |
| 7 | Uploads were unbounded - one large request could exhaust RAM and disk | streamed with a `max_upload_size` cap, aborted mid-stream (HTTP 413) |
| 8 | The filename from the multipart body was used unsanitised for the stored name and for `Content-Disposition` | `sanitize_filename` strips directories, CR/LF and quotes; storage refuses any path that resolves outside its root |
| 9 | `GET /files` and `GET /alerts` returned every row, forever | `limit`/`offset` with a validated cap |
| 10 | Postgres data lived in an unmounted directory (`/var/lib/postgresql` vs. `PGDATA`), so the volume held nothing | `PGDATA` points inside the mount |
| 11 | Neither the API nor the worker waited for Redis; the worker did not even declare it | healthchecks + `depends_on: service_healthy` |
| 12 | The worker read blobs from its own container-local directory - it could only ever see the API's files by accident of the bind mount | an explicit shared `backend-storage` volume |
| 13 | `alembic.ini` and `migrations/` were not in the image, so `alembic upgrade head` only worked because of a dev bind mount | both are copied into the image |
| 14 | A blank or whitespace-only title was accepted | validated in the entity, before anything is written |

## Optimisations

**1. Constant-memory file handling (the non-obvious one).** The old code read
whole files into RAM three times over: `await upload_file.read()` on upload, then
`read_text()` or `read_bytes()` in the metadata task purely to count lines,
characters or PDF page markers. Peak memory scaled with file size, in a service
whose own scanner flags anything over 10 MB as unusual.

Both directions are now streamed in 1 MB chunks. The counting had to survive
being cut into arbitrary pieces, so `TextContentAnalyzer` decodes UTF-8
incrementally and reproduces `str.splitlines()` semantics exactly - including a
`\r\n` pair split across a chunk boundary and the ten characters Python treats as
line breaks - while `PdfContentAnalyzer` keeps a 10-byte overlap so a marker
straddling two chunks is still counted once. `tests/unit/test_metadata.py`
asserts the streaming result equals the whole-file result on hand-picked and on
200 randomised inputs.

The scanner needs no bytes at all, so scanning never opens the file.

**2. Three Celery tasks collapsed into one.** `scan → extract_metadata →
send_alert` chained through the broker, each task opening its own session and
re-loading the same row: 3 broker round-trips, 3 connection checkouts, 3 SELECTs
per upload. They are still three explicit business steps (`ProcessFileUseCase`
calls them in order, with the same commit boundaries, so the intermediate
`processing` state stays observable) but they run in one invocation on one
session: 1 round-trip, 1 checkout, 1 SELECT.

**3. Indexes for the queries that actually run.** Both list endpoints sort by
`created_at DESC` and neither column was indexed; `alerts.file_id` had no index
either, because Postgres does not create one for a foreign key, so every file
deletion scanned the whole alerts table. Measured on 50 000 rows:

```
with ix_files_created_at_id:   Index Scan Backward ... (actual rows=100)   0.140 ms
without it:                    Seq Scan on files   ... (actual rows=50001) + top-N sort
```

**4. One event loop per worker process.** The old `run_in_worker_loop` created
and re-created a module-level loop by hand. An `asyncio.Runner` is now held for
the process lifetime, so the asyncpg pool is established once instead of being
rebuilt per task, and it is disposed on `worker_process_shutdown`.

**5. `eager_defaults=True` on the mappers.** Server-generated `created_at` /
`updated_at` come back through `RETURNING` as part of the INSERT/UPDATE, instead
of the extra `SELECT` the original `session.refresh()` issued after every write.

**6. Zero-copy downloads.** When the storage adapter is backed by a local disk it
exposes the path and the response is served with `sendfile`; a remote adapter
returns `None` and the same endpoint falls back to streaming. Downloads no longer
pull the file through Python either way.

## Running

```bash
docker compose -f docker-compose.dev.yml up
docker exec -it backend alembic upgrade head
```

API docs: <http://localhost:8000/docs> · health: <http://localhost:8000/health>

## Development

```bash
uv sync                       # install (uv manages the venv and the lockfile)
uv run ruff check .           # lint
uv run ruff format .          # format
uv run ty check src tests     # type check
uv run pytest                 # tests
```

The test suite needs no Postgres and no Redis: the ports are filled with SQLite,
a temporary directory and in-memory doubles, which is the practical payoff of the
layering. `tests/unit` covers the domain and the use cases, `tests/integration`
drives the real adapters and the real FastAPI app.

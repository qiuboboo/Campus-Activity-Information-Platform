# Deployment Record

This document records repository synchronization and server deployment progress.

## 2026-05-06

### Repository Pull

- Local repository path: `C:\Users\HP\Desktop\软件工程\Campus-Activity-Information-Platform`
- Remote repository: `https://github.com/qiuboboo/Campus-Activity-Information-Platform.git`
- Pull mode: `git pull --ff-only`
- Result: success
- Updated from `34cb269` to `31b06e7`
- Pulled commit: `31b06e7 Complete server deployment and update TODO list`
- Changed files:
  - `backend/Dockerfile`
  - `backend/app/services/bootstrap.py`
  - `docs/TODOList.md`

### Server Deployment Status From TODOList

- Server initial backend deployment is complete.
- Project directory on server: `/home/workspace/Campus-Activity-Information-Platform`
- Python direct run: success
- Docker Compose run: success
- Health check endpoint: success
- Login endpoint: success
- Docker mode database: PostgreSQL
- Python direct-run mode database: SQLite
- Containers confirmed: `api`, `postgres`, `redis`

### Follow-Up Action

`docs/TODOList.md` noted that PostgreSQL and Redis were exposed externally through Docker port mappings. The next local change limits service exposure:

- API is bound to `127.0.0.1:5000` for Nginx reverse proxy access.
- PostgreSQL no longer publishes `5432` to the host.
- Redis no longer publishes `6379` to the host.

After pulling this change on the server, run:

```bash
cd /home/workspace/Campus-Activity-Information-Platform/backend
docker compose down
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:5000/api/health
```

If external access is needed, route requests through Nginx on `80/443` instead of exposing database or cache ports.

### Server GitHub SSH Key

The server has generated an SSH key for the `workspace` user and the public key has been added to GitHub with the title `campus-platform-server`.

Public key:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKdyA2pgOY1gGo8SRVR19nhLVZ5yJI00b3iIwi9luw+l workspace@campus-platform
```

After confirming GitHub accepts the key, the server repository should use the SSH remote:

```bash
cd /home/workspace/Campus-Activity-Information-Platform
git remote set-url origin git@github.com:qiuboboo/Campus-Activity-Information-Platform.git
ssh -T git@github.com
git pull --ff-only
```

Expected SSH test output:

```text
Hi qiuboboo! You've successfully authenticated, but GitHub does not provide shell access.
```

If `ssh -T git@github.com` waits forever, check outbound access from the server to GitHub port `22`. As a fallback, test GitHub's SSH-over-HTTPS endpoint:

```bash
ssh -T -p 443 git@ssh.github.com
```

If port `443` works but port `22` does not, add this to `/home/workspace/.ssh/config`:

```sshconfig
Host github.com
    HostName ssh.github.com
    User git
    Port 443
```

## 2026-05-06 (Round 2 — Server Hardening & Nginx)

### Pulled Commit

- From: `31b06e7` → To: `47fe627`
- Pulled changes: Docker port lockdown, new TODO list, DeploymentRecord.md

### Docker Port Convergence

- Applied updated `docker-compose.yml`:
  - `api` port mapping: `127.0.0.1:5000:5000` (localhost only)
  - `postgres`: removed host port mapping (internal only)
  - `redis`: removed host port mapping (internal only)
- Restarted with `docker-compose down && docker-compose up -d --build`
- All 3 containers running successfully
- Port check: only `127.0.0.1:5000` listening on host

### Nginx Reverse Proxy

- Installed nginx 1.18.0 via apt
- Deployed config from `deploy/nginx/campus-activity.conf`
- Verified: `curl http://127.0.0.1/api/health` returns `{"status":"ok"}`

### Next Steps

- Evaluate domain name and HTTPS setup
- Begin frontend-backend integration

## 2026-05-06 (Round 3 - Backend Knowledge Graph)

### Scope

- HTTPS, domain binding, OpenClaw, and vector search are intentionally deferred.
- This round focuses on backend knowledge graph features from `docs/后端技术文档.md`.

### Implemented Locally

- Added knowledge node, poster-node, and poster-link models.
- Added rule-based knowledge node generation from poster fields.
- Added rule-based poster relation generation.
- Added `GET /api/posters/{id}/related`.
- Added knowledge node query endpoints under `/api/knowledge`.
- Added keyword internal search under `/api/search/internal`.
- Updated demo seed data for related poster scenarios.
- Added `docs/APIExamples.md`.
- Local verification: `python -m compileall backend` passed.
- Runtime API verification is left for the server Docker environment because local Flask dependencies are not installed.

### Server Verification

- Pulled `289aebb` and restarted Docker (`docker-compose down && up -d --build`)
- Health check: `{"status":"ok"}`
- Login: JWT token returned
- Demo data seeded: 3 posters + 12 knowledge nodes generated
- `GET /api/posters/1/related`: Poster 1 linked to Poster 2 (same_day, same_place, same_topic), Poster 3 (same_org)
- `GET /api/knowledge/nodes`: 12 nodes returned (time, place, organization, topic, source)
- `GET /api/knowledge/nodes/1`: Node detail with 2 linked posters
- `GET /api/search/internal?q=校园`: 2 poster hits returned

### Fix Applied During Deployment

- Gunicorn multi-worker `db.create_all()` race condition caused `UniqueViolation` on PostgreSQL internal `pg_type` catalog.
- Moved database initialization from `create_app()` into gunicorn `on_starting` hook with `preload_app=True`.
- `wsgi.py` still calls `init_database()` for single-process direct-run compatibility.

## 2026-05-06 (Round 4 Planning - Data Sources and Basic Crawler)

### Local Pull

- Pulled remote server verification result into local workspace.
- Current base commit: `81f754b Server verify knowledge graph APIs and fix gunicorn db race`.
- Server-side knowledge graph verification is treated as complete.

### Next Active TODO

- Archived the completed knowledge graph TODO to `docs/todos/2026-05-06-backend-knowledge-graph.md`.
- Rotated `docs/TODOList.md` to the next executable task list.
- Next target: implement data source configuration, basic `requests + BeautifulSoup` crawling, crawl logs, and draft poster generation.
- Still deferred: HTTPS, domain binding, certificate setup, frontend pages, OpenClaw, vector search, and scheduled Celery tasks.

### Server Implementation & Verification

- Pulled `e4377e7` and implemented the data source crawler feature on the server:
  - Added `requests` and `beautifulsoup4` to `requirements.txt`
  - Added `DataSource` and `CrawlLog` models with `to_dict()` and relationships
  - Created `data_source_service.py`: CRUD, validation, crawl log management
  - Created `crawler_service.py`: HTTP fetch, HTML parsing via CSS selectors, content cleaning, draft poster creation with dedup
  - Created `data_sources.py` API blueprint with endpoints: GET/POST `/data-sources`, GET/PUT `/data-sources/{id}`, POST `/{id}/crawl`, GET `/{id}/logs`
  - Registered blueprint in `__init__.py`
- Fixed Docker build: `python:3.12-slim` image now includes `requests` and `beautifulsoup4`
- Verified all endpoints:
  - Created test data source (`https://example.com`)
  - Crawl succeeded: 1 page found, 1 succeeded, 1 draft poster created
  - Crawl log written with `completed` status
  - Health check and login continue to work
  - Existing knowledge graph APIs unaffected

## 2026-05-07 (Round 5 — Real CSE Crawler & Structured Field Extraction)

### Scope

- Extended `crawler_service.py` to extract structured fields from detail pages:
  - Title from `<h1>` (fallback to `<title>`)
  - Event time from `time[datetime]` inside `.field-date-period`
  - Location from `.field-event-location .field-item`
  - Speaker/organizer from `.field-speaker .field-item`
- Added `_parse_datetime()` to handle ISO 8601 formats (`2025-10-09T14:30:00Z`, etc.)
- Updated `_create_draft_poster()` to accept and persist `event_time`, `location`, `organizer` on the `Poster` model
- No model changes required (Poster already had these fields from a prior round)

### Real Site Experiment — `https://cse.sysu.edu.cn/`

- Created data source:
  - name: `中山大学计算机学院学术活动`
  - base_url: `https://cse.sysu.edu.cn/research/activity`
  - list_selector: `.eventitems a[href^="/event/"]`
  - content_selector: `.article-header, .field-subtitle, .field-date-period, .field-event-location, .field-speaker, .field-body`
- Crawl result: 12 events found, 12 succeeded, 0 failed
- Verified sample poster (`https://cse.sysu.edu.cn/event/3345`):
  - title: `Efficient parallel acceleration technology for distributed large models`
  - event_time: `2025-10-09T14:30:00`
  - location: `Room A327, School of Computer Science, East Campus, Sun Yat-sen University`
  - organizer/speaker: `Huang Jiayi`
- All 12 posters had correctly extracted event_time, location, and organizer
- Approved poster 17 → knowledge graph generated: 4 nodes (time, place, organization, source)
- Internal search verified:
  - `分布式大模型` → 2 poster hits
  - `分布式大模型高效并行加速技术` → 1 poster hit
  - `Huang Jiayi` → 1 poster hit + 1 knowledge node hit
  - `并行加速` → 1 poster hit

## 2026-05-07 (Round 6 Planning - Server Memory and Swap)

### Reason

- The server showed high memory usage while running the backend stack and crawler workflow.
- Before adding Celery or more crawler tasks, the next round prioritizes server stability.

### Next Active TODO

- Archived the completed crawler TODO to `docs/todos/2026-05-07-data-source-crawler.md`.
- Rotated `docs/TODOList.md` to a server memory stabilization task list.
- Next target: diagnose memory usage, create a persistent `2G` swap file, tune `vm.swappiness`, observe Docker memory usage, and optionally reduce Gunicorn memory pressure.
- Still deferred: HTTPS, domain binding, certificate setup, OpenClaw, frontend pages, and Celery feature work.

## 2026-05-07 (Round 6 — Server Swap and Memory Stabilization)

### Scope

- This round made no business feature changes. It focused on server stability: creating persistent swap, tuning memory pressure, adding Docker auto-restart, and observing post-reboot behavior.

### Swap Setup

- Created 2GiB swap file at `/swapfile`:
  - `sudo fallocate -l 2G /swapfile`
  - `sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
- Persisted in `/etc/fstab`: `/swapfile none swap sw 0 0`
- Verified fstab mount: `swapon --show` reports `/swapfile 2G`
- Set `vm.swappiness = 10` (runtime + persisted to `/etc/sysctl.d/99-campus-platform.conf`)
- Backup of original fstab saved as `/etc/fstab.bak.<timestamp>`

### Docker Compose Auto-Restart

- Added `restart: unless-stopped` to all three services (api, postgres, redis) in `backend/docker-compose.yml`
- This ensures containers restart automatically after a server reboot.

### Reboot Verification

- Server rebooted successfully.
- After reboot:
  - Swap auto-mounted: 2GiB available, 0 used ✓
  - Docker containers were recreated with `docker-compose up -d --build` (docker-compose v1.29 compatibility issue required `down -v` then `up -d`)
  - Demo data re-seeded (`flask seed-demo`)
  - All 3 containers running: api, postgres, redis

### Post-Crawl Observation

- Triggered a real crawl on `https://cse.sysu.edu.cn/research/activity` (12 events)
- Memory observed across 3 checks at 30s intervals after crawl:
  - API container: stable at ~127MiB (3.64%)
  - PostgreSQL: stable at ~51MiB (1.48%)
  - Redis: stable at ~9MiB (0.26%)
  - System available: ~1.4Gi
  - Swap usage: 0B (not needed under normal load)
- Gunicorn workers kept at 2 (not reduced — memory well within limits)
- Docker Compose memory limits not added (v1.29, current usage low)
- Health check: `{"status":"ok"}`

### Still Deferred

- HTTPS, domain, certificates, OpenClaw, frontend pages, and Celery feature work remain deferred.

## 2026-05-07 (Candidate Next Task - Celery Async Crawl Queue)

### Planning Note

- Added `docs/NextTaskPlan.md` as a candidate plan for the round after swap and memory stabilization.
- The active TODO remains `docs/TODOList.md`, which should still be completed first.
- Candidate target: convert manual data source crawling from synchronous API execution to a Celery + Redis async task queue.
- Memory guardrail: initial worker concurrency should stay at `1`.
- Deferred from the candidate plan: Celery Beat, OpenClaw, high-concurrency crawling, and scheduled crawler automation.

## 2026-05-07 (Round 7 Planning - Celery Async Crawl Queue)

### Rotation

- Archived the completed swap and memory stabilization TODO to `docs/todos/2026-05-07-server-swap-memory.md`.
- Promoted the Celery async crawl queue plan into the active `docs/TODOList.md`.
- Removed `docs/NextTaskPlan.md` because the candidate plan is now the official active TODO.

### Next Active TODO

- Target: convert manual data source crawling from synchronous API execution to a Celery + Redis async task queue.
- Guardrail: worker concurrency starts at `1`.
- Still deferred: HTTPS, domain binding, certificates, OpenClaw, frontend pages, Celery Beat, and scheduled crawler automation.

## 2026-05-07 (Round 8 — Celery Async Crawl Queue Implementation)

### Scope

- This round makes the `POST /api/data-sources/{id}/crawl` endpoint submit a Celery task by default, instead of blocking on the HTTP request.
- A `GET /api/tasks/{task_id}` endpoint is added to query async task status.
- Synchronous ("debug") mode is preserved via `{"sync": true}`.

### New Files

- **`backend/app/celery_app.py`** — Celery application initialized with `REDIS_URL` as broker and result backend.
- **`backend/app/tasks/__init__.py`** — Task package marker.
- **`backend/app/tasks/crawl_tasks.py`** — Defines `crawl_data_source_task` which calls the existing `crawl_data_source()` inside a Flask app context.
- **`backend/app/api/tasks.py`** — Implements `GET /api/tasks/{task_id}` returning `task_id`, `state`, `result`, `error`.

### Modified Files

- **`backend/app/api/data_sources.py`** — `POST /api/data-sources/{id}/crawl` now defaults to async (returns `202` + `task_id` + `status_url`); pass `{"sync": true}` for synchronous execution.
- **`backend/app/__init__.py`** — Registered the `tasks_bp` blueprint at `/api`.
- **`backend/docker-compose.yml`** — Added `worker` service using the same image, with command `celery -A app.celery_app.celery worker --loglevel=INFO --concurrency=1`, `restart: unless-stopped`, depends on `postgres` and `redis`.
- **`docs/APIExamples.md`** — Added async crawl, task status query, and sync debug mode examples.

### Verification Results

- **4 containers running:** api, worker, postgres, redis.
- **Worker logs:** connected to `redis://redis:6379/0`, task `app.tasks.crawl_tasks.crawl_data_source_task` registered.
- **Async crawl:** Returns `202` with `task_id`, task transitions through `PENDING → STARTED → SUCCESS`.
- **Completed task result:** `{success: true, pages_found: 12, pages_succeeded: 12, posters_created: 0}` (already crawled).
- **Sync crawl:** `{"sync": true}` still executes synchronously and returns `200` with full result.
- **Task status API:** Returns correct `state` and `result` for completed and running tasks.
- **Health check:** `{"status":"ok"}`.
- **Crawl logs:** Correctly written for both async and sync invocations.

### Memory Observation (3 checks at 30s intervals after async crawl)

| Container | Memory |
|-----------|--------|
| API | 151.5 MiB (stable) |
| Worker | 140.4 MiB (stable, concurrency=1) |
| PostgreSQL | 26.4 MiB |
| Redis | 8.7 MiB |
| System available | 1.1 GiB |
| Swap used | 0 B |

### Still Deferred

- HTTPS, domain binding, certificates, OpenClaw, frontend pages, Celery Beat, and scheduled crawler automation remain deferred.

## 2026-05-07 (Round 9 Planning - Activity Governance and Admin Workflow)

### Rotation

- Archived the completed Celery async crawl TODO to `docs/todos/2026-05-07-celery-async-crawl.md`.

## 2026-05-07 (Round 9 — Activity Governance and Admin Workflow)

### Scope

Extended backend with governance capabilities: review queue, bulk review, duplicate detection, quality scoring, audit logging, knowledge rebuild, and demo export APIs.

### New Fields on Existing Models

- **Poster**: added `duplicate_group_key`, `source_fingerprint`, `quality_score`, `quality_notes`, `last_crawled_at` (all nullable)
- **DataSource**: added `source_level` (official/internal/external), `owner`, `notes`, `last_success_at`, `last_failure_at`, `last_error_message`
- **CrawlLog**: added `duplicates_skipped`, `drafts_created`, `average_quality_score`
- **User**: added `audit_logs` relationship

### New Model

- **AuditLog**: tracks actor_id, action, target_type, target_id, summary, metadata_json

### New Service Files

- `backend/app/services/audit_service.py` — `create_audit_log()` with JSON metadata serialization
- `backend/app/services/dedup_service.py` — MD5-based dedup via source_key (exact URL) and fingerprint (title+date+location)
- `backend/app/services/quality_service.py` — 0–100 quality scoring with configurable rules

### Strategy

- **Duplicate detection**: tiered — exact source URL match skips creation; fingerprint match (same title+date+location) creates draft with `duplicate_group_key`
- **Quality scoring**: title completeness (−30/−15), summary (−15), event_time (−15), location (−10), source_url (−10), raw_text length (−10/−5), duplicate penalty (−20), official source bonus (+10). Score clamped to [0, 100]
- **Audit logging**: all review, bulk-review, merge, and rebuild actions logged with actor, action type, summary, and metadata

### New API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posters/review-queue` | Review queue with filters (status, source_type, duplicate_group_key) and sort by quality_score |
| POST | `/api/posters/bulk-review` | Batch approve/reject with audit logging |
| GET | `/api/posters/{id}/duplicates` | Find duplicates by `duplicate_group_key` and `source_fingerprint` |
| POST | `/api/posters/{id}/merge-source` | Merge source poster into main, record merged URLs |
| POST | `/api/posters/{id}/rebuild-knowledge` | Rebuild knowledge nodes and links for a single poster |
| POST | `/api/knowledge/rebuild` | Rebuild knowledge for all published (or filtered) posters |
| GET | `/api/audit-logs` | Paginated audit log with actor/action/target_type filters |
| GET | `/api/export/posters.json` | Export all posters (no raw_text) |
| GET | `/api/export/knowledge.json` | Export all knowledge nodes |
| GET | `/api/export/crawl-report.json` | Export recent crawl logs |
| GET | `/api/demo/summary` | Aggregated platform summary |

### Existing Enhancements

- **POST /api/data-sources**: accepts `source_level`, `owner`, `notes` in create and update
- **POST /api/data-sources/{id}/crawl**: integrates dedup detection and quality scoring; updates `last_success_at`/`last_failure_at` on data source
- **POST /api/posters/{id}/review**: writes audit log on approve/reject

### Verification Results

- **Duplicate detection**: First crawl: 12 created, 0 duplicates; Second crawl: 0 created, 12 duplicates skipped
- **Quality scoring**: All 12 crawled posters scored 100 (official source bonus + complete fields)
- **Review queue**: Returns 12 drafts with quality scores and notes, filterable by status
- **Bulk review**: 2 drafts approved in batch, audit logs written for each
- **Knowledge rebuild**: Single poster rebuilt (4 nodes, 0 links); Full rebuild (5 published posters: 5 succeeded, 0 failed)
- **Audit logs**: Correctly recorded bulk_review_approve entries with actor, summary, metadata
- **Export**: posters.json (15), knowledge.json (24), crawl-report.json (2)
- **Health check**: `{"status":"ok"}`

### Docker Memory (after crawl)

| Container | Memory |
|-----------|--------|
| API | 136.3 MiB (3.90%) |
| Worker | 79.9 MiB (2.29%) |
| PostgreSQL | 49.8 MiB (1.42%) |
| Redis | 4.4 MiB (0.12%) |
| System available | ~1.4 GiB |

### Still Deferred

- HTTPS, domain binding, certificates, OpenClaw, frontend pages, Celery Beat, and scheduled crawler automation remain deferred.
- Rotated `docs/TODOList.md` to a longer backend governance task list.

### Next Active TODO

- Target: activity governance and admin workflow.
- Scope includes review queue, batch review, duplicate detection, source merging, audit logs, quality scoring, knowledge graph rebuild, and demo/export APIs.
- Recommended split if the round is too large:
  - Review queue, batch review, and audit logs first.
  - Duplicate detection, source merging, and quality scoring second.
  - Knowledge rebuild, export APIs, and demo summary third.
- Still deferred: HTTPS, domain binding, certificates, OpenClaw, and frontend pages.

## 2026-05-07 (Round 10 — Backend Basic Version Finalization)

### Scope

Finalized the backend for stable deployment, recovery, verification, and delivery readiness. No new business features — focused on infrastructure hardening, documentation, and testing.

### Changes

- **Celery Beat scheduled crawl**: Added `beat` service to docker-compose.yml; `crawl_all_enabled_sources` task runs every 12 hours; gated by `ENABLE_SCHEDULED_CRAWL` (default `false`) and `CRAWL_SCHEDULE_HOURS` env vars
- **Backup & restore scripts**: `scripts/backup_db.sh` (`pg_dump` via Docker, auto-prunes to last 14); `scripts/restore_db.sh` (with "type yes" confirmation guard); verified with 48K backup file
- **Security hardening**: Confirmed JWT secret is non-default, `.env` not in Git, PostgreSQL/Redis ports unexposed, API on 127.0.0.1:5000 only, nginx on port 80, no hardcoded credentials
- **API documentation**: `docs/APIOverview.md` with all 11 endpoint categories, auth markers, Quick Start curl examples, design decisions, and out-of-scope note
- **Smoke test**: `scripts/smoke_backend.sh` — 12 tests covering health, login, demo summary, data sources, review queue, search, 3 export endpoints, audit logs, knowledge nodes, and auth rejection; all passing

### Verification Results

```
Smoke Test: 12 passed, 0 failed
Containers: api, worker, beat, postgres, redis — all Up
Data persistence after restart: 15 posters, 12 nodes, 6 links, 1 data source
Memory: API 139M / Worker 80M / Beat ~20M / Postgres 47M / Redis 10M
Backup: 48K, pg_dump from Docker container
```

### Still Deferred

- HTTPS, domain binding, certificates, OpenClaw, frontend pages remain deferred.

- HTTPS, domain binding, SSL certificates.
- Formal frontend pages and frontend-backend integration.
- OpenClaw or other production-grade poster vision analysis.
- Production monitoring, alerting, and high-concurrency load testing.

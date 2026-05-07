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
